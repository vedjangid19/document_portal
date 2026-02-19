import os
from pathlib import Path
from src.document_analyzer.data_ingestion import DataHandler
from src.document_analyzer.data_analysis import DocumentAnalyzer


# def main():
#     try:
#         data_handler = DataHandler(session_id="test_session_001")

#         sample_file_path = r"C:\Users\ved.sharma\Desktop\LLM-Ops-18-DEC-2025\document_portal\data\sample2.pdf"

#         save_pdf_path = data_handler.save_pdf(
#             open(sample_file_path, "rb")
#         )

#         sample_text = data_handler.read_pdf(save_pdf_path)

#         documnet_analyzer = DocumentAnalyzer()

#         response = documnet_analyzer.analyze_document(sample_text)

#         print("Document analysis response:", response)


#     except Exception as e:
#         print(f"Error in main:", str(e))


# if __name__ == "__main__":
#     main()


# # Testing code for document compare functionality
# import io
# from pathlib import Path
# from src.document_compare.data_ingestion import DocumentIngestion
# from src.document_compare.document_comparator import DocumentComparaorLLM

# def test_compare_documents():
#     ref_path = Path("C:\\Users\\ved.sharma\\Desktop\\LLM-Ops-18-DEC-2025\\document_portal\\data\\Long_Report_V1.pdf")
#     act_path = Path("C:\\Users\\ved.sharma\\Desktop\\LLM-Ops-18-DEC-2025\\document_portal\\data\\Long_Report_V2.pdf")

#     comparator = DocumentIngestion()
#     # ref_upload = open(ref_path, 'rb').read()
#     # act_upload = open(act_path, 'rb').read()

#     class FakeUpload:
#         def __init__(self, file_path: Path):
#             self.name = file_path.name
#             self._buffer = file_path.read_bytes()
        
#         def get_buffer(self):
#             return self._buffer
    
#     ref_upload = FakeUpload(ref_path)
#     act_upload = FakeUpload(act_path)


#     ref_file, act_file = comparator.save_uploaded_file(refrence_file=ref_upload, actual_file=act_upload)

#     combined_text = comparator.combined_documents()

#     llm_comparator = DocumentComparaorLLM()
#     comparison_df = llm_comparator.compare_documents(combined_docs=combined_text)

#     print("\n=== COMPARISON RESULT ===")
#     print(comparison_df.head())

# if __name__ == "__main__":
#     test_compare_documents()



# # Testing code for document chat functionality
# import sys
# from utils.model_loader import ModelLoader
# from pathlib import Path
# from langchain_community.vectorstores import FAISS
# from src.single_document_chat.data_ingestion import SingleDocIngestor
# from src.single_document_chat.retrieval import ConversationalRAG


# FAISS_INDEX_PATH = Path("faiss_index")
# def test_conversational_rag_on_pdf(pdf_path:str, question:str):
#     try:
#         model_loader = ModelLoader()

#         if FAISS_INDEX_PATH.exists():
#             print("Loading exiting FAISS index...")
#             embeddings = model_loader.load_embeddings()
#             vectorstore = FAISS.load_local(folder_path=str(FAISS_INDEX_PATH), embeddings=embeddings, allow_dangerous_deserialization=True)

#             retriever = vectorstore.as_retriever(
#                 search_type="similarity", search_kwargs={"k": 5}
#             )
#         else:
#             # step 2 ingest document and create retriever
#             print("FAISS index not found. Ingesting PDF and creating index...")

#             with open(pdf_path, "rb") as f:
#                 uploaded_files = [f]
#                 ingestor = SingleDocIngestor()
#                 retriever = ingestor.ingest_files(uploaded_files)

#         print("Running Conversational RAG...")
#         session_id = "test_conversational_rag"
#         rag = ConversationalRAG(retriever=retriever, session_id=session_id)
#         response = rag.invoke(question)
#         print(f"\n Question: {question}\nAnswer: {response}")

#     except Exception as e:
#         print("Test failed.", str(e))
#         sys.exit(1)


# if __name__ == "__main__":
#     # Example PDF path and question
#     pdf_path = "data\\single_document_chat\\NIPS-2017-attention-is-all-you-need-Paper.pdf"
#     question = "What is the significance of the attention mechanism? can you explain it in simple terms?"

#     if not Path(pdf_path).exists():
#         print(f"PDF file does not exist at: {pdf_path}")
#         sys.exit(1)
    
#     # Run the test
#     test_conversational_rag_on_pdf(pdf_path, question)




# Testing code for multi document chat functionality

import sys
from pathlib import Path
from src.multi_document_chat.data_ingestion import DocumentIngestor
from src.multi_document_chat.retrieval import ConversationalRAG


def test_document_ingestion_and_rag():
    try:
        test_files = [
            "data\\multi_doc_chat\\market_analysis_report.docx",
            "data\\multi_doc_chat\\NIPS-2017-attention-is-all-you-need-Paper.pdf",
            "data\\multi_doc_chat\\sample.pdf",
            "data\\multi_doc_chat\\state_of_the_union.txt"
        ]
        uploaded_files = []

        for file_path in test_files:
            if Path(file_path).exists():
                uploaded_files.append(open(file_path, "rb"))
            else:
                print(f"file does not exist: {file_path}")

        if not uploaded_files:
            print("No valid files to upload.")
            sys.exit(1)
        
        ingestor = DocumentIngestor()
        retriever = ingestor.ingest_files(uploaded_files)

        for f in uploaded_files:
            f.close()

        session_id = "test_multi_doc_chat"

        rag = ConversationalRAG(session_id=session_id, retriever=retriever)

        question = "what is President Zelenskyy said in their speech in parliament?"
        answer=rag.invoke(question)
        print("\n Question:", question)
        print("Answer:", answer)
        if not uploaded_files:
            print("No valid files to upload.")
            sys.exit(1)

    except Exception as e:
        print(f"test failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_document_ingestion_and_rag()