from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
import os
import shutil
from uuid import uuid4
from app.services.file_service import convert_pdf_to_images, validate_and_standardize_image
from app.services.llava_service import analyze_image_with_llava, LLaVAServiceError

router = APIRouter()

UPLOAD_DIR = "/tmp/sda_uploads"
PROCESSED_DIR = "/tmp/sda_processed"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
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

    # LLaVA visual analysis for each image
    results = []
    for img_path in image_paths:
        try:
            llava_result = analyze_image_with_llava(img_path)
            results.append({
                "image": os.path.basename(img_path),
                "llava_result": llava_result
            })
        except LLaVAServiceError as e:
            results.append({
                "image": os.path.basename(img_path),
                "error": str(e)
            })

    return JSONResponse({
        "filename": safe_name,
        "content_type": file.content_type,
        "status": "uploaded",
        "results": results
    })
