import os
import json
from typing import Dict, Any, List, Optional
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from .vector_store_service import vector_store_service

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
TEXT_MODEL = os.getenv("TEXT_MODEL", "llama3.1:8b")

class TextAnalysisServiceError(Exception):
    pass

class TextAnalysisService:
    def __init__(self):
        self.llm = OllamaLLM(
            model=TEXT_MODEL,
            base_url=OLLAMA_HOST
        )
        self.embeddings = OllamaEmbeddings(
            model=TEXT_MODEL,
            base_url=OLLAMA_HOST
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def summarize_content(self, text_content: str) -> Dict[str, Any]:
        """Summarize the extracted text content"""
        try:
            prompt_template = PromptTemplate(
                input_variables=["text"],
                template="""Summarize the following document content in a clear and concise manner:

{text}

Provide a summary that includes:
1. Main topic or purpose of the document
2. Key points and important information
3. Any action items or next steps mentioned
4. Important dates, names, or numbers

Summary:"""
            )
            
            # Use newer LangChain pattern
            chain = prompt_template | self.llm
            result = chain.invoke({"text": text_content})
            
            return {
                "summary": result.strip(),
                "original_length": len(text_content),
                "summary_length": len(result)
            }
        except Exception as e:
            raise TextAnalysisServiceError(f"Summarization failed: {e}")
    
    def extract_structured_data(self, text_content: str, document_type: str) -> Dict[str, Any]:
        """Extract structured data based on document type"""
        try:
            if document_type.lower() in ["invoice", "receipt"]:
                return self._extract_financial_data(text_content)
            elif document_type.lower() in ["form", "application"]:
                return self._extract_form_fields(text_content)
            elif document_type.lower() in ["meeting", "notes", "report"]:
                return self._extract_meeting_data(text_content)
            else:
                return self._extract_general_data(text_content)
        except Exception as e:
            raise TextAnalysisServiceError(f"Structured data extraction failed: {e}")
    
    def _extract_financial_data(self, text_content: str) -> Dict[str, Any]:
        """Extract financial data from invoices/receipts"""
        prompt_template = PromptTemplate(
            input_variables=["text"],
            template="""Extract financial information from this document and return it as JSON:

{text}

Return a JSON object with the following structure:
{{
    "total_amount": "amount in currency",
    "currency": "currency code",
    "date": "date in YYYY-MM-DD format",
    "vendor": "vendor/company name",
    "items": [
        {{
            "description": "item description",
            "quantity": "quantity",
            "price": "price per item",
            "total": "total for this item"
        }}
    ],
    "tax_amount": "tax amount if present",
    "reference_number": "invoice/receipt number",
    "payment_method": "payment method if mentioned"
}}

JSON:"""
        )
        
        # Use newer LangChain pattern
        chain = prompt_template | self.llm
        result = chain.invoke({"text": text_content})
        
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response", "raw_response": result}
    
    def _extract_form_fields(self, text_content: str) -> Dict[str, Any]:
        """Extract form fields and their values"""
        prompt_template = PromptTemplate(
            input_variables=["text"],
            template="""Extract form fields and their values from this document and return as JSON:

{text}

Return a JSON object with the following structure:
{{
    "form_type": "type of form",
    "fields": [
        {{
            "field_name": "name of the field",
            "field_value": "value entered in the field",
            "field_type": "text, date, number, checkbox, etc."
        }}
    ],
    "required_fields": ["list of required field names"],
    "optional_fields": ["list of optional field names"]
}}

JSON:"""
        )
        
        # Use newer LangChain pattern
        chain = prompt_template | self.llm
        result = chain.invoke({"text": text_content})
        
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response", "raw_response": result}
    
    def _extract_meeting_data(self, text_content: str) -> Dict[str, Any]:
        """Extract meeting information and action items"""
        prompt_template = PromptTemplate(
            input_variables=["text"],
            template="""Extract meeting information and action items from this document and return as JSON:

{text}

Return a JSON object with the following structure:
{{
    "meeting_title": "title of the meeting",
    "date": "meeting date",
    "participants": ["list of participants"],
    "agenda_items": [
        {{
            "topic": "agenda topic",
            "discussion": "summary of discussion",
            "decisions": ["list of decisions made"]
        }}
    ],
    "action_items": [
        {{
            "task": "action item description",
            "assignee": "person responsible",
            "due_date": "due date if mentioned",
            "priority": "high/medium/low"
        }}
    ],
    "next_meeting": "date of next meeting if mentioned"
}}

JSON:"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        result = chain.run(text=text_content)
        
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response", "raw_response": result}
    
    def _extract_general_data(self, text_content: str) -> Dict[str, Any]:
        """Extract general information from any document"""
        prompt_template = PromptTemplate(
            input_variables=["text"],
            template="""Extract key information from this document and return as JSON:

{text}

Return a JSON object with the following structure:
{{
    "document_type": "type of document",
    "title": "document title",
    "author": "author if mentioned",
    "date": "document date",
    "key_entities": ["important people, places, organizations"],
    "key_dates": ["important dates mentioned"],
    "key_numbers": ["important numbers, amounts, quantities"],
    "main_topics": ["main topics discussed"],
    "key_points": ["key points or findings"]
}}

JSON:"""
        )
        
        # Use newer LangChain pattern
        chain = prompt_template | self.llm
        result = chain.invoke({"text": text_content})
        
        try:
            return json.loads(result.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON response", "raw_response": result}
    
    def _get_context_from_text(self, text_content: str, question: str) -> str:
        """Helper method to get context from text using in-memory vector store"""
        docs = [Document(page_content=text_content)]
        splits = self.text_splitter.split_documents(docs)
        vectorstore = FAISS.from_documents(splits, self.embeddings)
        relevant_docs = vectorstore.similarity_search(question, k=3)
        return "\n".join([doc.page_content for doc in relevant_docs])
    
    def answer_question(self, text_content: str, question: str, document_id: str = None) -> Dict[str, Any]:
        """Answer questions about the document content"""
        try:
            # If document_id is provided, try to use stored vector store
            if document_id:
                relevant_docs = vector_store_service.search_similar(document_id, question, k=3)
                if relevant_docs:
                    context = "\n".join([doc.page_content for doc in relevant_docs])
                else:
                    # Fallback to in-memory processing
                    context = self._get_context_from_text(text_content, question)
            else:
                # Use in-memory processing
                context = self._get_context_from_text(text_content, question)
            
            prompt_template = PromptTemplate(
                input_variables=["context", "question"],
                template="""Answer the question based on the following document context:

Context:
{context}

Question: {question}

Answer the question accurately using only the information provided in the context. If the answer cannot be found in the context, say so.

Answer:"""
            )
            
            # Use newer LangChain pattern
            chain = prompt_template | self.llm
            result = chain.invoke({"context": context, "question": question})
            
            return {
                "question": question,
                "answer": result.strip(),
                "context_used": len(context),
                "vector_store_used": document_id is not None and bool(relevant_docs)
            }
        except Exception as e:
            raise TextAnalysisServiceError(f"Question answering failed: {e}")
    
    def generate_action_items(self, text_content: str) -> Dict[str, Any]:
        """Generate action items from document content"""
        try:
            prompt_template = PromptTemplate(
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
            
            # Use newer LangChain pattern
            chain = prompt_template | self.llm
            result = chain.invoke({"text": text_content})
            
            try:
                return json.loads(result.strip())
            except json.JSONDecodeError:
                return {"error": "Failed to parse JSON response", "raw_response": result}
        except Exception as e:
            raise TextAnalysisServiceError(f"Action item generation failed: {e}")

# Global instance
text_analysis_service = TextAnalysisService() 