import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton, QWidget, QFrame, QSplitter, QTreeView, QMenu, QHeaderView, QMessageBox, QFileDialog,QHBoxLayout,QToolButton, QSizePolicy,QSpacerItem,QButtonGroup
from PyQt5.QtGui import QPixmap, QIcon
from base64 import b64decode
from PyQt5.QtCore import pyqtSlot, QSortFilterProxyModel
import requests
import cv2
import numpy as np


class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage)  # Signal for updating video frame

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

class VideoFrame(QLabel):
    def __init__(self, parent=None):
        super(VideoFrame, self).__init__(parent)
        self.setFixedSize(500, 400)
        self.setAlignment(Qt.AlignCenter)
        self.active = False

    def set_active(self, active):
        self.active = active
        self.setStyleSheet("border: 2px solid red;" if active else "")

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
        self.header.setFixedHeight(90)
        self.header_layout = QHBoxLayout(self.header)
        self.header.setStyleSheet("background-color: #28282B;")
        self.main_layout.addWidget(self.header)

        # Create and set up header_title
        self.header_title = QLabel("Default Title", self.header)
        self.header_layout.addWidget(self.header_title)

        # Logo
        logo_pixmap = QPixmap("./logo.png").scaled(350, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label = QLabel(self.header)
        self.logo_label.setPixmap(logo_pixmap)
        self.header_layout.addWidget(self.logo_label)

        self.header_layout.addStretch()

        # Left and right panels #E5E5E5
        self.left_panel = QFrame(self)
       
        self.left_panel.setStyleSheet("background-color: #28282B;")
         # Right panel
        self.right_panel = QFrame(self)
        self.right_panel.setStyleSheet("background-color: white;")

        # Splitter for left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])
        self.main_layout.addWidget(self.splitter)

        # Right panel layout
        self.right_panel_layout = QVBoxLayout(self.right_panel)
        # Initialize content
        self.current_content_function = None
        self.setup_main_screen()  # Set default content

        # Left panel buttons and tabs
        self.left_panel_layout = QVBoxLayout(self.left_panel)
        self.right_panel_layout = QVBoxLayout(self.right_panel)

# Button group to manage button clicks
        self.button_group = QButtonGroup()

# New buttons
        self.btn_setup = QPushButton("Setup New Screen", self.left_panel)
        self.btn_setup.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_setup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_setup.clicked.connect(lambda: self.update_right_panel("Setup New Screen"))
        # self.btn_upload.clicked.connect(lambda: self.update_right_panel("Upload to Screen"))

        self.btn_fullscreen = QPushButton("Full Screen", self.left_panel)
        self.btn_fullscreen.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_fullscreen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_fullscreen.clicked.connect(self.preview)

        self.btn_upload = QPushButton("Upload to Screen", self.left_panel)
        self.btn_upload.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_upload.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.btn_upload.clicked.connect(self.upload_mp4)
        self.btn_upload.clicked.connect(lambda: self.update_right_panel("Update to Screen"))

# Spacer for adjusting the spacing between buttons
        spacer = QSpacerItem(30, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

# Add new buttons and spacer to the left panel layout
        
        
        self.left_panel_layout.addWidget(self.btn_setup)
        self.left_panel_layout.addWidget(self.btn_fullscreen)

        self.left_panel_layout.addWidget(self.btn_upload)

# Set spacing between buttons
        # self.left_panel_layout.setSpacing(3)

        # self.btn_main = QToolButton(self.left_panel)
        # self.btn_main.setText("Main")
        # self.btn_main.setStyleSheet("background-color: #4F94CD; color: white;")
        # self.btn_main.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # # self.btn_main.clicked.connect(lambda: self.show_content(self.tab_main))
        # self.btn_main.clicked.connect(lambda: self.update_right_panel("Main"))

        self.btn_error = QToolButton(self.left_panel)
        self.btn_error.setText("Error Report")
        self.btn_error.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_error.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.btn_error.clicked.connect(lambda: self.show_content(self.tab_error))
        # self.btn_error.clicked.connect(lambda: self.update_right_panel("Error Report"))

        self.btn_members = QToolButton(self.left_panel)
        self.btn_members.setText("Members List")
        self.btn_members.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_members.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.btn_members.clicked.connect(lambda: self.show_content(self.tab_members))
        # self.btn_members.clicked.connect(lambda: self.update_right_panel("Members List"))

        self.btn_main = QPushButton("Main", self.left_panel)
        self.btn_main.clicked.connect(lambda: self.show_content(self.setup_main_screen))

        self.btn_fullscreen = QPushButton("Full Screen", self.left_panel)
        self.btn_fullscreen.clicked.connect(lambda: self.show_content(self.setup_full_screen))

        self.btn_upload = QPushButton("Upload to Screen", self.left_panel)
        self.btn_upload.clicked.connect(lambda: self.show_content(self.setup_upload_screen))


# Add buttons to the left panel layout
        self.left_panel_layout.addItem(spacer)
        self.left_panel_layout.addWidget(self.btn_main)
        self.left_panel_layout.addWidget(self.btn_error)
        self.left_panel_layout.addWidget(self.btn_members)



# Initialize the content widgets
        self.tab_main = QWidget()
        self.tab_error = QWidget()
        self.tab_members = QWidget()

# Add buttons to the Main tab
        self.upload_button = QPushButton("Upload MP4", self.tab_main)
        self.upload_button.clicked.connect(self.upload_mp4)
        self.preview_button = QPushButton("Preview", self.tab_main)
        self.preview_button.clicked.connect(self.preview)

        self.tab_main_layout = QVBoxLayout(self.tab_main)
        self.tab_main_layout.addWidget(self.upload_button)
        self.tab_main_layout.addWidget(self.preview_button)

        # Right panel video frames
        self.video_frame_1 = VideoFrame(self.right_panel)
        self.video_frame_2 = VideoFrame(self.right_panel)
        self.video_frames = [self.video_frame_1, self.video_frame_2]

          

    
        # Right panel video frames
        self.video_frame_1 = VideoFrame(self.right_panel)
        self.video_frame_2 = VideoFrame(self.right_panel)
        self.video_frames = [self.video_frame_1, self.video_frame_2]

        self.video_feed_layout = QHBoxLayout(self.right_panel)
        for video_frame in self.video_frames:
            self.video_feed_layout.addWidget(video_frame)

        # Footer
        self.footer = QLabel("© 2024 SPONSOR SALES", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color:white")
        self.main_layout.addWidget(self.footer)

        # # Add an export button to the UI
        # self.export_button = QPushButton('Preview Window', self.right_panel)
        # self.export_button.setStyleSheet("background-color: Green;")
        # self.export_button.clicked.connect(self.export_detections_to_excel)
        # self.video_feed_layout.addWidget(self.export_button)

        # Timer for periodically updating the active video frame
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_active_video_frame)
        self.timer.start(1000)  # Update every second

        # Set the initial active video frame
        self.active_video_frame = self.video_frame_1
        self.active_video_frame.set_active(True)
# Inside VehicleMonitoringApp class

    def show_content(self, content_function):
        # Call the content function to set up the right panel
        content_function()

    def setup_main_screen(self):
        self.clear_right_panel()

        # Add content for Main Screen
        label = QLabel("Main Screen Content", self.right_panel)
        layout = QVBoxLayout(self.right_panel)
        layout.addWidget(label)

        # Set the current content function
        self.current_content_function = self.setup_main_screen

    def setup_full_screen(self):
        self.clear_right_panel()

        # Add content for Full Screen
        label = QLabel("Full Screen Content", self.right_panel)
        layout = QVBoxLayout(self.right_panel)
        layout.addWidget(label)

        # Set the current content function
        self.current_content_function = self.setup_full_screen

    def setup_upload_screen(self):
        self.clear_right_panel()

        # Add content for Upload Screen
        upload_screen = QFrame(self.right_panel)
        upload_screen.setGeometry(100, 100, 800, 400)
        upload_screen.setStyleSheet("background-color: #ADD8E6;")

        label = QLabel("Upload Screen Content", upload_screen)
        layout = QVBoxLayout(upload_screen)
        layout.addWidget(label)

        self.right_panel_layout.addWidget(upload_screen)

        # Set the current content function
        self.current_content_function = self.setup_upload_screen

    def clear_right_panel(self):
        # Clear existing content in the right panel
        while self.right_panel_layout.count():
            item = self.right_panel_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def update_right_panel(self, button_text):
        # Set the header title
        self.header_title.setText(button_text)

        for i in reversed(range(self.right_panel_layout.count())):
            self.right_panel_layout.itemAt(i).widget().setParent(None)


        # Add new content based on the button clicked
        if button_text == "Main":
            self.setup_main_screen()
        elif button_text == "Full Screen":
            self.setup_full_screen()
        elif button_text == "Upload to Screen":
            self.setup_upload_screen()
        elif button_text == "Setup New Screen":
            self.setup_setup_screen()
        # Add more conditions for other button_text values


    def update_active_video_frame(self):
        # Update the active video frame and set the other frame as inactive
        for video_frame in self.video_frames:
            video_frame.set_active(video_frame == self.active_video_frame)

    def start_stream(self, video_frame_idx):
        self.active_video_frame = self.video_frames[video_frame_idx]
        self.active_video_frame.set_active(True)

    @pyqtSlot(QImage, int)
    def update_video_feed(self, image, video_frame_idx):
        video_frame = self.video_frames[video_frame_idx]
        video_frame.setPixmap(QPixmap.fromImage(image))

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
        # Set up the stream threads for each video frame
        self.stream_threads = [StreamThread('http://192.168.1.5:5000/video_feed') for _ in self.video_frames]
        for idx, stream_thread in enumerate(self.stream_threads):
            stream_thread.update_frame_signal.connect(lambda image, idx=idx: self.update_video_feed(image, idx))
            stream_thread.start()

    

# Run the application
app = QApplication(sys.argv)
ex = VehicleMonitoringApp()
ex.show()
sys.exit(app.exec_())