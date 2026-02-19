import os
import sys
import fitz
import uuid
from datetime import datetime
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException


class DataHandler:
    """A class to handle data ingestion and preprocessing for document analysis.
    Automatically logs all actions and supports session-based organization.
    """

    def __init__(self, data_dir=None, session_id=None):
        try:
            self.log = CustomLogger().get_logger(__name__)
            self.data_dir = data_dir or os.getenv(
                "DATA_STORAGE_PATH", 
                os.path.join(os.getcwd(), "data", "document_analysis")
                )
            
            self.session_id = session_id or f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

            # Create session directory if it doesn't exist
            self.session_path = os.path.join(self.data_dir, self.session_id)
            os.makedirs(self.session_path, exist_ok=True)

            self.log.info("DataHandler initialized successfully.", data_dir=self.data_dir, session_id=self.session_id, session_path=self.session_path)
            
        except Exception as e:
            self.log.error(f"Error initializing DataHandler:", error=str(e))
            raise DocumentPortalException("failed to initialize DataHandler", sys)

    def save_pdf(self, uploaded_file):
        """Save uploaded PDF file to the session directory."""
        try:
            filename = os.path.basename(uploaded_file.name)

            if not filename.lower().endswith(".pdf"):
                self.log.error(f"Uploaded file is not a PDF:", filename=filename)
                raise DocumentPortalException("Uploaded file is not a PDF", sys)
            
            save_path = os.path.join(self.session_path, filename)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.read())

            self.log.info("PDF file saved successfully.", filename=filename, save_path=save_path)

            return save_path
        
        except Exception as e:
            self.log.error(f"Error saving PDF file:", error=str(e))
            raise DocumentPortalException("failed to save PDF file", sys)

    def read_pdf(self, pdf_path)-> str:
        """Read and extract text from a PDF file."""
        try:
            text_chunks = []

            with fitz.open(pdf_path) as doc:
                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    text_chunks.append(f"\n---Page {page_num + 1}---\n{page.get_text()}")
            
            text = "\n".join(text_chunks)

            self.log.info("PDF file read successfully.", pdf_path=pdf_path, total_pages=len(text_chunks))

            return text
        except Exception as e:
            self.log.error(f"Error reading PDF file:", error=str(e))
            raise DocumentPortalException("failed to read PDF file", sys)


if __name__ == "__main__":
    data_handler = DataHandler()
    print("DataHandler initialized successfully.", data_handler.session_path)
    print("---------------------------------------------------")
    sample_pdf_path = r"C:\Users\ved.sharma\Desktop\LLM-Ops-18-DEC-2025\document_portal\data\sample.pdf"
    save_path = data_handler.save_pdf(open(sample_pdf_path, "rb"))

    content = data_handler.read_pdf(save_path)
    print("PDF content extracted successfully.", content[:500])  # Print first 500 characters
