from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
import logging
from uuid import uuid4
from app.services.file_service import (
    convert_pdf_to_images, 
    validate_and_standardize_image, 
    enhance_image_for_handwriting,
    ocr_image_with_tesseract
)
from app.services.llava_service import (
    analyze_image_with_llava,
    analyze_image_with_llava_fast,
    LLaVAServiceError
)
from app.services.text_analysis_service import text_analysis_service, TextAnalysisServiceError
from app.services.vector_store_service import vector_store_service
from app.services.processing_pipeline import processing_pipeline
from app.services.progress_service import progress_tracker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

UPLOAD_DIR = "/tmp/sda_uploads"
PROCESSED_DIR = "/tmp/sda_processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

async def process_document_background(job_id: str, image_paths: list, filename: str):
    """Background task for processing documents with progress tracking"""
    try:
        logger.info(f"Starting background processing for job {job_id}")
        
        # Process pages concurrently
        results = await processing_pipeline.process_pages_concurrently(image_paths)
        
        # Update progress for each completed page
        for i, result in enumerate(results):
            progress_tracker.update_page_progress(job_id, i, result)
        
        # Create batch vector store for entire document
        if len(results) > 1:
            # For multi-page documents, create a single vector store
            document_id = f"{os.path.splitext(filename)[0]}_{uuid4().hex[:8]}"
            vector_store_created = await processing_pipeline.create_batch_vector_store(results, document_id)
            logger.info(f"Batch vector store creation: {'success' if vector_store_created else 'failed'}")
        else:
            # For single page, use the existing vector store creation
            vector_store_created = True
            for result in results:
                if result.get("document_id"):
                    vector_store_created = vector_store_service.create_vector_store(
                        result["document_id"], 
                        result.get("ocr_text", "")
                    )
        
        # Prepare final response
        final_results = []
        for result in results:
            # Remove page_index from final response
            final_result = {
                "image": result["image"],
                "enhanced_image": result.get("enhanced_image"),
                "llava_result": result.get("llava_result"),
                "llava_error": result.get("llava_error"),
                "ocr_text": result.get("ocr_text", ""),
                "ocr_error": result.get("ocr_error"),
                "text_analysis": result.get("text_analysis", {}),
                "error": result.get("error")
            }
            final_results.append(final_result)
        
        # Mark job as completed
        progress_tracker.complete_job(job_id, final_results)
        logger.info(f"Completed background processing for job {job_id}")
        
    except Exception as e:
        logger.error(f"Background processing failed for job {job_id}: {e}")
        progress_tracker.fail_job(job_id, str(e))

@router.post("/upload", status_code=202)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload and process document with background processing and progress tracking"""
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    ext = os.path.splitext(file.filename)[-1]
    safe_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_paths = []
    # If PDF, convert to images
    if file.content_type == "application/pdf":
        try:
            image_paths = convert_pdf_to_images(dest_path, PROCESSED_DIR)
            logger.info(f"Converted PDF to {len(image_paths)} images")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")
    else:
        # Validate and standardize image
        try:
            std_img = validate_and_standardize_image(dest_path, PROCESSED_DIR)
            image_paths = [std_img]
            logger.info("Processed single image")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image validation failed: {e}")

    # Create progress tracking job
    job_id = progress_tracker.create_job(len(image_paths), safe_name)
    
    # Start background processing
    background_tasks.add_task(
        process_document_background, 
        job_id, 
        image_paths, 
        safe_name
    )
    
    return JSONResponse({
        "message": "Document uploaded and processing started",
        "job_id": job_id,
        "filename": safe_name,
        "content_type": file.content_type,
        "total_pages": len(image_paths),
        "status": "processing",
        "progress_url": f"/api/jobs/{job_id}"
    }, status_code=202)

@router.post("/upload-sync", status_code=201)
async def upload_file_sync(file: UploadFile = File(...)):
    """Synchronous upload endpoint for immediate processing (legacy compatibility)"""
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    
    ext = os.path.splitext(file.filename)[-1]
    safe_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_paths = []
    # If PDF, convert to images
    if file.content_type == "application/pdf":
        try:
            image_paths = convert_pdf_to_images(dest_path, PROCESSED_DIR)
            logger.info(f"Converted PDF to {len(image_paths)} images")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")
    else:
        # Validate and standardize image
        try:
            std_img = validate_and_standardize_image(dest_path, PROCESSED_DIR)
            image_paths = [std_img]
            logger.info("Processed single image")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image validation failed: {e}")

    # Use async processing pipeline for concurrent page processing
    try:
        logger.info(f"Starting concurrent processing of {len(image_paths)} pages")
        results = await processing_pipeline.process_pages_concurrently(image_paths)
        
        # Create batch vector store for entire document
        if len(results) > 1:
            # For multi-page documents, create a single vector store
            document_id = f"{os.path.splitext(safe_name)[0]}_{uuid4().hex[:8]}"
            vector_store_created = await processing_pipeline.create_batch_vector_store(results, document_id)
            logger.info(f"Batch vector store creation: {'success' if vector_store_created else 'failed'}")
        else:
            # For single page, use the existing vector store creation
            vector_store_created = True
            for result in results:
                if result.get("document_id"):
                    vector_store_created = vector_store_service.create_vector_store(
                        result["document_id"], 
                        result.get("ocr_text", "")
                    )
        
        # Prepare final response
        final_results = []
        for result in results:
            # Remove page_index from final response
            final_result = {
                "image": result["image"],
                "enhanced_image": result.get("enhanced_image"),
                "llava_result": result.get("llava_result"),
                "llava_error": result.get("llava_error"),
                "ocr_text": result.get("ocr_text", ""),
                "ocr_error": result.get("ocr_error"),
                "text_analysis": result.get("text_analysis", {}),
                "error": result.get("error")
            }
            final_results.append(final_result)

        logger.info(f"Completed processing {len(final_results)} pages")
        
        return JSONResponse({
            "filename": safe_name,
            "content_type": file.content_type,
            "status": "uploaded",
            "results": final_results,
            "processing_info": {
                "total_pages": len(image_paths),
                "processed_pages": len(final_results),
                "concurrent_processing": True,
                "batch_vector_store": len(image_paths) > 1
            }
        })
        
    except Exception as e:
        logger.error(f"Processing pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

@router.post("/upload-legacy", status_code=201)
async def upload_file_legacy(file: UploadFile = File(...)):
    """Legacy sequential processing endpoint for comparison"""
    allowed_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    ext = os.path.splitext(file.filename)[-1]
    safe_name = f"{uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_paths = []
    # If PDF, convert to images
    if file.content_type == "application/pdf":
        try:
            image_paths = convert_pdf_to_images(dest_path, PROCESSED_DIR)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF conversion failed: {e}")
    else:
        # Validate and standardize image
        try:
            std_img = validate_and_standardize_image(dest_path, PROCESSED_DIR)
            image_paths = [std_img]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image validation failed: {e}")

    results = []
    for img_path in image_paths:
        # Enhance image for better LLaVA processing
        try:
            enhanced_img_path = enhance_image_for_handwriting(img_path, PROCESSED_DIR)
        except Exception:
            enhanced_img_path = img_path

        # Run LLaVA analysis with optimized prompt
        llava_result = None
        llava_error = None
        try:
            # Use fast LLaVA analysis for better performance
            llava_result = analyze_image_with_llava_fast(enhanced_img_path)
        except LLaVAServiceError as e:
            llava_error = str(e)

        # Extract text content using OCR
        ocr_text = ""
        ocr_error = None
        try:
            ocr_text = ocr_image_with_tesseract(enhanced_img_path)
        except Exception as e:
            ocr_error = str(e)

        # Perform unified text analysis if we have text content
        text_analysis_results = {}
        document_id = None
        
        if ocr_text.strip():
            try:
                # Create document ID for vector store
                document_id = f"{os.path.splitext(os.path.basename(img_path))[0]}_{uuid4().hex[:8]}"
                
                # Create vector store for this document
                vector_store_created = vector_store_service.create_vector_store(document_id, ocr_text)
                
                # Extract document type from LLaVA analysis
                document_type = "general"
                if llava_result and "response" in llava_result:
                    llava_response = llava_result["response"]
                    if any(word in llava_response.lower() for word in ["invoice", "receipt"]):
                        document_type = "invoice"
                    elif any(word in llava_response.lower() for word in ["form", "application"]):
                        document_type = "form"
                    elif any(word in llava_response.lower() for word in ["meeting", "notes"]):
                        document_type = "meeting"

                logger.info(f"Processing document type: {document_type}")
                logger.info(f"OCR text length: {len(ocr_text)}")

                # Use unified analysis for better performance
                unified_analysis = text_analysis_service.analyze_content_unified(ocr_text, document_type)
                
                logger.info(f"Unified analysis result keys: {list(unified_analysis.keys()) if isinstance(unified_analysis, dict) else 'Not a dict'}")
                
                # Ensure all components are present in the results
                text_analysis_results = {
                    "summary": unified_analysis.get("summary", {}),
                    "structured_data": unified_analysis.get("structured_data", {}),
                    "action_items": unified_analysis.get("action_items", {}),
                    "document_type": document_type,
                    "document_id": document_id,
                    "vector_store_created": vector_store_created
                }
                
                # Validate that we have actual content, not just error messages
                if (isinstance(text_analysis_results["summary"], dict) and 
                    "error" in text_analysis_results["summary"]):
                    logger.warning("Unified analysis failed, trying individual methods")
                    # If unified analysis failed, try individual methods
                    try:
                        summary_result = text_analysis_service.summarize_content(ocr_text)
                        structured_data = text_analysis_service.extract_structured_data(ocr_text, document_type)
                        action_items = text_analysis_service.generate_action_items(ocr_text)
                        
                        text_analysis_results.update({
                            "summary": summary_result,
                            "structured_data": structured_data,
                            "action_items": action_items
                        })
                        logger.info("Individual analysis methods succeeded")
                    except Exception as e:
                        logger.error(f"Individual analysis methods failed: {e}")
                        text_analysis_results["analysis_error"] = f"Text analysis failed: {e}"
                        
            except Exception as e:
                logger.error(f"Text analysis failed: {e}")
                text_analysis_results = {"error": str(e)}

        results.append({
            "image": os.path.basename(img_path),
            "enhanced_image": os.path.basename(enhanced_img_path) if enhanced_img_path != img_path else None,
            "llava_result": llava_result,
            "llava_error": llava_error,
            "ocr_text": ocr_text,
            "ocr_error": ocr_error,
            "text_analysis": text_analysis_results
        })

    return JSONResponse({
        "filename": safe_name,
        "content_type": file.content_type,
        "status": "uploaded",
        "results": results,
        "processing_info": {
            "total_pages": len(image_paths),
            "processed_pages": len(results),
            "concurrent_processing": False,
            "batch_vector_store": False
        }
    })
