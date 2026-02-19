from __future__ import annotations
from typing import List, Optional, Dict, Any, Iterable
from pathlib import Path
import os
import uuid
import sys
import json
import hashlib
import fitz  # PyMuPDF
import shutil
from datetime import datetime, timezone
from langchain_core.documents import Document
from utils.model_loader import ModelLoader
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from utils.model_loader import ModelLoader
from utils.file_io import _session_id, save_uploaded_file
from utils.document_ops import load_documents, concat_for_analysis, concat_for_comparison
from langchain_community.vectorstores import FAISS  # type: ignore
from langchain_text_splitters import RecursiveCharacterTextSplitter


class FaissManager:
    """A class to manage FAISS vector store operations including creation, loading, and saving.
    Automatically logs all actions and handles exceptions."""
    def __init__(self, index_dir: Path, model_loader: Optional[ModelLoader] = None):
        self.log = CustomLogger().get_logger(__name__)

        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.meta_path = self.index_dir / "ingested_metadata.json"
        self._meta_data: Dict[str, Any] = {"rows": {}}

        if self.meta_path.exists():
            try:
                self._meta_data = json.loads(self.meta_path.read_text(encoding="utf-8")) or {"rows": {}}
                self.log.info("Existing metadata loaded.", index_dir=str(self.index_dir), meta_path=str(self.meta_path))

            except Exception as e:
                self.log.error("Failed to load existing metadata.", error=str(e))
                raise DocumentPortalException("Failed to load existing metadata", sys)

        self.model_loader = model_loader or ModelLoader()
        self.embedding_model = self.model_loader.load_embeddings()
        self.vector_store: Optional[FAISS] = None

        self.log.info("FaissManager initialized.", index_dir=str(self.index_dir))

    def _exist(self):
        """Check if FAISS index files exist in the index directory."""
        return (self.index_dir / "index.faiss").exists() and (self.index_dir / "index.pkl").exists()

    @staticmethod
    def _fingerprint(text: str, md: Dict[str, Any]) -> str:
        """Generate a unique fingerprint for the document based on its content and metadata."""
        source = md.get("source") or md.get("file_path") or "unknown_source"
        row_id = md.get("row_id")

        if source is not None:
            return f"{source}:: {'' if row_id is None else row_id}"
        
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _save_meta(self):
        """Save the current metadata to the meta_path as a JSON file."""
        self.meta_path.write_text(json.dumps(self._meta_data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_documents(self, docs: List[Document]):
        """ Add documents to the FAISS index, avoiding duplicates based on fingerprints."""
        if self.vector_store is None:
            raise RuntimeError("Vector store not initialized. Call load_or_create_index() first, before add_documents_idempotent().",)

        new_docs: List[Document] = []

        for doc in docs:

            key = self._fingerprint(doc.page_content, doc.metadata or {})

            if key in self._meta_data["rows"]:
                self.log.info("Document already exists in index. Skipping.", fingerprint=key)
                continue

            self._meta_data["rows"][key] = True
            new_docs.append(doc)

        if new_docs:
            self.vector_store.add_documents(new_docs)
            self.vector_store.save_local(str(self.index_dir))
            self._save_meta()
            self.log.info("New documents added to FAISS index.", count=len(new_docs))
        
        return len(new_docs)


    def load_or_create_index(self, texts: Optional[List[str]] =None, metadatas: Optional[List[Dict]] = None):
        """"""
        if self._exist():
            self.vector_store = FAISS.load_local(
                str(self.index_dir), 
                embeddings=self.embedding_model,
                allow_dangerous_deserialization=True)
            self.log.info("FAISS index loaded from disk.", index_dir=str(self.index_dir))

            return self.vector_store
        
        if not texts:
            raise DocumentPortalException("No texts or metadatas provided for creating new FAISS index", sys)

        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embedding_model,
            metadatas=metadatas or [])
        self.vector_store.save_local(str(self.index_dir))

        self.log.info("New FAISS index created and saved to disk.", index_dir=str(self.index_dir))

        return self.vector_store
    

class DocHandler:
    """A class to handle document operations such as saving and reading PDF files."""
    def __init__(self, data_dir: Optional[str] = None, session_id: Optional[str] = None):
        
        self.log = CustomLogger().get_logger(__name__)
        self.log.info("DocHandler initialization started...")
        

        self.session_id = session_id or _session_id()
        
        self.data_dir = data_dir or  os.getenv("DATA_STORAGE_PATH", os.path.join(os.getcwd(), "data", "document_analysis"))

        self.session_path = Path(self.data_dir) / self.session_id

        self.session_path.mkdir(parents=True, exist_ok=True)

        self.log.info("DocHandler initialized.", data_dir=str(self.data_dir), session_id=self.session_id, session_path=str(self.session_path))

    def save_pdf(self, uploaded_file) -> str:
        try:

            filename = os.path.basename(uploaded_file.name)

            if not filename.lower().endswith(".pdf"):
                raise ValueError("Invalid file type. Only PDF files are supported.")
            
            save_path = self.session_path / filename

            with open(save_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())

            self.log.info("PDF file saved.", original_filename=filename, saved_as=str(save_path))
            return str(save_path)
            
        except Exception as e:
            self.log.error("Failed to save PDF file.", error=str(e))
            raise DocumentPortalException("Failed to save PDF file", e) from e

    def read_pdf(self, pdf_path: str) -> str:
        
        try:
            text_chunks: List[str] = []
            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()
                    text_chunks.append(f"\n--- Page {page_num + 1} ---\n{text}")
                
            full_text = "\n".join(text_chunks)
            self.log.info("PDF file read successfully.", pdf_path=pdf_path, total_pages=len(text_chunks))

            return full_text
        
        except Exception as e:
            self.log.error("Failed to read PDF file.", error=str(e))
            raise DocumentPortalException("Failed to read PDF file", e) from e


class DocumentComparator:
    """A class to handle document comparison operations."""
    def __init__(self, base_dir: str = "data/document_compare", session_id: Optional[str] = None):
        self.log = CustomLogger().get_logger(__name__)

        self.base_dir = Path(base_dir)
        self.session_id = session_id or _session_id()
        self.session_path = self.base_dir / self.session_id
        self.session_path.mkdir(parents=True, exist_ok=True)

        self.log.info("DocumentComparator initialized.", base_dir=str(self.base_dir), session_id=self.session_id, session_path=str(self.session_path))

    def save_uploaded_files(self, reference_file, actual_file):
        try:
            actual_file_path = self.session_path / actual_file.name
            reference_file_path = self.session_path / reference_file.name

            for file_obj, save_path in [(reference_file, reference_file_path), (actual_file, actual_file_path)]:

                if not file_obj.name.lower().endswith(".pdf"):
                    raise ValueError("Invalid file type. Only PDF files are supported.")
                
                with open(save_path,"wb") as f:
                    if hasattr(file_obj, "read"):
                        f.write(file_obj.read())
                    else:
                        f.write(file_obj.getbuffer())
                
                self.log.info("Uploaded file saved for comparison.", original_filename=file_obj.name, saved_as=str(save_path))

            return actual_file, reference_file
        except Exception as e:
            self.log.error("Failed to save uploaded files for comparison.", error=str(e))
            raise DocumentPortalException("Failed to save uploaded files for comparison", e) from e

    def read_pdf(self, pdf_path: str) -> str:
        """Read a PDF file and return its text content."""
        try:
            total_pages = 0
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError("Cannot read encrypted PDF files.")
                
                text_chunks: List[str] = []

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    if text.strip():
                        text_chunks.append(f"\n--- Page {page_num + 1} ---\n{text}")
                
                page_count = len(text_chunks)
                full_text = "\n".join(text_chunks)
            self.log.info("PDF file read successfully for comparison.", pdf_path=pdf_path, total_pages=page_count)

            return full_text
        
        except Exception as e:
            self.log.error("Failed to read PDF file.", error=str(e))
            raise DocumentPortalException("Failed to read PDF file", e) from e
    def combined_documents(self) -> str:
        """Combine texts from the reference and actual PDF files."""
        try:
            doc_parts = []
            for file in self.session_path.iterdir():
                if file.suffix.lower() == ".pdf":
                    text = self.read_pdf(str(file))
                    doc_parts.append(f"\n--- Document: {file.name} ---\n{text}")
            
            combined_text = "\n".join(doc_parts)
            self.log.info("Documents combined for comparison.", session_id=self.session_id, total_documents=len(doc_parts))

            return combined_text
        except Exception as e:
            self.log.error("Failed to combine documents.", error=str(e))
            raise DocumentPortalException("Failed to combine documents", e) from e

    def clean_old_sessions(self, keep_latest: int = 5):
        try:
            sessions = sorted([f for f in self.base_dir.iterdir() if f.is_dir()], reverse=True)

            for old_session in sessions[keep_latest:]:
                shutil.rmtree(old_session, ignore_errors=True)
                self.log.info("Old session directory removed.", session_path=str(old_session))
            
            self.log.info("Old sessions cleanup completed.", total_removed=len(sessions) - keep_latest)
            
        except Exception as e:
            self.log.error("Failed to clean old sessions.", error=str(e))
            raise DocumentPortalException("Failed to clean old sessions", e) from e
        


class ChatIngestor:
    def __init__(self, temp_base: str = "data", faiss_base: str = "faiss_index", session_id: Optional[str] = None, use_session_dir: bool = True):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.model_loader = ModelLoader()

            self.temp_base = Path(temp_base)
            self.faiss_base = Path(faiss_base)
            self.session_id = session_id or _session_id()
            self.use_session_dir = use_session_dir

            self.temp_base.mkdir(parents=True, exist_ok=True)
            self.faiss_base.mkdir(parents=True, exist_ok=True)

            self.temp_dir = self._resolve_dir(self.temp_base)
            self.faiss_dir = self._resolve_dir(self.faiss_base)

            self.log.info(
                "ChatIngestor initialized.",
                session_id=self.session_id, 
                use_session_dir=self.use_session_dir, 
                temp_dir=str(self.temp_dir), 
                faiss_dir=str(self.faiss_dir)
                )

        except Exception as e:
            self.log.error("Failed to initialize ChatIngestor.", error=str(e))
            raise DocumentPortalException("Initialization error in ChatIngestor", e) from e

    def _resolve_dir(self, base_dir: Path) -> Path:
        if self.use_session_dir:
            session_dir = base_dir / self.session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            return session_dir
        
        return base_dir

    def _split(self, docs: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
        try:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            chunks = splitter.split_documents(docs)

            self.log.info("Documents split into chunks.", original_count=len(docs), chunk_count=len(chunks))

            return chunks
        except Exception as e:
            self.log.error("Failed to split documents into chunks.", error=str(e))
            raise DocumentPortalException("Failed to split documents", e) from e

    def built_retriever(self, uploaded_files: Iterable,
        *,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        k: int = 5,):
        
        try:
            paths = save_uploaded_file(uploaded_files=uploaded_files, target_dir=self.temp_dir)

            docs = load_documents(paths=paths)

            if not docs:
                raise ValueError("No valid documents loaded for ingestion.")
            
            chunks = self._split(docs=docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            faiss_manager = FaissManager(index_dir=self.faiss_dir, model_loader=self.model_loader)

            texts = [doc.page_content for doc in chunks]
            metadatas = [doc.metadata or {} for doc in chunks]

            try:
                vector_store = faiss_manager.load_or_create_index(texts=texts, metadatas=metadatas)
            except Exception as e:
                self.log.error("Failed to load or create FAISS index.", error=str(e))
                vector_store = faiss_manager.load_or_create_index(texts=texts, metadatas=metadatas)

            added = faiss_manager.add_documents(chunks)
            self.log.info("Retriever built successfully.", total_chunks=len(chunks), new_chunks_added=added, session_id=self.session_id)

            return vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k}
            )

        except Exception as e:
            self.log.error("Failed to ingest files.", error=str(e))
            raise DocumentPortalException("Failed to ingest files", e) from e
