import os
import shutil
import pytest
from app.services.file_service import convert_pdf_to_images, validate_and_standardize_image

TEST_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

@pytest.fixture(scope="module", autouse=True)
def clean_output():
    # Clean output dir before and after tests
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yield
    shutil.rmtree(OUTPUT_DIR)

@pytest.mark.skipif(not os.path.exists(os.path.join(TEST_DATA_DIR, 'sample.pdf')), reason="sample.pdf not found")
def test_convert_pdf_to_images():
    pdf_path = os.path.join(TEST_DATA_DIR, 'sample.pdf')
    images = convert_pdf_to_images(pdf_path, OUTPUT_DIR)
    assert len(images) > 0
    for img_path in images:
        assert os.path.exists(img_path)
        assert img_path.endswith('.png')

@pytest.mark.skipif(not os.path.exists(os.path.join(TEST_DATA_DIR, 'sample.png')), reason="sample.png not found")
def test_validate_and_standardize_image():
    img_path = os.path.join(TEST_DATA_DIR, 'sample.png')
    out_path = validate_and_standardize_image(img_path, OUTPUT_DIR)
    assert os.path.exists(out_path)
    assert out_path.endswith('.png')

# Error handling tests
def test_convert_pdf_to_images_invalid():
    with pytest.raises(Exception):
        convert_pdf_to_images('not_a_pdf.txt', OUTPUT_DIR)

def test_validate_and_standardize_image_invalid():
    with pytest.raises(Exception):
        validate_and_standardize_image('not_an_image.txt', OUTPUT_DIR) 