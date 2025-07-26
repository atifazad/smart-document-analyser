import asyncio
import os
import logging
from typing import List, Dict, Any, Optional
from uuid import uuid4
from app.services.file_service import (
    convert_pdf_to_images, 
    validate_and_standardize_image, 
    enhance_image_for_handwriting,
    ocr_image_with_tesseract
)
from app.services.text_analysis_service import text_analysis_service, TextAnalysisServiceError
from app.services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """Async processing pipeline for concurrent document analysis"""
    
    def __init__(self):
        self.max_concurrent_pages = int(os.getenv("MAX_CONCURRENT_PROCESSES", "4"))
    
    async def process_single_page(self, img_path: str, page_index: int) -> Dict[str, Any]:
        """Process a single page/image asynchronously (LLaVA analysis removed)"""
        try:
            logger.info(f"Processing page {page_index + 1}: {os.path.basename(img_path)}")
            
            # Enhance image for better OCR processing (run in thread pool)
            try:
                enhanced_img_path = await asyncio.to_thread(
                    enhance_image_for_handwriting, img_path, "/tmp/sda_processed"
                )
            except Exception:
                enhanced_img_path = img_path

            # Extract text content using OCR (run in thread pool)
            ocr_text = ""
            ocr_error = None
            try:
                ocr_text = await asyncio.to_thread(
                    ocr_image_with_tesseract, enhanced_img_path
                )
            except Exception as e:
                ocr_error = str(e)

            # Perform unified text analysis if we have text content (run in thread pool)
            text_analysis_results = {}
            document_id = None
            
            if ocr_text.strip():
                try:
                    # Create document ID for vector store
                    document_id = f"{os.path.splitext(os.path.basename(img_path))[0]}_{uuid4().hex[:8]}"
                    
                    # Use general document type since we don't have LLaVA analysis
                    document_type = "general"

                    # Use unified analysis for better performance (run in thread pool)
                    unified_analysis = await asyncio.to_thread(
                        text_analysis_service.analyze_content_unified, ocr_text, document_type
                    )
                    
                    # Ensure all components are present in the results
                    text_analysis_results = {
                        "summary": unified_analysis.get("summary", {}),
                        "structured_data": unified_analysis.get("structured_data", {}),
                        "action_items": unified_analysis.get("action_items", {}),
                        "document_type": document_type,
                        "document_id": document_id,
                        "vector_store_created": False  # Will be handled later for batching
                    }
                    
                    # Validate that we have actual content, not just error messages
                    if (isinstance(text_analysis_results["summary"], dict) and 
                        "error" in text_analysis_results["summary"]):
                        logger.warning(f"Unified analysis failed for page {page_index + 1}, trying individual methods")
                        # If unified analysis failed, try individual methods
                        try:
                            summary_result = await asyncio.to_thread(
                                text_analysis_service.summarize_content, ocr_text
                            )
                            structured_data = await asyncio.to_thread(
                                text_analysis_service.extract_structured_data, ocr_text, document_type
                            )
                            action_items = await asyncio.to_thread(
                                text_analysis_service.generate_action_items, ocr_text
                            )
                            
                            text_analysis_results.update({
                                "summary": summary_result,
                                "structured_data": structured_data,
                                "action_items": action_items
                            })
                            logger.info(f"Individual analysis methods succeeded for page {page_index + 1}")
                        except Exception as e:
                            logger.error(f"Individual analysis methods failed for page {page_index + 1}: {e}")
                            text_analysis_results["analysis_error"] = f"Text analysis failed: {e}"
                            
                except Exception as e:
                    logger.error(f"Text analysis failed for page {page_index + 1}: {e}")
                    text_analysis_results = {"error": str(e)}

            return {
                "page_index": page_index,
                "image": os.path.basename(img_path),
                "enhanced_image": os.path.basename(enhanced_img_path) if enhanced_img_path != img_path else None,
                "llava_result": None,  # LLaVA analysis removed
                "llava_error": "LLaVA analysis disabled for performance",
                "ocr_text": ocr_text,
                "ocr_error": ocr_error,
                "text_analysis": text_analysis_results,
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error processing page {page_index + 1}: {e}")
            return {
                "page_index": page_index,
                "image": os.path.basename(img_path),
                "error": str(e)
            }
    
    async def process_pages_concurrently(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Process multiple pages concurrently with controlled concurrency"""
        logger.info(f"Processing {len(image_paths)} pages with max concurrency: {self.max_concurrent_pages}")
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(self.max_concurrent_pages)
        
        async def process_with_semaphore(img_path: str, page_index: int):
            async with semaphore:
                return await self.process_single_page(img_path, page_index)
        
        # Create tasks for all pages
        tasks = [
            process_with_semaphore(img_path, i) 
            for i, img_path in enumerate(image_paths)
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and sort by page index
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
            else:
                processed_results.append(result)
        
        # Sort by page index to maintain order
        processed_results.sort(key=lambda x: x.get("page_index", 0))
        
        logger.info(f"Completed processing {len(processed_results)} pages")
        return processed_results
    
    async def create_batch_vector_store(self, results: List[Dict[str, Any]], document_id: str) -> bool:
        """Create vector store for entire document instead of per page"""
        try:
            # Collect all OCR text from all pages
            all_text = []
            for result in results:
                if result.get("ocr_text"):
                    all_text.append(result["ocr_text"])
            
            if not all_text:
                logger.warning("No OCR text available for vector store creation")
                return False
            
            # Combine all text with page separators
            combined_text = "\n\n--- PAGE SEPARATOR ---\n\n".join(all_text)
            
            # Create vector store for entire document (run in thread pool)
            success = await asyncio.to_thread(
                vector_store_service.create_vector_store, document_id, combined_text
            )
            
            if success:
                logger.info(f"Created batch vector store for document: {document_id}")
                # Update all results to indicate vector store was created
                for result in results:
                    if "text_analysis" in result and isinstance(result["text_analysis"], dict):
                        result["text_analysis"]["vector_store_created"] = True
                        result["text_analysis"]["document_id"] = document_id
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create batch vector store: {e}")
            return False

# Global instance
processing_pipeline = ProcessingPipeline() 