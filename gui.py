import os
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QPushButton, QVBoxLayout, QWidget, QProgressBar, QMessageBox, QLabel, QSpinBox, QHBoxLayout, QListWidget, QLineEdit, QTextEdit, QComboBox, QRadioButton
import pandas as pd
from datetime import datetime

# Video processing thread
from PyQt5.QtCore import QThread, pyqtSignal
from video_processing import process_video
from screenshot_processing import process_screenshots
from utils import calculate_token_cost

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
    processing_finished = pyqtSignal(list)
    progress_updated = pyqtSignal(int)

    def __init__(self, screenshots_folder, prompt):
        super().__init__()
        self.screenshots_folder = screenshots_folder
        self.prompt = prompt

    def run(self):
        def progress_callback(current, total):
            progress = int((current / total) * 100)
            self.progress_updated.emit(progress)

        descriptions = process_screenshots(self.screenshots_folder, self.prompt, progress_callback)
        self.processing_finished.emit(descriptions)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Description Generator")
        self.setGeometry(100, 100, 800, 1000)
        self.prompts_file = "prompts.ini"
        self.prompts_config = configparser.ConfigParser()

        self.video_path = None
        self.scene_detection_destination_folder = None
        self.screenshots_source_folder = None
        self.sensitivity = 30

        self.config_file = "config.ini"

        self.select_video_button = QPushButton("Select Video")
        self.select_video_button.clicked.connect(self.select_video)

        self.video_label = QLabel("No video selected")

        self.descriptions_text_edit = QTextEdit()
        self.descriptions_text_edit.setReadOnly(True)

        self.select_screenshots_source_button = QPushButton("Select Screenshots Source Folder")
        self.select_screenshots_source_button.clicked.connect(self.select_screenshots_source_folder)

        self.screenshots_source_label = QLabel("No screenshots source folder selected")

        self.select_scene_detection_destination_button = QPushButton("Select Scene Detection Destination Folder")
        self.select_scene_detection_destination_button.clicked.connect(self.select_scene_detection_destination_folder)

        self.scene_detection_destination_label = QLabel("No scene detection destination folder selected")

        self.sensitivity_label = QLabel("Sensitivity:")
        self.sensitivity_spinbox = QSpinBox()
        self.sensitivity_spinbox.setMinimum(1)
        self.sensitivity_spinbox.setMaximum(100)
        self.sensitivity_spinbox.setValue(30)
        self.sensitivity_spinbox.valueChanged.connect(self.update_sensitivity)

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
        self.progress_bar.setVisible(True)

        self.prompts_listbox = QListWidget()
        self.prompts_listbox.itemClicked.connect(self.select_prompt)
        
        self.prompt_edit = QLineEdit()
        
        self.save_prompt_button = QPushButton("Save Prompt")
        self.save_prompt_button.clicked.connect(self.save_prompt)
        
        self.delete_prompt_button = QPushButton("Delete Prompt")
        self.delete_prompt_button.clicked.connect(self.delete_prompt)

        self.image_treatment_label = QLabel("Image Treatment Mode:")
        self.image_treatment_combo = QComboBox()
        self.image_treatment_combo.addItems(["Independent", "Consequent"])
        self.image_treatment_combo.currentTextChanged.connect(self.update_image_treatment_mode)

        self.sequence_length_label = QLabel("Sequence Length:")
        self.sequence_length_spinbox = QSpinBox()
        self.sequence_length_spinbox.setMinimum(1)
        self.sequence_length_spinbox.setValue(5)
        self.sequence_length_spinbox.valueChanged.connect(self.update_sequence_length)

        self.overlap_label = QLabel("Overlap:")
        self.overlap_spinbox = QSpinBox()
        self.overlap_spinbox.setMinimum(0)
        self.overlap_spinbox.setValue(2)
        self.overlap_spinbox.valueChanged.connect(self.update_overlap)

        self.detail_mode_label = QLabel("Detail Mode:")
        self.detail_mode_combo = QComboBox()
        self.detail_mode_combo.addItems(["Low", "High", "Auto"])
        self.detail_mode_combo.currentTextChanged.connect(self.update_detail_mode)

        self.cost_label = QLabel("Estimated Token Cost: 0")

        layout = QVBoxLayout()
        layout.addWidget(self.select_video_button)
        layout.addWidget(self.video_label)
        layout.addWidget(self.select_scene_detection_destination_button)
        layout.addWidget(self.scene_detection_destination_label)
        layout.addLayout(sensitivity_layout)
        layout.addWidget(self.run_video_button)

        layout.addWidget(self.select_screenshots_source_button)
        layout.addWidget(self.screenshots_source_label)
        layout.addWidget(self.image_treatment_label)
        layout.addWidget(self.image_treatment_combo)
        layout.addWidget(self.sequence_length_label)
        layout.addWidget(self.sequence_length_spinbox)
        layout.addWidget(self.overlap_label)
        layout.addWidget(self.overlap_spinbox)
        layout.addWidget(self.detail_mode_label)
        layout.addWidget(self.detail_mode_combo)
        layout.addWidget(self.cost_label)
        layout.addWidget(self.prompts_listbox)
        layout.addWidget(self.prompt_edit)
        layout.addWidget(self.save_prompt_button)
        layout.addWidget(self.delete_prompt_button)
        layout.addWidget(self.run_screenshots_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.descriptions_text_edit)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.load_config()
        self.load_prompts()

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            self.video_path = config.get("LastState", "VideoPath", fallback=None)
            self.scene_detection_destination_folder = config.get("LastState", "SceneDetectionDestinationFolder", fallback=None)
            self.screenshots_source_folder = config.get("LastState", "ScreenshotsSourceFolder", fallback=None)
            self.sensitivity = config.getint("LastState", "Sensitivity", fallback=30)
            self.image_treatment_mode = config.get("LastState", "ImageTreatmentMode", fallback="Independent")
            self.sequence_length = config.getint("LastState", "SequenceLength", fallback=5)
            self.overlap = config.getint("LastState", "Overlap", fallback=2)
            self.detail_mode = config.get("LastState", "DetailMode", fallback="Auto")

            if self.video_path:
                self.video_label.setText(f"Selected video: {self.video_path}")
                self.run_video_button.setEnabled(True)
            if self.scene_detection_destination_folder:
                self.scene_detection_destination_label.setText(f"Selected scene detection destination folder: {self.scene_detection_destination_folder}")
            if self.screenshots_source_folder:
                self.screenshots_source_label.setText(f"Selected screenshots source folder: {self.screenshots_source_folder}")
                self.run_screenshots_button.setEnabled(True)
            self.sensitivity_spinbox.setValue(self.sensitivity)
        else:
            self.save_config()

    def save_config(self):
        config = configparser.ConfigParser()
        config["LastState"] = {
            "VideoPath": self.video_path or "",
            "SceneDetectionDestinationFolder": self.scene_detection_destination_folder or "",
            "ScreenshotsSourceFolder": self.screenshots_source_folder or "",
            "Sensitivity": str(self.sensitivity),
            "ImageTreatmentMode": (self.image_treatment_mode),
            "SequenceLength": str(self.sequence_length),
            "Overlap": str(self.overlap),
            "DetailMode": self.detail_mode
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
            self.save_config()
            self.update_cost_estimate()  

    def select_screenshots_source_folder(self):
        screenshots_source_folder = QFileDialog.getExistingDirectory(self, "Select Screenshots Source Folder")
        if screenshots_source_folder:
            self.screenshots_source_folder = screenshots_source_folder
            self.screenshots_source_label.setText(f"Selected screenshots source folder: {screenshots_source_folder}")
            self.run_screenshots_button.setEnabled(True)
            self.save_config()
            self.update_cost_estimate()  

    def select_scene_detection_destination_folder(self):
        scene_detection_destination_folder = QFileDialog.getExistingDirectory(self, "Select Scene Detection Destination Folder")
        if scene_detection_destination_folder:
            self.scene_detection_destination_folder = scene_detection_destination_folder
            self.scene_detection_destination_label.setText(f"Selected scene detection destination folder: {scene_detection_destination_folder}")
            self.save_config()

    def update_sensitivity(self, value):
        self.sensitivity = value
        self.save_config()

    def run_video_processing(self):
        if self.video_path and self.scene_detection_destination_folder:
            self.processing_thread = VideoProcessingThread(self.video_path, self.scene_detection_destination_folder, self.sensitivity)
            self.processing_thread.processing_finished.connect(self.video_processing_finished)
            self.processing_thread.start()
            self.progress_bar.setVisible(True)

    def run_screenshot_processing(self):
        if self.screenshots_source_folder:
            current_item = self.prompts_listbox.currentItem()
            if current_item:
                prompt = self.prompts_config.get("Prompts", current_item.text())
                self.screenshot_processing_thread = ScreenshotProcessingThread(self.screenshots_source_folder, prompt)
                self.screenshot_processing_thread.processing_finished.connect(self.screenshot_processing_finished)
                self.screenshot_processing_thread.progress_updated.connect(self.update_progress)
                self.screenshot_processing_thread.start()
                self.progress_bar.setVisible(True)
            else:
                QMessageBox.warning(self, "No Prompt Selected", "Please select a prompt from the list.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def screenshot_processing_finished(self, descriptions):
            self.progress_bar.setVisible(False)
            self.descriptions_text_edit.clear()
            for description in descriptions:
                self.descriptions_text_edit.append(f"Image: {description['Image']}")
                self.descriptions_text_edit.append(f"Description: {description['Description']}")
                self.descriptions_text_edit.append("---")
            
            excel_path = self.save_descriptions_to_excel(descriptions)
            QMessageBox.information(self, "Processing Complete", f"Screenshot processing finished. Descriptions saved in {excel_path}")

    def load_prompts(self):
        if not os.path.exists(self.prompts_file):
            self.prompts_config["Prompts"] = {}
            with open(self.prompts_file, "w") as f:
                self.prompts_config.write(f)
        else:
            self.prompts_config.read(self.prompts_file)
        self.prompts_listbox.clear()
        for prompt in self.prompts_config.options("Prompts"):
            self.prompts_listbox.addItem(prompt)
    
    def select_prompt(self, item):
        prompt = self.prompts_config.get("Prompts", item.text())
        self.prompt_edit.setText(prompt)
    
    def save_prompt(self):
        prompt_name = self.prompt_edit.text().split(".")[0]
        self.prompts_config.set("Prompts", prompt_name, self.prompt_edit.text())
        with open(self.prompts_file, "w") as f:
            self.prompts_config.write(f)
        self.load_prompts()
    
    def delete_prompt(self):
        current_item = self.prompts_listbox.currentItem()
        if current_item:
            self.prompts_config.remove_option("Prompts", current_item.text())
            with open(self.prompts_file, "w") as f:
                self.prompts_config.write(f)
            self.load_prompts()
    
    def video_processing_finished(self, output_folder):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Processing Complete", f"Video processing finished. Keyframes saved in {output_folder}")

    def save_descriptions_to_excel(self, descriptions):
        if self.screenshots_source_folder:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            excel_filename = f"descriptions_{timestamp}.xlsx"
            excel_path = os.path.join(self.screenshots_source_folder, excel_filename)
            df = pd.DataFrame(descriptions)
            df.to_excel(excel_path, index=False)
            return excel_path
        else:
            QMessageBox.warning(self, "No Screenshots Source Folder", "Please select a screenshots source folder.")
            return None

    def update_image_treatment_mode(self, mode):
        self.image_treatment_mode = mode
        self.sequence_length_label.setVisible(mode == "Consequent")
        self.sequence_length_spinbox.setVisible(mode == "Consequent")
        self.overlap_label.setVisible(mode == "Consequent")
        self.overlap_spinbox.setVisible(mode == "Consequent")
        self.save_config()
        self.update_cost_estimate()

    def update_sequence_length(self, value):
        self.sequence_length = value
        self.save_config()
        self.update_cost_estimate()

    def update_overlap(self, value):
        self.overlap = value
        self.save_config()
        self.update_cost_estimate()

    def update_detail_mode(self, mode):
        self.detail_mode = mode
        self.save_config()
        self.update_cost_estimate()

    def update_cost_estimate(self):
        cost = calculate_token_cost(self.screenshots_source_folder, self.detail_mode, self.image_treatment_mode, self.sequence_length, self.overlap)
        self.cost_label.setText(f"Estimated Token Cost: {cost}")