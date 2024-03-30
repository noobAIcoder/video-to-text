import os
from datetime import datetime
from PIL import Image
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer, QEventLoop


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


def generate_description_independent(client, model, max_tokens, image_path, prompt, detail_mode):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode("utf-8")

    messages = [
        {
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
        },
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )

    description = response.choices[0].message.content.strip()
    return description


def generate_description_sequential(client, model, max_tokens, sequence_paths, prompt, detail_mode):
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
            ],
        },
    ]

    for image_path in sequence_paths:
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

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )

    description = response.choices[0].message.content.strip()
    return description


def confirm_sequences(sequences):
    app = QApplication.instance()
    if app is None:
        raise RuntimeError("No QApplication instance found")

    def show_confirmation_dialog():
        message = "The following sequences will be sent to the AI:\n\n"
        for i, sequence in enumerate(sequences, start=1):
            message += f"Sequence {i}: {', '.join(sequence)}\n"
        message += "\nDo you want to proceed?"

        reply = QMessageBox.question(None, "Confirm Sequences", message, QMessageBox.Yes | QMessageBox.No)
        confirmation_result[0] = reply == QMessageBox.Yes
        event_loop.quit()

    confirmation_result = [False]
    event_loop = QEventLoop()
    QTimer.singleShot(0, show_confirmation_dialog)
    event_loop.exec_()

    return confirmation_result[0]