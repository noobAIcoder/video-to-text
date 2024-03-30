import os
import openai
from utils import generate_description_independent

def process_screenshots_independent(screenshots_folder, prompt, detail_mode, progress_callback=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 100))

    image_files = [f for f in os.listdir(screenshots_folder) if f.endswith(".jpg") or f.endswith(".png")]
    descriptions = []

    print("Querying AI with the following parameters:")
    print(f"Model: {model}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Prompt: {prompt}")
    print(f"Detail Mode: {detail_mode}")
    print(f"Number of Images: {len(image_files)}")
    print("Messages:")

    for i, image_file in enumerate(image_files, start=1):
        image_path = os.path.join(screenshots_folder, image_file)
        description = generate_description_independent(openai, model, max_tokens, image_path, prompt, detail_mode)
        descriptions.append({"Image": image_file, "Description": description})
        if progress_callback:
            progress_callback(i, len(image_files))

    return descriptions