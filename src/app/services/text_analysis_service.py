import os
import json
import logging
from typing import Dict, Any, List
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from app.services.model_manager import model_manager
import math
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class TextAnalysisServiceError(Exception):
    """Custom exception for text analysis service errors"""
    pass

class TextAnalysisService:
    def __init__(self):
        self.llm = model_manager.llm
        self.embeddings = model_manager.embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200
        )
        
        # Restored comprehensive summary prompt
        self.summary_prompt = PromptTemplate(
            input_variables=["text"],
            template="""Summarize the following document content in a clear and comprehensive manner:

{text}

Provide a summary that includes:
1. Main topic or purpose of the document
2. Key points and important information
3. Important dates, names, or numbers

Summary:"""
        )
        
        self.unified_prompt = PromptTemplate(
            input_variables=["text", "document_type"],
            template="""Analyze this {document_type} document and provide a comprehensive JSON response with:
1. Summary (detailed summary with key points and important details)
2. Key structured data (dates, amounts, names, entities, etc.)
3. Action items (if any)

Text: {text}

Respond in this JSON format only:
{{
  "summary": {{
    "summary": "comprehensive summary with key details",
    "original_length": "length of original text",
    "summary_length": "length of summary"
  }},
  "structured_data": {{"key": "value"}},
  "action_items": ["action1", "action2"]
}}"""
        )
        
        self.action_items_prompt = PromptTemplate(
            input_variables=["text"],
            template="""Analyze this document and generate actionable items:

{text}

Generate a list of action items in JSON format:
{{
  "action_items": [
    {{
      "action": "description of the action",
      "priority": "high/medium/low",
      "assignee": "who should do this (if mentioned)",
      "due_date": "when this should be done (if mentioned)",
      "category": "work/personal/financial/etc"
    }}
  ],
  "summary": "brief summary of what needs to be done"
}}

JSON:"""
        )

    def chunk_text(self, text: str, chunk_size: int = 1500, chunk_overlap: int = 200) -> list:
        """Split text into overlapping chunks for summarization"""
        splits = self.text_splitter.split_text(text)
        return splits

    def summarize_document(self, text_content: str) -> Dict[str, Any]:
        """Recursively summarize a long document for best context coverage"""
        # If short, use direct summary
        if len(text_content) <= 3000:
            return self.summarize_content(text_content)
        # Otherwise, chunk and summarize recursively
        chunks = self.chunk_text(text_content)
        chunk_summaries = []
        for chunk in chunks:
            summary = self.summarize_content(chunk)
            chunk_summaries.append(summary["summary"] if isinstance(summary, dict) else summary)
        # Aggregate summaries
        combined = "\n".join(chunk_summaries)
        # If still too long, summarize again recursively
        if len(combined) > 3000:
            return self.summarize_document(combined)
        return {
            "summary": combined,
            "original_length": len(text_content),
            "summary_length": len(combined),
            "recursive": True,
            "chunks": len(chunks)
        }

    def summarize_content(self, text_content: str) -> Dict[str, Any]:
        """Generate a comprehensive summary of the content"""
        try:
            prompt = self.summary_prompt.format(text=text_content[:3000])  # Increased for better context
            result = self.llm.invoke(prompt)
            
            return {
                "summary": result.strip(),
                "original_length": len(text_content),
                "summary_length": len(result.strip())
            }
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return {"error": str(e)}

    def extract_structured_data(self, text_content: str, document_type: str = "general") -> Dict[str, Any]:
        """Extract structured data based on document type"""
        try:
            if document_type == "invoice":
                prompt = f"""Extract key invoice data from: {text_content[:1000]}
Return as JSON: {{"amount": "value", "date": "value", "vendor": "value"}}"""
            elif document_type == "form":
                prompt = f"""Extract form fields from: {text_content[:1000]}
Return as JSON: {{"fields": [{{"name": "value"}}]}}"""
            elif document_type == "meeting":
                prompt = f"""Extract meeting details from: {text_content[:1000]}
Return as JSON: {{"date": "value", "participants": ["name"], "decisions": ["decision"]}}"""
            else:
                prompt = f"""Extract key information from: {text_content[:1000]}
Return as JSON: {{"key_info": "value"}}"""
            
            result = self.llm.invoke(prompt)
            
            try:
                # Try to parse JSON response
                parsed_data = json.loads(result.strip())
                return {"extracted_data": parsed_data}
            except json.JSONDecodeError:
                # If JSON parsing fails, return as text
                return {"summary": result.strip()}
                
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            return {"error": str(e)}

    def generate_action_items(self, text_content: str) -> Dict[str, Any]:
        """Generate action items from the content"""
        try:
            prompt = self.action_items_prompt.format(text=text_content[:1000])  # Reduced for speed
            result = self.llm.invoke(prompt)
            
            try:
                # Try to parse JSON response
                parsed_result = json.loads(result.strip())
                return parsed_result
            except json.JSONDecodeError:
                # If JSON parsing fails, parse action items manually
                action_items = [item.strip() for item in result.split('\n') if item.strip()]
                return {
                    "action_items": action_items,
                    "count": len(action_items)
                }
        except Exception as e:
            logger.error(f"Action items generation failed: {e}")
            return {"error": str(e)}

    def answer_question(self, text_content: str, question: str, document_id: str = None) -> Dict[str, Any]:
        """Answer a specific question about the document"""
        try:
            prompt = f"""Based on this text, answer the question.

Text: {text_content[:1500]}

Question: {question}

Answer:"""
            
            result = self.llm.invoke(prompt)
            
            return {
                "answer": result.strip(),
                "question": question,
                "document_id": document_id
            }
        except Exception as e:
            logger.error(f"Question answering failed: {e}")
            return {"error": str(e)}

    def analyze_content_unified(self, text_content: str, document_type: str = "general") -> Dict[str, Any]:
        """Unified analysis that combines summary, structured data, and action items in one LLM call"""
        try:
            # Use recursive summarization for long docs
            if len(text_content) > 3000:
                summary_result = self.summarize_document(text_content)
            else:
                summary_result = self.summarize_content(text_content)
            # Use shorter text for structured data/action items for speed
            limited_text = text_content[:1000] if len(text_content) > 1000 else text_content
            structured_data = self.extract_structured_data(limited_text, document_type)
            action_items = self.generate_action_items(limited_text)
            return {
                "summary": summary_result,
                "structured_data": structured_data,
                "action_items": action_items
            }
        except Exception as e:
            logger.error(f"Unified analysis failed: {e}")
            return self._fallback_individual_analysis(text_content, document_type)

    def _fallback_individual_analysis(self, text_content: str, document_type: str) -> Dict[str, Any]:
        """Fallback to individual analysis methods if unified analysis fails"""
        try:
            summary_result = self.summarize_content(text_content)
            structured_data = self.extract_structured_data(text_content, document_type)
            action_items = self.generate_action_items(text_content)
            
            return {
                "summary": summary_result,
                "structured_data": structured_data,
                "action_items": action_items
            }
        except Exception as e:
            logger.error(f"Fallback analysis failed: {e}")
            return {
                "summary": {"error": f"Analysis failed: {e}"},
                "structured_data": {"error": f"Analysis failed: {e}"},
                "action_items": {"error": f"Analysis failed: {e}"}
            }

# Global instance
text_analysis_service = TextAnalysisService() 