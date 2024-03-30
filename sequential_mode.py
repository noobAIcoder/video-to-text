import os
import base64
import openai
from utils import generate_description_sequential, create_composite_image, generate_sequences, confirm_sequences

def process_screenshots_sequential(screenshots_folder, prompt, sequence_length, overlap, detail_mode, progress_callback=None):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 100))

    image_files = [f for f in os.listdir(screenshots_folder) if f.endswith(".jpg") or f.endswith(".png")]
    descriptions = []

    sequences = generate_sequences(image_files, sequence_length, overlap)
    
    print("Querying AI with the following parameters:")
    print(f"Model: {model}")
    print(f"Max Tokens: {max_tokens}")
    print(f"Prompt: {prompt}")
    print(f"Detail Mode: {detail_mode}")
    print(f"Number of Sequences: {len(sequences)}")
    print("Messages: ")

    print("Generated sequences:")
    for i, sequence in enumerate(sequences, start=1):
        print(f"Sequence {i}: {', '.join(sequence)}")

    confirmed = confirm_sequences(sequences)

    if confirmed:
        print("Sequences approved. Sending to AI...")
        for i, sequence in enumerate(sequences, start=1):
            sequence_paths = [os.path.join(screenshots_folder, image_file) for image_file in sequence]
            composite_image_path = create_composite_image(sequence_paths)
            description = generate_description_sequential(openai, model, max_tokens, sequence_paths, prompt, detail_mode)
            descriptions.append({"Image": composite_image_path, "Description": description})
            if progress_callback:
                progress_callback(i, len(sequences))
        print("Sequences processed.")
    else:
        print("Sequences not approved. Aborting.")
        return []

    return descriptions
