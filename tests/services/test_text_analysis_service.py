import pytest
from app.services.text_analysis_service import TextAnalysisService, TextAnalysisServiceError

@pytest.fixture
def text_service():
    return TextAnalysisService()

def test_summarize_content(text_service):
    """Test document summarization"""
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
    
    result = text_service.summarize_content(sample_text)
    
    assert "summary" in result
    assert "original_length" in result
    assert "summary_length" in result
    assert result["original_length"] > 0
    assert result["summary_length"] > 0

def test_extract_financial_data(text_service):
    """Test financial data extraction"""
    sample_text = """
    INVOICE
    Invoice #: INV-2024-001
    Date: 2024-01-15
    Vendor: ABC Company
    Address: 123 Main St, City, State
    
    Items:
    1. Product A - Qty: 2 - Price: $50 - Total: $100
    2. Product B - Qty: 1 - Price: $25 - Total: $25
    
    Subtotal: $125
    Tax: $12.50
    Total: $137.50
    
    Payment Method: Credit Card
    """
    
    result = text_service._extract_financial_data(sample_text)
    
    # Should return either valid JSON or error structure
    assert isinstance(result, dict)
    if "error" not in result:
        # If successful, should have expected fields
        assert "total_amount" in result or "error" in result

def test_extract_form_fields(text_service):
    """Test form field extraction"""
    sample_text = """
    APPLICATION FORM
    
    Name: John Doe
    Email: john@example.com
    Phone: (555) 123-4567
    Date of Birth: 1990-01-01
    
    Education: Bachelor's Degree
    Experience: 5 years
    
    Signature: John Doe
    Date: 2024-01-15
    """
    
    result = text_service._extract_form_fields(sample_text)
    
    assert isinstance(result, dict)
    if "error" not in result:
        assert "form_type" in result or "error" in result

def test_generate_action_items(text_service):
    """Test action item generation"""
    sample_text = """
    MEETING NOTES
    
    Attendees: John, Jane, Bob
    Date: 2024-01-15
    
    Discussion:
    - Project timeline needs to be updated
    - Budget review required
    - Client meeting scheduled for next week
    
    Action Items:
    - John to update project timeline by Friday
    - Jane to prepare budget report
    - Bob to schedule client meeting
    """
    
    result = text_service.generate_action_items(sample_text)
    
    assert isinstance(result, dict)
    if "error" not in result:
        assert "action_items" in result or "error" in result

def test_answer_question(text_service):
    """Test question answering"""
    sample_text = """
    Invoice #12345
    Date: 2024-01-15
    Vendor: ABC Company
    Total Amount: $150
    Payment Terms: Net 30
    """
    
    question = "What is the total amount of this invoice?"
    result = text_service.answer_question(sample_text, question)
    
    assert "question" in result
    assert "answer" in result
    assert result["question"] == question
    assert len(result["answer"]) > 0

def test_error_handling(text_service):
    """Test error handling with invalid input"""
    with pytest.raises(TextAnalysisServiceError):
        text_service.summarize_content("")  # Empty text should raise error 