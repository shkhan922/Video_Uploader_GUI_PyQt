import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton,
    QWidget, QFrame, QSplitter, QFileDialog, QButtonGroup,
    QDialog, QVBoxLayout, QLineEdit, QSpinBox,QSizePolicy, QSpacerItem
)
import requests
import cv2
import numpy as np

class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage)

    def __init__(self, url, update_interval=100):
        super().__init__()
        self.url = url
        self.update_interval = update_interval

    def run(self):
        with requests.get(self.url, stream=True) as r:
            bytes_data = bytes()
            while True:
                chunk = r.raw.read(1024)
                if not chunk:
                    break
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9', a)
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    self.emit_frame(jpg)

    def emit_frame(self, jpg_data):
        try:
            frame = cv2.imdecode(np.frombuffer(jpg_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                height, width, channel = frame.shape
                bytesPerLine = 3 * width
                qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped()
                self.update_frame_signal.emit(qImg)
        except Exception as e:
            print(f"Error processing frame: {e}")

class VideoFrame(QLabel):
    def __init__(self, name, parent=None):
        super(VideoFrame, self).__init__(parent)
        self.setFixedSize(500, 400)
        self.setAlignment(Qt.AlignCenter)
        self.active = False
        self.name = name
        self.setStyleSheet("border: 2px solid red;")

    def set_active(self, active):
        self.active = active
        self.setStyleSheet("border: 2px solid red;" if active else "")

class SetupScreenPopup(QDialog):
    def __init__(self, parent=None):
        super(SetupScreenPopup, self).__init__(parent)
        self.setWindowTitle("Setup New Screen")
        self.setGeometry(300, 300, 400, 200)

        self.init_ui()

    def init_ui(self):
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Enter screen name")

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter stream URL")

        confirm_button = QPushButton("Confirm", self)
        confirm_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.name_input)
        layout.addWidget(self.url_input)
        layout.addWidget(confirm_button)
        layout.addWidget(cancel_button)

    def get_setup_info(self):
        name = self.name_input.text()
        url = self.url_input.text()
        return name, url

class VideoUploaderApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.setWindowTitle('Video Uploader and Preview System')
        self.setGeometry(100, 100, 1366, 768)

        self.header = QFrame(self)
        self.header.setFixedHeight(90)
        self.header_layout = QVBoxLayout(self.header)
        self.header.setStyleSheet("background-color: #28282B;")
        self.main_layout.addWidget(self.header)

        self.header_title = QLabel("Default Title", self.header)
        self.header_layout.addWidget(self.header_title)

        logo_pixmap = QPixmap("./logo.png").scaled(350, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label = QLabel(self.header)
        self.logo_label.setPixmap(logo_pixmap)
        self.header_layout.addWidget(self.logo_label)

        self.header_layout.addStretch()

        self.left_panel = QFrame(self)
        self.left_panel.setStyleSheet("background-color: #28282B;")

        self.right_panel = QFrame(self)
        self.right_panel.setStyleSheet("background-color: white;")

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
        self.main_layout.addWidget(self.splitter)

        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.button_group = QButtonGroup()

        self.btn_setup = QPushButton("Setup New Screen", self.left_panel)
        self.btn_setup.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_setup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_setup.clicked.connect(self.show_setup_screen)

        self.btn_fullscreen = QPushButton("Full Screen", self.left_panel)
        self.btn_fullscreen.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_fullscreen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_fullscreen.clicked.connect(self.show_fullscreen_options)

        self.left_panel_layout.addWidget(self.btn_fullscreen)

        self.btn_upload = QPushButton("Upload to Screen", self.left_panel)
        self.btn_upload.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_upload.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_upload.clicked.connect(self.setup_upload_screen)

        spacer = QSpacerItem(30, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.left_panel_layout.addWidget(self.btn_fullscreen)
        self.left_panel_layout.addWidget(self.btn_upload)

        self.left_panel_layout.addItem(spacer)

        self.video_frames = []  # Initialize an empty list of video frames
        self.video_frame_layout = QVBoxLayout(self.right_panel)  # Initialize video frame layout

        self.footer = QLabel("© 2024 SPONSOR SALES", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color:white")
        self.main_layout.addWidget(self.footer)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_active_video_frame)
        self.timer.start(1000)

    def show_fullscreen_options(self):
        if hasattr(self, 'video_frames'):
            options_popup = FullscreenOptionsPopup(self, len(self.video_frames))
            result = options_popup.exec_()
            if result == QDialog.Accepted:
                num_frames = options_popup.get_selected_num_frames()

                # Clear existing video frames and layout
                self.clear_video_frames()

                # Create new video frames and layout
                self.video_frames = [VideoFrame(f"Remote Screen {i + 1}") for i in range(num_frames)]
                for video_frame in self.video_frames:
                    self.video_frame_layout.addWidget(video_frame)

                # Start streaming for each video frame
                self.start_streaming()
            else:
                print("Please create video frames first.")

    def setup_setup_screen(self):
        setup_popup = SetupScreenPopup(self)
        result = setup_popup.exec_()
        if result == QDialog.Accepted:
            # Get the setup information from the setup form
            name, url = setup_popup.get_setup_info()

            # Create a new video frame and start streaming for the entered setup information
            video_frame = VideoFrame(name)
            self.video_frames.append(video_frame)
            self.video_frame_layout.addWidget(video_frame)

            stream_thread = StreamThread(url)
            stream_thread.update_frame_signal.connect(lambda image, frame=video_frame: self.update_video_feed(image, frame))
            stream_thread.start()

        else:
            print("Setup New Screen popup canceled")

    def start_streaming(self):
        if hasattr(self, 'video_frames'):
            for idx, video_frame in enumerate(self.video_frames):
                # Assume you have the stream URL for each video frame
                # Modify this part according to your needs
                stream_url = f"http://example.com/stream/{idx + 1}"
                stream_thread = StreamThread(stream_url)
                stream_thread.update_frame_signal.connect(lambda image, idx=idx: self.update_video_feed(image, idx))
                stream_thread.start()


    def show_setup_screen(self, default_name):
        setup_popup = SetupScreenPopup(self)
        setup_popup.name_input.setText(default_name)
        result = setup_popup.exec_()
        if result == QDialog.Accepted:
            setup_info = setup_popup.get_setup_info()
            return setup_info
        return None

    def update_active_video_frame(self):
        for video_frame in self.video_frames:
            video_frame.set_active(video_frame == self.active_video_frame)

    def update_video_feed(self, image, video_frame_idx):
        video_frame = self.video_frames[video_frame_idx]
        video_frame.setPixmap(QPixmap.fromImage(image))

    def setup_upload_screen(self):
        # Modify this method according to your needs
        pass

app = QApplication(sys.argv)
ex = VideoUploaderApp()
ex.show()
sys.exit(app.exec_())
