# utils.py
import os
from datetime import datetime
from PIL import Image

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

def calculate_token_cost(screenshots_folder, detail_mode, image_treatment_mode, sequence_length, overlap):
    if not screenshots_folder:
        return 0

    image_files = [f for f in os.listdir(screenshots_folder) if f.endswith(".jpg") or f.endswith(".png")]
    total_cost = 0

    if image_treatment_mode == "Independent":
        for image_file in image_files:
            image_path = os.path.join(screenshots_folder, image_file)
            with Image.open(image_path) as img:
                width, height = img.size
            if detail_mode == "Low":
                total_cost += 85
            else:
                scaled_width = min(width, 2048)
                scaled_height = min(height, 2048)
                aspect_ratio = width / height
                if width > height:
                    scaled_height = int(scaled_width / aspect_ratio)
                else:
                    scaled_width = int(scaled_height * aspect_ratio)
                num_tiles = (scaled_width // 512) * (scaled_height // 512)
                total_cost += 170 * num_tiles + 85
    else:
        sequence_length = max(1, sequence_length)  # Ensure sequence_length is at least 1
        overlap = min(overlap, sequence_length - 1)  # Ensure overlap is less than sequence_length
        num_messages = (len(image_files) - sequence_length) // (sequence_length - overlap) + 1
        for _ in range(num_messages):
            if detail_mode == "Low":
                total_cost += 85 * sequence_length
            else:
                total_cost += (170 * sequence_length + 85) * 4  # Assuming 4 tiles per image in high detail mode

    return total_cost