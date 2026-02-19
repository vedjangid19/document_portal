from __future__ import annotations
import uuid
import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Dict, Any
from utils.model_loader import ModelLoader
from exception.custom_exception_archive import DocumentPortalException
from logger.custom_logger import CustomLogger


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}
log = CustomLogger().get_logger(__name__)

def _session_id(prefix: str = "session") -> str:
    """Generate a unique session ID with the given prefix."""
    return f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"



def save_uploaded_file(uploaded_files: Iterable, target_dir: Path) -> list[Path]:
    """Save uploaded files (Streamlit-like) and return local paths."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        saved_paths: list[Path] = []

        for uploaded_file in uploaded_files:
            name = getattr(uploaded_file, "name", "file")
            ext = Path(name).suffix.lower()

            if ext not in SUPPORTED_EXTENSIONS:
                log.warning("Unsupported File skipped.", filename=str(uploaded_file))
                continue

            unique_filename = f"{uuid.uuid4().hex[:8]}{ext}"
            output_path = target_dir / unique_filename

            with open(output_path, "wb") as f:
                if hasattr(uploaded_file, "read"):
                    f.write(uploaded_file.read())
                else:
                    f.write(uploaded_file.getbuffer())
            
            saved_paths.append(output_path)
            log.info("File saved.", original_filename=name, saved_as=str(output_path))
        return saved_paths

    except Exception as e:
        log.error("Failed to save uploaded file", error=str(e))
        raise DocumentPortalException("Failed to save uploaded file.", e) from e

