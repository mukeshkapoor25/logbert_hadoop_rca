# from fastapi import APIRouter
# router = APIRouter()
from fastapi import APIRouter, UploadFile, File
from app.services.inference import run_rca_on_uploaded_log

router = APIRouter()

@router.post("/upload-log/")
async def upload_log(file: UploadFile = File(...)):
    result = run_rca_on_uploaded_log(file)
    return result