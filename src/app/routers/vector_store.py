from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.vector_store_service import vector_store_service

router = APIRouter()

class QuestionRequest(BaseModel):
    document_id: str
    question: str

class DocumentRequest(BaseModel):
    document_id: str
    text_content: str

@router.get("/stats")
async def get_vector_store_stats():
    """Get statistics about stored vector databases"""
    try:
        stats = vector_store_service.get_storage_stats()
        return JSONResponse(stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e}")

@router.get("/documents")
async def list_stored_documents():
    """List all document IDs that have stored vector stores"""
    try:
        documents = vector_store_service.list_stored_documents()
        return JSONResponse({
            "documents": documents,
            "count": len(documents)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")

@router.post("/create")
async def create_vector_store(request: DocumentRequest):
    """Create vector store for a document"""
    try:
        success = vector_store_service.create_vector_store(
            request.document_id, 
            request.text_content
        )
        return JSONResponse({
            "document_id": request.document_id,
            "created": success
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vector store: {e}")

@router.delete("/{document_id}")
async def delete_vector_store(document_id: str):
    """Delete vector store for a document"""
    try:
        success = vector_store_service.delete_vector_store(document_id)
        return JSONResponse({
            "document_id": document_id,
            "deleted": success
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete vector store: {e}")

@router.post("/search")
async def search_vector_store(request: QuestionRequest):
    """Search vector store for a document"""
    try:
        results = vector_store_service.search_similar(
            request.document_id, 
            request.question, 
            k=3
        )
        return JSONResponse({
            "document_id": request.document_id,
            "question": request.question,
            "results": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                } for doc in results
            ],
            "count": len(results)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search vector store: {e}") 