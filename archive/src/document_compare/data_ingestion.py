import sys
import os
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
import fitz
from pathlib import Path


class DocumentIngestion:
    """Class for document ingestion and processing."""

    def __init__(self, base_dir: str = "data/document_compare"):
        self.log = CustomLogger().get_logger(__name__)
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def delete_existing_files(self):
        """Delete existing files in the ingestion directory."""
        try:
            if self.base_dir.exists() and self.base_dir.is_dir():
                for file in self.base_dir.iterdir():
                    if file.is_file():
                        file.unlink()
                        self.log.info("File Deleted.", path=str(file))

                self.log.info("Directory Cleaned", directory=str(self.base_dir))
        except Exception as e:
            self.log.error(f"Error deleting existing files: {e}")
            raise DocumentPortalException("An error occurred while deleting existing files.", sys)

    def save_uploaded_file(self, refrence_file, actual_file):
        """Save the uploaded file to the ingestion directory."""
        try:
            self.delete_existing_files()
            self.log.info("Existing Files deleted successfully.")

            ref_path = self.base_dir / refrence_file.name
            act_path = self.base_dir / actual_file.name

            if not refrence_file.name.endswith(".pdf") or not actual_file.name.endswith(".pdf"):
                raise ValueError("Only PDF files are allowed.")
            
            with open(ref_path, 'wb') as f:
                f.write(refrence_file.get_buffer())

            with open(act_path, 'wb') as f:
                f.write(actual_file.get_buffer())
            
            self.log.info("Files Saved", refrence=str(ref_path), actual_file=str(act_path))
            return ref_path, act_path
        
        except Exception as e:
            self.log.error(f"Error saving uploaded files: {e}")
            raise DocumentPortalException("An error occurred while saving uploaded files.", sys)

    def read_pdf(self, pdf_path: Path) -> str:
        """Read and extract text from a PDF file."""
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise ValueError(f"PDF is encrypted: {pdf_path.name}")
                
                all_text = []

                print("doc.page_count:::",doc.page_count)
                for page_num in range(doc.page_count):
                    page = doc.load_page(page_num)
                    text = page.get_text()

                    if text.strip():
                        all_text.append(f"\n---- Page {page_num} ---\n{text}")

                self.log.info("PDF read successfully", file=str(pdf_path), pages=len(all_text))
                return '\n'.join(all_text)
        except Exception as e:
            self.log.error(f"Error reading PDF: {e}")
            raise DocumentPortalException("An Error occured while reading the pdf.", sys)
        

    def combined_documents(self):
        """Combine multiple documents into a single text."""
        try:
            content_dict = {}
            doc_parts = []

            for filename in sorted(self.base_dir.iterdir()):
                if filename.is_file() and filename.suffix == ".pdf":
                    content_dict[filename.name] = self.read_pdf(filename)

            for filename, content in content_dict.items():
                doc_parts.append(f"Document: {filename}\n{content}")
            
            combined_text = '\n'.join(doc_parts)
            self.log.info("Document COmbined", count=len(doc_parts))
            return combined_text
        except Exception as e:
            self.log.error(f"Error Combining documents: {e}")
            raise DocumentPortalException("An error occured while  combining document.", sys)

