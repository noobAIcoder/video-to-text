import os
import base64
import openai
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
from PyQt5.QtWidgets import QMessageBox, QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt

load_dotenv()

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

def generate_sequences(image_files, sequence_length, overlap):
    print("Entering generate_sequences function...")
    sequences = []
    num_images = len(image_files)
    print(f"Total number of images: {num_images}")
    i = 0
    while i < num_images:
        print(f"Current position: {i}")
        end = min(i + sequence_length, num_images)
        print(f"End index: {end}")
        sequence = image_files[i:end]
        print(f"Generated sequence: {sequence}")
        sequences.append(sequence)
        i += sequence_length - overlap
        print(f"New position after overlap: {i}")
    print("Exiting generate_sequences function.")
    return sequences


def confirm_sequences(sequences):
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    dialog = QDialog()
    dialog.setWindowTitle("Confirm Sequences")
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
    print(f"Dialog created with title: {dialog.windowTitle()}")

    layout = QVBoxLayout()
    print("Vertical layout created")

    message_label = QLabel("The following sequences will be sent to the AI:")
    layout.addWidget(message_label)
    print("Message label added to the layout")

    for i, sequence in enumerate(sequences, start=1):
        sequence_label = QLabel(f"Sequence {i}: {', '.join(sequence)}")
        layout.addWidget(sequence_label)
        print(f"Sequence {i} label added to the layout")

    confirmation_label = QLabel("Do you want to proceed?")
    layout.addWidget(confirmation_label)
    print("Confirmation label added to the layout")

    button_box = QHBoxLayout()
    print("Horizontal button box layout created")

    yes_button = QPushButton("Yes")
    yes_button.clicked.connect(dialog.accept)
    button_box.addWidget(yes_button)
    print("Yes button added to the button box layout")

    no_button = QPushButton("No")
    no_button.clicked.connect(dialog.reject)
    button_box.addWidget(no_button)
    print("No button added to the button box layout")

    layout.addLayout(button_box)
    print("Button box layout added to the main layout")

    dialog.setLayout(layout)
    print("Layout set for the dialog")


def generate_description(client, model, max_tokens, image_paths, prompt, detail_mode):
    messages = [{"role": "system", "content": "You are an AI assistant that describes images."}]

    messages.append({
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
        ],
    })

    for image_path in image_paths:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")

        messages[-1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}",
                "detail": detail_mode.lower()
            },
        })

    print("Querying AI with the following parameters:")
    print(f"Model: {model}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Prompt: {prompt}")
    print(f"Detail Mode: {detail_mode}")
    print(f"Number of Images: {len(image_paths)}")
    print("Messages:")
    for message in messages:
        if message["role"] == "user":
            print(f"  User:")
            for content in message["content"]:
                if content["type"] == "text":
                    print(f"    Text: {content['text']}")
                else:
                    print(f"    Image: {content['image_url']['url'][:50]}...")  # Print truncated image URL
        else:
            print(f"  {message['role'].capitalize()}: {message['content']}")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )

    description = response.choices[0].message.content.strip()
    return description