from fastapi import FastAPI, UploadFile, File, HTTPException, Form, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import List, Optional, Any, Dict

from src.document_ingestion.data_ingestion import (
    FaissManager,
    ChatIngestor,
    DocHandler,
    DocumentComparator
)

from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_compare.document_comparator import DocumentComparaorLLM
from src.document_chat.retrieval import ConversationalRAG
from pathlib import Path

from utils.document_ops import FastAPIFileAdaptor, read_pdf_via_handler


BASE_DIR = Path(__file__).resolve().parent.parent  # project root
FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")
UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")

app = FastAPI(title="Document Portal API", version="1.0.0")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    resp = templates.TemplateResponse("index.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "service": "Document Portal API"}







@app.post("/analyze-document")
async def analyze_document(file:UploadFile=File(...)) -> Any:
    try:
        print("file received from analyse documnet:")
        dh = DocHandler()
        print("DocHandler initialized", type(file))
        saved_path = dh.save_pdf(FastAPIFileAdaptor(file))
        text = read_pdf_via_handler(dh, saved_path)
        analyzer = DocumentAnalyzer()
        response = analyzer.analyze_document(text)
        return JSONResponse(content={"analysis": response})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")



@app.post("/document-compare")
async def compare_documents(
    reference: UploadFile = File(...),
    actual: UploadFile = File(...)
) -> Any:
    try:
        print("Files received for comparison.")
        dc = DocumentComparator()
        print("DocumentComparator initialized.")
        ref_path, act_path = dc.save_uploaded_files(
            FastAPIFileAdaptor(reference), 
            FastAPIFileAdaptor(actual)
            )

        combined_text = dc.combined_documents()
        comparator = DocumentComparaorLLM()
        comparison_df = comparator.compare_documents(combined_docs=combined_text)
        return {"rows": comparison_df.to_dict(orient="records"), "session_id": dc.session_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document comparison failed: {str(e)}")


@app.post("/chat/index")
async def chat_build_index(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    use_session_dir: bool = Form(True),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    k: int = Form(5)
) -> Any:
    try:
        wrapped = [FastAPIFileAdaptor(f) for f in files]
        chat_ingestor = ChatIngestor(
            temp_base=UPLOAD_BASE,
            faiss_base=FAISS_BASE,
            session_id=session_id or None,
            use_session_dir=use_session_dir
        )

        chat_ingestor.built_retriever(wrapped, chunk_size=chunk_size, chunk_overlap=chunk_overlap, k=k)

        return {"session_id": chat_ingestor.session_id, "k": k, "use_session_dir": use_session_dir}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"index build failed: {str(e)}")


@app.post("/chat/query")
async def chat_query(
    question: str = Form(...),
    session_id: Optional[str] = Form(None),
    use_session_dir: bool = Form(True),
    k: int = Form(5)
) -> Any:
    try:
        
        if use_session_dir and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dir is True.")
        
        index_dir = os.path.join(FAISS_BASE, session_id) if use_session_dir else FAISS_BASE

        if not os.path.exists(index_dir):
            raise HTTPException(status_code=404, detail=f"FAISS index not found at {index_dir}")
        
        # Initialize LCEL-style RAG pipeline
        rag = ConversationalRAG(session_id=session_id)

        print(f"Loading FAISS retriever from {index_dir} with k={k}")
        rag.load_retriever_from_faiss(index_path=index_dir, k=k, index_name=FAISS_INDEX_NAME)

        # Optional: For now we pass empty chat history
        response = rag.invoke(question, chat_history=[])

        return {
            "answer": response,
            "session_id": session_id,
            "k": k,
            "engine": "LCEL-RAG"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"chat query failed: {str(e)}")





# command for executing the fast api
# uvicorn api.main:app --reload    
#uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload