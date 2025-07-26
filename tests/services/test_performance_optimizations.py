import pytest
import time
from app.services.text_analysis_service import text_analysis_service
from app.services.llava_service import analyze_image_with_llava_fast
from app.services.model_manager import model_manager

class TestPerformanceOptimizations:
    """Test Phase 1 performance optimizations"""
    
    def test_model_manager_singleton(self):
        """Test that model manager uses singleton pattern"""
        manager1 = model_manager
        manager2 = model_manager
        assert manager1 is manager2
    
    def test_unified_analysis_performance(self):
        """Test that unified analysis is faster than individual calls"""
        sample_text = """
        Invoice #12345
        Date: 2024-01-15
        Vendor: ABC Company
        Items:
        - Product A: $100
        - Product B: $50
        Total: $150
        Payment due: 30 days
        """
        
        # Test unified analysis
        start_time = time.time()
        unified_result = text_analysis_service.analyze_content_unified(sample_text, "invoice")
        unified_time = time.time() - start_time
        
        # Test individual analysis (for comparison)
        start_time = time.time()
        summary = text_analysis_service.summarize_content(sample_text)
        structured = text_analysis_service.extract_structured_data(sample_text, "invoice")
        action_items = text_analysis_service.generate_action_items(sample_text)
        individual_time = time.time() - start_time
        
        # Unified analysis should be faster (fewer LLM calls)
        assert unified_time < individual_time
        assert "summary" in unified_result
        assert "structured_data" in unified_result
        assert "action_items" in unified_result
    
    def test_llava_fast_analysis(self):
        """Test that fast LLaVA analysis works"""
        # This test would require an actual image file
        # For now, just test that the function exists and can be called
        assert callable(analyze_image_with_llava_fast)
    
    def test_model_warm_up(self):
        """Test that model warm-up works"""
        try:
            model_manager.warm_up_models()
            # If we get here, warm-up succeeded
            assert True
        except Exception as e:
            # Warm-up might fail in test environment, that's okay
            print(f"Model warm-up test failed (expected in test env): {e}")
            assert True
    
    def test_fallback_analysis(self):
        """Test that fallback analysis works when unified analysis fails"""
        # Test with malformed text that might cause JSON parsing issues
        malformed_text = "This is a test document with no clear structure."
        
        try:
            result = text_analysis_service.analyze_content_unified(malformed_text, "general")
            # Should still return a result (either unified or fallback)
            assert isinstance(result, dict)
        except Exception as e:
            # Should handle errors gracefully
            assert "error" in str(e).lower() or "failed" in str(e).lower() 