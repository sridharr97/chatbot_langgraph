import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage, SystemMessage
from src.agents.doc_agent.loader import load_docx

logger = logging.getLogger(__name__)

class DocAgentState(BaseModel):
    query: str
    selected_doc: Optional[str] = None
    answer: Optional[str] = None
    error: Optional[str] = None
    status: str = "success"
    metadata: Dict[str, Any] = {}

class DocAgent:
    def __init__(self, llm):
        self.llm = llm
        self.resources_dir = "src/resources"
        self.schema_path = os.path.join(self.resources_dir, "docs_schema.json")

    def _get_docs_schema(self) -> List[Dict[str, str]]:
        try:
            with open(self.schema_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading docs_schema: {e}")
            return []

    def select_document(self, query: str) -> str:
        """
        Step 1: Document Selection
        """
        schema = self._get_docs_schema()
        schema_str = json.dumps(schema, indent=2)
        
        system_prompt = (
            "You are a document selector. Based on the following document descriptions, "
            "select the most relevant document name for the user's query.\n\n"
            f"Available Documents:\n{schema_str}\n\n"
            "Return ONLY the document name. No other text."
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}")
        ]
        
        response = self.llm.invoke(messages)
        selected_name = response.content.strip()
        
        # Simple validation: ensure selected_name matches one of the names in the schema
        valid_names = [d["name"] for d in schema]
        if selected_name not in valid_names:
            # Fallback to the first document name if LLM fails to provide a valid name
            selected_name = valid_names[0] if valid_names else "doc"
            
        return selected_name

    def generate_answer(self, query: str, doc_name: str) -> str:
        """
        Step 2: Answer Generation
        """
        file_path = os.path.join(self.resources_dir, f"{doc_name}.docx")
        doc_content = load_docx(file_path)
        
        if not doc_content:
            return "Error: Could not load the document content."

        system_prompt = (
            "You are an assistant that answers questions based ONLY on the provided document content.\n\n"
            "Rules:\n"
            "1. Answer ONLY using the provided document.\n"
            "2. If the answer is not found in the document, respond with: 'Not found in document'.\n"
            "3. Do not use external knowledge.\n\n"
            f"Document Content ({doc_name}):\n{doc_content}"
        )
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content.strip()

    def run(self, query: str) -> Dict[str, Any]:
        """
        Orchestrates the two-step Doc QA process.
        """
        try:
            logger.info(f"--- DOC AGENT: Processing query: '{query}' ---")
            
            # Step 1: Selection
            doc_name = self.select_document(query)
            logger.info(f"--- DOC AGENT: Selected '{doc_name}' ---")
            
            # Step 2: Generation
            answer = self.generate_answer(query, doc_name)
            
            return {
                "answer": answer,
                "data": [],
                "sql": None,
                "error": None,
                "status": "success",
                "metadata": {
                    "source": doc_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error in DocAgent: {e}")
            return {
                "answer": f"Sorry, an error occurred: {str(e)}",
                "data": [],
                "sql": None,
                "error": str(e),
                "status": "error",
                "metadata": {
                    "source": None
                }
            }
