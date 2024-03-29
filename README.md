# Video to Text Description Generator

The Video to Text Description Generator is a Python application that automatically generates textual descriptions for videos. It utilizes scene detection techniques to extract keyframes from a video and employs the OpenAI API to generate descriptive text for each keyframe.

## Features

- Automatically detects scenes in a video and extracts keyframes
- Generates textual descriptions for each keyframe using the OpenAI API
- Provides a user-friendly graphical interface for easy interaction
- Allows adjusting the sensitivity threshold for scene detection
- Supports processing multiple videos and saving the results in an Excel file

## Installation

1. Clone the repository:

git clone https://github.com/noobAIcoder/video-to-text.git

2. Install the required dependencies:

pip install -r requirements.txt

3. Set up the necessary environment variables:
- Create a `.env` file in the project directory.
- Add the following variables to the `.env` file:
  ```
  OPENAI_API_KEY=your-api-key
  OPENAI_MODEL=gpt-4-vision-preview
  OPENAI_MAX_TOKENS=300
  ```
- Replace `your-api-key` with your actual OpenAI API key.

## Usage

1. Run the application:

python .\main.py

2. Use the graphical interface to select a video file and adjust the sensitivity threshold (higher = lower).

3. Click the "Run Video Processing" button to start the scene detection and keyframe extraction process.

4. Once the video processing is complete, select folder where screenshots were saved and click the "Run Screenshot Processing" button to generate textual descriptions for each keyframe.

5. The generated descriptions will be saved in an Excel file in the same directory as the selected screenshots folder.

## Contributing

Contributions are welcome! If you would like to contribute to this project, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

## Authors

- noobAIcoder - Prompting and copy-pasting
- Claude (Anthropic AI) - Advisory, code generation, debugging

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information