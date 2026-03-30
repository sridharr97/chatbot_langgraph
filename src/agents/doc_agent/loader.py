import os
import docx
import logging

logger = logging.getLogger(__name__)

def load_docx(file_path: str) -> str:
    """
    Loads text from an MS Word document.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return ""
    
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    except Exception as e:
        logger.error(f"Error loading docx {file_path}: {e}")
        return ""
