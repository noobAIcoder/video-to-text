# screenshot_processing.py
import os
import base64
import openai
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def generate_description(client, model, max_tokens, image_path, prompt):
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": image_base64},
                    ],
                }
            ],
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating description: {str(e)}")
        return ""


def process_screenshots(screenshots_folder, prompt, progress_callback=None):
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

    for i, image_file in enumerate(image_files, start=1):
        image_path = os.path.join(screenshots_folder, image_file)
        description = generate_description(openai, model, max_tokens, image_path, prompt)
        descriptions.append({"Image": image_file, "Description": description})
        
        if progress_callback:
            progress_callback(i, len(image_files))

    return descriptions