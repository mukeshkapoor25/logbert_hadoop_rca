import sys
import os
# Add the parent directory to sys.path so 'scripts' can be imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import shutil
from fastapi import UploadFile
from scripts.logbert_rca_pipeline_api import detect_anomalies_and_explain

INPUT_LOG_PATH = os.path.join("AI_MODELS", "datasets", "Hadoop", "rca_abnormal_hadoop.log")

def save_uploaded_log(uploaded_file: UploadFile):
    """
    Save the uploaded log file to the RCA input path.
    """
    with open(INPUT_LOG_PATH, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)
    uploaded_file.file.close()

def run_rca_on_uploaded_log(uploaded_file: UploadFile):
    """
    Save the uploaded log file and run RCA pipeline on it.
    """
    save_uploaded_log(uploaded_file)
    result = detect_anomalies_and_explain(INPUT_LOG_PATH)
    return {
        "status": "RCA completed successfully.",
        "details": result  # result should be list of RCA reports or messages
    }
