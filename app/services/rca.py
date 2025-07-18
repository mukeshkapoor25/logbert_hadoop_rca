# RCA logic
import os
import uuid
from app.utils.parser import parse_logs_and_generate_structured_files
from app.services.inference import detect_anomalies_and_explain

TEMP_LOG_DIR = "temp_logs"
os.makedirs(TEMP_LOG_DIR, exist_ok=True)

def run_rca_pipeline(log_text: str):
    temp_file_path = os.path.join(TEMP_LOG_DIR, f"log_{uuid.uuid4().hex}.log")
    
    # Save uploaded logs to temp file
    with open(temp_file_path, "w") as f:
        f.write(log_text)
    
    try:
        app_results = detect_anomalies_and_explain(temp_file_path)
    finally:
        os.remove(temp_file_path)

    return app_results