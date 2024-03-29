import os
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QProgressBar, QMessageBox, QLabel, QSpinBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal
from video_processing import process_video
from screenshot_processing import process_screenshots

class VideoProcessingThread(QThread):
    processing_finished = pyqtSignal(str)

    def __init__(self, video_path, output_folder, sensitivity):
        super().__init__()
        self.video_path = video_path
        self.output_folder = output_folder
        self.sensitivity = sensitivity

    def run(self):
        output_folder = process_video(self.video_path, self.output_folder, self.sensitivity)
        self.processing_finished.emit(output_folder)

class ScreenshotProcessingThread(QThread):
    processing_finished = pyqtSignal(str)

    def __init__(self, screenshots_folder):
        super().__init__()
        self.screenshots_folder = screenshots_folder

    def run(self):
        excel_path = process_screenshots(self.screenshots_folder)
        self.processing_finished.emit(excel_path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Description Generator")
        self.setGeometry(100, 100, 600, 400)

        self.video_path = None
        self.scene_detection_destination_folder = None
        self.screenshots_source_folder = None

        self.config_file = "config.ini"
        self.load_config()

        self.select_video_button = QPushButton("Select Video")
        self.select_video_button.clicked.connect(self.select_video)

        self.video_label = QLabel("No video selected")

        self.select_scene_detection_destination_button = QPushButton("Select Scene Detection Destination Folder")
        self.select_scene_detection_destination_button.clicked.connect(self.select_scene_detection_destination_folder)

        self.scene_detection_destination_label = QLabel("No scene detection destination folder selected")

        self.select_screenshots_source_button = QPushButton("Select Screenshots Source Folder")
        self.select_screenshots_source_button.clicked.connect(self.select_screenshots_source_folder)

        self.screenshots_source_label = QLabel("No screenshots source folder selected")

        self.sensitivity_label = QLabel("Sensitivity:")
        self.sensitivity_spinbox = QSpinBox()
        self.sensitivity_spinbox.setMinimum(1)
        self.sensitivity_spinbox.setMaximum(100)
        self.sensitivity_spinbox.setValue(30)

        sensitivity_layout = QHBoxLayout()
        sensitivity_layout.addWidget(self.sensitivity_label)
        sensitivity_layout.addWidget(self.sensitivity_spinbox)

        self.run_video_button = QPushButton("Run Video Processing")
        self.run_video_button.clicked.connect(self.run_video_processing)
        self.run_video_button.setEnabled(False)

        self.run_screenshots_button = QPushButton("Run Screenshot Processing")
        self.run_screenshots_button.clicked.connect(self.run_screenshot_processing)
        self.run_screenshots_button.setEnabled(False)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.select_video_button)
        layout.addWidget(self.video_label)
        layout.addWidget(self.select_screenshots_source_button)
        layout.addWidget(self.screenshots_source_label)
        layout.addWidget(self.select_scene_detection_destination_button)
        layout.addWidget(self.scene_detection_destination_label)
        layout.addLayout(sensitivity_layout)
        layout.addWidget(self.run_video_button)
        layout.addWidget(self.run_screenshots_button)
        layout.addWidget(self.progress_bar)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.video_path = config.get("LastState", "VideoPath", fallback=None)
            self.scene_detection_destination_folder = config.get("LastState", "SceneDetectionDestinationFolder", fallback=None)
            self.screenshots_source_folder = config.get("LastState", "ScreenshotsSourceFolder", fallback=None)
        else:
            config["LastState"] = {
                "VideoPath": "",
                "SceneDetectionDestinationFolder": "",
                "ScreenshotsSourceFolder": ""
            }
            with open(self.config_file, "w") as f:
                config.write(f)

    def save_config(self):
        config = configparser.ConfigParser()
        config["LastState"] = {
            "VideoPath": self.video_path or "",
            "SceneDetectionDestinationFolder": self.scene_detection_destination_folder or "",
            "ScreenshotsSourceFolder": self.screenshots_source_folder or ""
        }
        with open(self.config_file, "w") as f:
            config.write(f)

    def closeEvent(self, event):
        self.save_config()
        event.accept()

    def select_video(self):
        video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov)")
        if video_path:
            self.video_path = video_path
            self.video_label.setText(f"Selected video: {video_path}")
            self.run_video_button.setEnabled(True)

    def select_screenshots_source_folder(self):
        screenshots_source_folder = QFileDialog.getExistingDirectory(self, "Select Screenshots Source Folder")
        if screenshots_source_folder:
            self.screenshots_source_folder = screenshots_source_folder
            self.screenshots_source_label.setText(f"Selected screenshots source folder: {screenshots_source_folder}")
            self.run_screenshots_button.setEnabled(True)

    def select_scene_detection_destination_folder(self):
        scene_detection_destination_folder = QFileDialog.getExistingDirectory(self, "Select Scene Detection Destination Folder")
        if scene_detection_destination_folder:
            self.scene_detection_destination_folder = scene_detection_destination_folder
            self.scene_detection_destination_label.setText(f"Selected scene detection destination folder: {scene_detection_destination_folder}")

    def run_video_processing(self):
        if self.video_path and self.scene_detection_destination_folder:
            sensitivity = self.sensitivity_spinbox.value()
            self.processing_thread = VideoProcessingThread(self.video_path, self.scene_detection_destination_folder, sensitivity)
            self.processing_thread.processing_finished.connect(self.video_processing_finished)
            self.processing_thread.start()
            self.progress_bar.setVisible(True)

    def run_screenshot_processing(self):
        if self.screenshots_source_folder:
            self.screenshot_processing_thread = ScreenshotProcessingThread(self.screenshots_source_folder)
            self.screenshot_processing_thread.processing_finished.connect(self.screenshot_processing_finished)
            self.screenshot_processing_thread.start()
            self.progress_bar.setVisible(True)

    def video_processing_finished(self, output_folder):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Processing Complete", f"Video processing finished. Keyframes saved in {output_folder}")

    def screenshot_processing_finished(self, excel_path):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Processing Complete", f"Screenshot processing finished. Descriptions saved in {excel_path}")