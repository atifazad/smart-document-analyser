from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.text_analysis_service import text_analysis_service, TextAnalysisServiceError

router = APIRouter()

class AnalysisRequest(BaseModel):
    text_content: str
    document_type: Optional[str] = None

class QuestionRequest(BaseModel):
    text_content: str
    question: str

class ActionItemsRequest(BaseModel):
    text_content: str

@router.post("/test-unified")
async def test_unified_analysis(request: AnalysisRequest):
    """Test the unified analysis method"""
    try:
        result = text_analysis_service.analyze_content_unified(
            request.text_content, 
            request.document_type or "general"
        )
        return JSONResponse({
            "success": True,
            "result": result,
            "components": {
                "has_summary": "summary" in result,
                "has_structured_data": "structured_data" in result,
                "has_action_items": "action_items" in result
            }
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        })

@router.post("/summarize")
async def summarize_document(request: AnalysisRequest):
    """Summarize document content"""
    try:
        result = text_analysis_service.summarize_content(request.text_content)
        return JSONResponse({
            "summary": result["summary"],
            "original_length": result["original_length"],
            "summary_length": result["summary_length"],
            "compression_ratio": round(result["summary_length"] / result["original_length"], 2)
        })
    except TextAnalysisServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {e}")

@router.post("/extract-structured-data")
async def extract_structured_data(request: AnalysisRequest):
    """Extract structured data based on document type"""
    try:
        if not request.document_type:
            raise HTTPException(status_code=400, detail="document_type is required")
        
        result = text_analysis_service.extract_structured_data(
            request.text_content, 
            request.document_type
        )
        return JSONResponse(result)
    except TextAnalysisServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structured data extraction failed: {e}")

@router.post("/answer-question")
async def answer_question(request: QuestionRequest):
    """Answer questions about document content"""
    try:
        result = text_analysis_service.answer_question(
            request.text_content, 
            request.question
        )
        return JSONResponse(result)
    except TextAnalysisServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {e}")

@router.post("/generate-action-items")
async def generate_action_items(request: ActionItemsRequest):
    """Generate action items from document content"""
    try:
        result = text_analysis_service.generate_action_items(request.text_content)
        return JSONResponse(result)
    except TextAnalysisServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action item generation failed: {e}")

@router.get("/supported-document-types")
async def get_supported_document_types():
    """Get list of supported document types for structured data extraction"""
    return JSONResponse({
        "supported_types": [
            {
                "type": "invoice",
                "description": "Financial documents with amounts, dates, vendor info"
            },
            {
                "type": "receipt", 
                "description": "Purchase receipts with items, prices, totals"
            },
            {
                "type": "form",
                "description": "Forms with fields and values to extract"
            },
            {
                "type": "application",
                "description": "Application forms with structured data"
            },
            {
                "type": "meeting",
                "description": "Meeting notes with participants, agenda, action items"
            },
            {
                "type": "notes",
                "description": "General notes with key points and action items"
            },
            {
                "type": "report",
                "description": "Reports with findings, conclusions, recommendations"
            }
        ]
    }) 