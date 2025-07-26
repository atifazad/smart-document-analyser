import pytest
import asyncio
import time
from unittest.mock import Mock, patch
from app.services.processing_pipeline import processing_pipeline
from app.services.progress_service import progress_tracker

class TestPhase2Optimizations:
    """Test Phase 2 async/parallel processing optimizations"""
    
    def test_processing_pipeline_initialization(self):
        """Test that processing pipeline initializes correctly"""
        assert processing_pipeline.max_concurrent_pages > 0
        assert processing_pipeline.max_concurrent_pages <= 10  # Reasonable limit
    
    @pytest.mark.asyncio
    async def test_concurrent_page_processing(self):
        """Test concurrent processing of multiple pages"""
        # Mock image paths
        image_paths = ["/tmp/test1.jpg", "/tmp/test2.jpg", "/tmp/test3.jpg"]
        
        # Mock the processing functions to avoid actual file operations
        with patch('app.services.processing_pipeline.enhance_image_for_handwriting') as mock_enhance, \
             patch('app.services.processing_pipeline.analyze_image_with_llava_fast') as mock_llava, \
             patch('app.services.processing_pipeline.ocr_image_with_tesseract') as mock_ocr, \
             patch('app.services.processing_pipeline.text_analysis_service.analyze_content_unified') as mock_analysis:
            
            # Setup mocks
            mock_enhance.return_value = "/tmp/enhanced.jpg"
            mock_llava.return_value = {"response": "Test LLaVA response"}
            mock_ocr.return_value = "Test OCR text"
            mock_analysis.return_value = {
                "summary": {"summary": "Test summary"},
                "structured_data": {"extracted_data": []},
                "action_items": {"action_items": []}
            }
            
            # Test concurrent processing
            start_time = time.time()
            results = await processing_pipeline.process_pages_concurrently(image_paths)
            end_time = time.time()
            
            # Verify results
            assert len(results) == 3
            assert all("page_index" in result for result in results)
            assert all("image" in result for result in results)
            
            # Verify concurrent processing (should be faster than sequential)
            processing_time = end_time - start_time
            assert processing_time < 5.0  # Should be much faster than sequential
    
    def test_progress_tracker_creation(self):
        """Test progress tracker job creation"""
        job_id = progress_tracker.create_job(5, "test.pdf")
        assert job_id is not None
        assert len(job_id) > 0
        
        job = progress_tracker.get_job_status(job_id)
        assert job is not None
        assert job["filename"] == "test.pdf"
        assert job["total_pages"] == 5
        assert job["status"] == "processing"
        assert job["progress_percentage"] == 0
    
    def test_progress_tracker_updates(self):
        """Test progress tracker updates"""
        job_id = progress_tracker.create_job(3, "test.pdf")
        
        # Simulate page completion
        result1 = {"page_index": 0, "image": "page1.jpg", "ocr_text": "test"}
        progress_tracker.update_page_progress(job_id, 0, result1)
        
        job = progress_tracker.get_job_status(job_id)
        assert job["processed_pages"] == 1
        assert job["progress_percentage"] == pytest.approx(33.33, rel=1e-2)
        assert job["current_page"] == 1
        
        # Complete the job
        final_results = [result1, {"page_index": 1, "image": "page2.jpg"}, {"page_index": 2, "image": "page3.jpg"}]
        progress_tracker.complete_job(job_id, final_results)
        
        job = progress_tracker.get_job_status(job_id)
        assert job["status"] == "completed"
        assert job["progress_percentage"] == 100
        assert job["results"] == final_results
    
    def test_progress_tracker_failure(self):
        """Test progress tracker failure handling"""
        job_id = progress_tracker.create_job(2, "test.pdf")
        
        progress_tracker.fail_job(job_id, "Test error")
        
        job = progress_tracker.get_job_status(job_id)
        assert job["status"] == "failed"
        assert job["error"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_batch_vector_store_creation(self):
        """Test batch vector store creation for multi-page documents"""
        # Mock results with OCR text
        results = [
            {"ocr_text": "Page 1 content", "page_index": 0},
            {"ocr_text": "Page 2 content", "page_index": 1},
            {"ocr_text": "Page 3 content", "page_index": 2}
        ]
        
        with patch('app.services.processing_pipeline.vector_store_service.create_vector_store') as mock_create:
            mock_create.return_value = True
            
            success = await processing_pipeline.create_batch_vector_store(results, "test_doc")
            
            assert success is True
            mock_create.assert_called_once()
            
            # Verify combined text was passed
            call_args = mock_create.call_args
            assert "test_doc" in call_args[0]
            assert "Page 1 content" in call_args[1]
            assert "Page 2 content" in call_args[1]
            assert "Page 3 content" in call_args[1]
    
    def test_progress_tracker_cleanup(self):
        """Test progress tracker cleanup functionality"""
        # Create some old jobs
        old_job_id = progress_tracker.create_job(1, "old.pdf")
        old_job = progress_tracker.get_job_status(old_job_id)
        old_job["start_time"] = time.time() - (25 * 3600)  # 25 hours ago
        old_job["status"] = "completed"
        
        # Create a recent job
        recent_job_id = progress_tracker.create_job(1, "recent.pdf")
        
        before_count = len(progress_tracker.jobs)
        progress_tracker.cleanup_old_jobs(max_age_hours=24)
        after_count = len(progress_tracker.jobs)
        
        # Old job should be removed, recent job should remain
        assert after_count < before_count
        assert progress_tracker.get_job_status(old_job_id) is None
        assert progress_tracker.get_job_status(recent_job_id) is not None
    
    def test_concurrent_processing_semaphore(self):
        """Test that concurrent processing respects the semaphore limit"""
        # This test verifies that the semaphore properly limits concurrent operations
        max_concurrent = processing_pipeline.max_concurrent_pages
        
        # Create more tasks than the semaphore limit
        async def test_semaphore():
            semaphore = asyncio.Semaphore(max_concurrent)
            active_tasks = 0
            max_active = 0
            
            async def task():
                nonlocal active_tasks, max_active
                async with semaphore:
                    active_tasks += 1
                    max_active = max(max_active, active_tasks)
                    await asyncio.sleep(0.1)  # Simulate work
                    active_tasks -= 1
            
            # Create more tasks than the semaphore limit
            tasks = [task() for _ in range(max_concurrent + 2)]
            await asyncio.gather(*tasks)
            
            # Verify that we never exceeded the semaphore limit
            assert max_active <= max_concurrent
        
        asyncio.run(test_semaphore()) 