import os
import base64
import openai
import pandas as pd
from dotenv import load_dotenv
from PIL import Image

load_dotenv()


def generate_description(client, model, max_tokens, image_paths, prompt, detail_mode):
    messages = [{"role": "system", "content": "You are an AI assistant that describes images."}]

    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                        "detail": detail_mode.lower()
                    },
                },
            ],
        })

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )

    description = response.choices[0].message.content.strip()

    if len(image_paths) > 1:
        composite_image_path = create_composite_image(image_paths)
    else:
        composite_image_path = image_paths[0]

    return description, composite_image_path


def create_composite_image(image_paths):
    images = [Image.open(image_path) for image_path in image_paths]
    widths, heights = zip(*(i.size for i in images))

    max_width = max(widths)
    total_height = sum(heights)

    composite_image = Image.new("RGB", (max_width, total_height))

    y_offset = 0
    for image in images:
        composite_image.paste(image, (0, y_offset))
        y_offset += image.size[1]

    composite_image_path = "composite_image.jpg"
    composite_image.save(composite_image_path)

    return composite_image_path


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
            descriptions.append({"Image": image_file, "Description": description})
            if progress_callback:
                progress_callback(i, len(image_files))
    else:
        for i in range(0, len(image_files), sequence_length - overlap):
            sequence = image_files[i:i+sequence_length]
            sequence_paths = [os.path.join(screenshots_folder, image_file) for image_file in sequence]
            description, composite_image_path = generate_description(openai, model, max_tokens, sequence_paths, prompt, detail_mode)
            descriptions.append({"Image": composite_image_path, "Description": description})
            if progress_callback:
                progress_callback(i + len(sequence), len(image_files))

    return descriptions
