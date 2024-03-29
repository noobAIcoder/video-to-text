# utils.py
import os
from datetime import datetime

def create_output_folder(video_path):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"{video_name}_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    return output_folder

def calculate_progress(current, total):
    if total == 0:
        return 0
    return (current / total) * 100