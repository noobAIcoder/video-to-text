import os
import base64
import openai
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

load_dotenv()

def process_screenshots(screenshots_folder, prompt, image_treatment_mode, sequence_length, overlap, detail_mode, progress_callback=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    max_tokens = os.getenv("OPENAI_MAX_TOKENS")
    
    if max_tokens is None:
        print("OPENAI_MAX_TOKENS environment variable is not set. Using default value of 100.")
        max_tokens = 100
    else:
        try:
            max_tokens = int(max_tokens)
        except ValueError:
            print("Invalid value for OPENAI_MAX_TOKENS. Using default value of 100.")
            max_tokens = 100

    image_files = [f for f in os.listdir(screenshots_folder) if f.endswith(".jpg") or f.endswith(".png")]
    descriptions = []

    if image_treatment_mode == "Independent":
        for i, image_file in enumerate(image_files, start=1):
            image_path = os.path.join(screenshots_folder, image_file)
            description = generate_description(openai, model, max_tokens, [image_path], prompt, detail_mode)
            descriptions.append({"Image": image_file, "Description": description[0]})
            if progress_callback:
                progress_callback(i, len(image_files))
    else:
        print("Generating sequences...")
        sequences = generate_sequences(image_files, sequence_length, overlap)
        print(f"Generated {len(sequences)} sequences.")
        
        print("Displaying confirmation dialog...")
        confirmed = confirm_sequences(sequences)
        print(f"User confirmation: {confirmed}")
        
        if confirmed:
            print("Sequential sending confirmed. Processing sequences...")
            for i, sequence in enumerate(sequences, start=1):
                print(f"Processing sequence {i}/{len(sequences)}...")
                sequence_paths = [os.path.join(screenshots_folder, image_file) for image_file in sequence]
                description = generate_description(openai, model, max_tokens, sequence_paths, prompt, detail_mode)
                composite_image_path = create_composite_image(sequence_paths)
                descriptions.append({"Image": composite_image_path, "Description": description})
                if progress_callback:
                    progress_callback(i, len(sequences))
            print("Sequential sending completed.")
        else:
            print("Sequential sending canceled.")
            return []

    return descriptions

