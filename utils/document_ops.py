from __future__ import annotations
import os
import sys
import json
import uuid
import hashlib
import shutil
from datetime import datetime, timezone

import fitz  # PyMuPDF

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

from utils.model_loader import ModelLoader

from typing import Iterable, List, Optional, Dict, Any
from pathlib import Path
from logger.custom_logger import CustomLogger
from exception.custom_exception import DocumentPortalException
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from fastapi import FastAPI, UploadFile




log = CustomLogger().get_logger(__name__)
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class FastAPIFileAdaptor:
    def __init__(self, upload_file: UploadFile):
        self._upload_file = upload_file
        self.name = upload_file.filename

    def getbuffer(self) -> bytes:
        return self._upload_file.file.read()


def read_pdf_via_handler(handler, path:str) -> str:
    if hasattr(handler, "read_pdf"):
        return handler.read_pdf(path)
    if hasattr(handler, "read_"):
        return handler.read_(path)
    
    raise RuntimeError("No valid read method found in DocHandler")


def load_documents(paths:Iterable[Path]) -> List[Document]:
    """Load documents using appropriate loaders based on file extensions."""

    docs: List[Document] = []
    try:
        for file_path in paths:
            ext = file_path.suffix.lower()

            if ext == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif ext == ".docx":
                loader = Docx2txtLoader(str(file_path))
            elif ext == ".txt":
                loader = TextLoader(str(file_path), encoding='utf-8')
            else:
                log.warning("Unsupported file type encountered.", filename=str(file_path))
                continue  # Unsupported file type

            docs.extend(loader.load())
        log.info("Loaded document.", filename=str(file_path), count=len(docs))

        return docs
    except Exception as e:
        log.error("Error loading documents.", error=str(e))
        raise DocumentPortalException("Failed to load documents", str(e)) from e


def concat_for_analysis(documents: List[Document]) -> str:
    """Concat all document texts into a single string for analysis."""
    try:
        parts = []

        for doc in documents:
            src = doc.metadata.get("source") or doc.metadata.get("filename") or "unknown"
            parts.append(f"\n----SOURCE: {src} ---\n {doc.page_content}")

        return "\n".join(parts)

    except Exception as e:
        log.error("Error concatenating documents for analysis.", error=str(e))
        raise DocumentPortalException("Failed to concatenate documents", str(e)) from e
    
def concat_for_comparison(ref_documents: List[Document], act_documents: List[Document]) -> str:
    """Concat all document texts into a single string for comparison."""
    try:
        left = concat_for_analysis(ref_documents)
        right = concat_for_analysis(act_documents)

        return f"<<Reference Documents>>\n{left}\n\n\n<<Actual Documents>>\n{right}"
    
    except Exception as e:
        log.error("Error concatenating documents for comparison.", error=str(e))
        raise DocumentPortalException("Failed to concatenate documents for comparison", str(e)) from e