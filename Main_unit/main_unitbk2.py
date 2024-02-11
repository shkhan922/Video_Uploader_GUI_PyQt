import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QFrame, QSplitter, QTreeView, QMenu, QHeaderView, QMessageBox,QFileDialog
from PyQt5.QtGui import QPixmap, QIcon
from base64 import b64decode
from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel
import requests
import cv2
import numpy as np

class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage)  # Signal for updating video frame

    def __init__(self, url):
        super().__init__()
        self.url = url

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
                self.update_frame_signal.emit(qImg)
        except Exception as e:
            print(f"Error processing frame: {e}")

class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super(CustomHeaderView, self).__init__(orientation, parent)
        self.setStyleSheet("""
            QHeaderView::section {
                background-color: #4F94CD; /* Change to your desired color */
                padding: 4px;
                border: 1px solid #6c6c6c;
                text-align: center;
            }
        """)

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

        # Header 4F94CD
        self.header = QFrame(self)
        self.header.setFixedHeight(50)
        self.header.setStyleSheet("background-color: black;")
        # Logo
        logo_label = QLabel(self.header)
        logo_pixmap = QPixmap('Main_unit/logo.png')  # Replace with the path to your logo image
        logo_label.setPixmap(logo_pixmap.scaledToHeight(60, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.main_layout.addWidget(self.header)

        # Left and right panels #E5E5E5
        self.left_panel = QFrame(self)
        self.right_panel = QFrame(self)
        self.left_panel.setStyleSheet("background-color: white;")
        self.right_panel.setStyleSheet("background-color: white;")

        # Splitter for left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
        self.main_layout.addWidget(self.splitter)

        # Left panel buttons
        self.upload_button = QPushButton("Upload MP4", self.left_panel)
        self.upload_button.clicked.connect(self.upload_mp4)
        self.preview_button = QPushButton("Preview", self.left_panel)
        self.preview_button.clicked.connect(self.preview)
        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.left_panel_layout.addWidget(self.upload_button)
        self.left_panel_layout.addWidget(self.preview_button)

        # Right panel video frame
        self.video_feed_label = QLabel(self.right_panel)
        self.video_feed_label.setAlignment(Qt.AlignCenter)
        self.video_feed_layout = QVBoxLayout(self.right_panel)
        self.video_feed_layout.addWidget(self.video_feed_label)

        # Set up the stream thread
       

        # Footer
        self.footer = QLabel("© 2024 Video Uploader", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color: #4F94CD; color: white;")
        self.main_layout.addWidget(self.footer)

        # Add an export button to the UI
        self.export_button = QPushButton('Preview Window', self.right_panel)
        self.export_button.setStyleSheet("background-color: Green;")
        self.export_button.clicked.connect(self.export_detections_to_excel)
        self.video_feed_layout.addWidget(self.export_button)

    def start_stream(self):
        self.stream_thread = StreamThread('http://192.168.1.5:5000/video_feed')
        self.stream_thread.update_frame_signal.connect(self.update_video_feed)
        self.stream_thread.start()

    @pyqtSlot(QImage)
    def update_video_feed(self, image):
        self.video_feed_label.setPixmap(QPixmap.fromImage(image))

    def upload_mp4(self):
        file_dialog = QFileDialog()
        mp4_path, _ = file_dialog.getOpenFileName(self, 'Select MP4 File', '', 'MP4 Files (*.mp4)')

        if mp4_path:
            files = {'file': open(mp4_path, 'rb')}
            response = requests.post('http://192.168.1.5:5000/upload_mp4', files=files)
            print(response.text)  # Print the response from the REMOTE unit

    def preview(self):
        # Replace this with your preview logic
        print("Preview clicked")
        self.start_stream()

    def export_detections_to_excel(self):
        # Replace this with your export to Excel logic
        print("Export to Excel clicked")

# Run the application
app = QApplication(sys.argv)
ex = VehicleMonitoringApp()
ex.show()
sys.exit(app.exec_())
