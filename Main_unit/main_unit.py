import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer,pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QWidget,
    QFrame,
    QSplitter,
    QTabWidget,
    QFileDialog,
    QHBoxLayout,
    QTabBar,
)
import requests
import cv2
import numpy as np

class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage, int)  # Signal for updating video frame

    def __init__(self, url, video_frame_idx, update_interval=100):
        super().__init__()
        self.url = url
        self.video_frame_idx = video_frame_idx
        self.update_interval = update_interval

    def run(self):
        with requests.get(self.url, stream=True) as r:
            bytes_data = bytes()
            while True:
                chunk = r.raw.read(1024)
                if not chunk:
                    break
                bytes_data += chunk
                # Process image
                a = bytes_data.find(b'\xff\xd8')  # Start of JPEG
                b = bytes_data.find(b'\xff\xd9', a)  # End of JPEG
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
                self.update_frame_signal.emit(qImg, self.video_frame_idx)
        except Exception as e:
            print(f"Error processing frame: {e}")

class VideoFrame(QLabel):
    def __init__(self, remote_client_name, parent=None):
        super(VideoFrame, self).__init__(parent)
        self.setFixedSize(320, 240)
        self.setAlignment(Qt.AlignCenter)
        self.active = False
        self.remote_client_name = remote_client_name
        self.setText(f"{self.remote_client_name}\n16:9")

    def set_active(self, active):
        self.active = active
        self.setStyleSheet("border: 2px solid red;" if active else "")

class TabWidget(QTabWidget):
    def __init__(self, parent=None):
        super(TabWidget, self).__init__(parent)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.currentChanged.connect(self.tab_changed)

    def close_tab(self, index):
        self.removeTab(index)

    def tab_changed(self, index):
        # Emit a signal to handle tab changes
        self.current_tab_changed.emit(index)

    # Define a custom signal for tab changes
    current_tab_changed = pyqtSignal(int)

class VehicleMonitoringApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Main widget and layout
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setSpacing(0)
        self.setWindowTitle('Video Uploader and Preview System')
        self.setGeometry(100, 100, 1366, 768)

        # Header (logo and icons)
        self.header = QFrame(self)
        self.header.setFixedHeight(50)
        self.header_layout = QHBoxLayout(self.header)
        self.header.setStyleSheet("background-color: black;")
        self.main_layout.addWidget(self.header)

        # Logo
        logo_pixmap = QPixmap("./logo.png").scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label = QLabel(self.header)
        self.logo_label.setPixmap(logo_pixmap)
        self.header_layout.addWidget(self.logo_label)

        self.header_layout.addStretch()

        # Left and right panels #E5E5E5
        self.left_panel = QFrame(self)
        self.right_panel = QFrame(self)
        self.left_panel.setStyleSheet("background-color: white;")
        self.right_panel.setStyleSheet("background-color: white;")

        # Tab widget for the left panel
        self.tab_widget = TabWidget(self.left_panel)
        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.left_panel_layout.addWidget(self.tab_widget)

        # Right panel video frames
        self.video_frame_1 = VideoFrame("Remote Unit 1", self.right_panel)
        self.video_frame_2 = VideoFrame("Remote Unit 2", self.right_panel)
        self.video_frames = [self.video_frame_1, self.video_frame_2]

        self.video_frame_layout = QVBoxLayout(self.right_panel)
        for video_frame in self.video_frames:
            self.video_frame_layout.addWidget(video_frame)

        # Footer
        self.footer = QLabel("© 2024 Video Uploader", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color: black; color: white;")
        self.main_layout.addWidget(self.footer)

        # Add an export button to the UI
        self.export_button = QPushButton('Preview Window', self.right_panel)
        self.export_button.setStyleSheet("background-color: Green;")
        self.export_button.clicked.connect(self.export_detections_to_excel)
        self.video_frame_layout.addWidget(self.export_button)

        # Timer for periodically updating the active video frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_active_video_frame)
        self.timer.start(1000)  # Update every second

        # Set up the initial tabs
        self.setup_tabs()

    def setup_tabs(self):
        # Add tabs for Main, Error Reports, and Members List
        self.tab_widget.addTab(QLabel("Main Content"), "Main")
        self.tab_widget.addTab(QLabel("Error Reports"), "Error Reports")
        self.tab_widget.addTab(QLabel("Members List"), "Members List")

        # Connect the custom signal to the tab_changed method
        self.tab_widget.current_tab_changed.connect(self.tab_changed)

    def tab_changed(self, index):
        # Handle tab changes here
        # For now, print the selected tab index
        print(f"Selected tab index: {index}")

    def update_active_video_frame(self):
        # Update the active video frame based on the selected tab
        current_index = self.tab_widget.currentIndex()
        if 0 <= current_index < len(self.video_frames):
            self.active_video_frame = self.video_frames[current_index]
            self.active_video_frame.set_active(True)

            # Start the stream for the selected video frame
            self.start_stream(current_index)

            # Set other frames as inactive
            for idx, video_frame in enumerate(self.video_frames):
                if idx != current_index:
                    video_frame.set_active(False)

    def start_stream(self, video_frame_idx):
        # Start the stream thread for the specified video frame
        stream_thread = StreamThread('http://192.168.1.3:5000/video_feed', video_frame_idx)
        stream_thread.update_frame_signal.connect(self.update_video_feed)
        stream_thread.start()

    @pyqtSlot(QImage, int)
    def update_video_feed(self, image, video_frame_idx):
        video_frame = self.video_frames[video_frame_idx]
        video_frame.setPixmap(QPixmap.fromImage(image))

    def upload_mp4(self):
        file_dialog = QFileDialog()
        mp4_path, _ = file_dialog.getOpenFileName(self, 'Select MP4 File', '', 'MP4 Files (*.mp4)')

        if mp4_path:
            files = {'file': open(mp4_path, 'rb')}
            response = requests.post('http://192.168.1.3:5000/upload_mp4', files=files)
            print(response.text)  # Print the response from the REMOTE unit

    def export_detections_to_excel(self):
        # Replace this with your export to Excel logic
        print("Export to Excel clicked")

# Run the application
app = QApplication(sys.argv)
ex = VehicleMonitoringApp()
ex.show()
sys.exit(app.exec_())
