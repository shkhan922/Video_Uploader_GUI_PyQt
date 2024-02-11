import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton,
    QWidget, QFrame, QSplitter, QFileDialog, QSpacerItem, QButtonGroup,
    QDialog, QHBoxLayout, QHeaderView, QSizePolicy, QLineEdit, QSpinBox
)
from PyQt5.QtGui import QPixmap, QIcon
from base64 import b64decode
from PyQt5.QtCore import pyqtSlot
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
                    jpg = bytes_data[a:b + 2]
                    bytes_data = bytes_data[b + 2:]
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

    def stop(self):
        self.terminate()
        self.wait()


class CustomHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super(CustomHeaderView, self).__init__(orientation, parent)
        self.setStyleSheet("""
            QHeaderView::section {
                background-color: #4F94CD;
                padding: 4px;
                border: 1px solid #6c6c6c;
                text-align: center;
            }
        """)


class UploadScreenPopup(QDialog):
    def __init__(self, parent=None):
        super(UploadScreenPopup, self).__init__(parent)
        self.setWindowTitle("Upload to Screen")
        self.setGeometry(300, 300, 800, 600)

        self.init_ui()

    def init_ui(self):
        label = QLabel("Select file to upload:")
        upload_button = QPushButton("Upload", self)
        upload_button.clicked.connect(self.upload_file)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(upload_button)

    def upload_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Select File to Upload', '', 'All Files (*)')
        print(f"File selected for upload: {file_path}")
        self.accept()


class SetupScreenPopup(QDialog):
    def __init__(self, parent=None, main_app=None):
        super(SetupScreenPopup, self).__init__(parent)
        self.setWindowTitle("Setup New Screen")
        self.setGeometry(300, 300, 800, 400)
        self.setStyleSheet("background-color: #28282B;")
        self.main_app = main_app  # Reference to the main application instance

        self.init_ui()

    def init_ui(self):
        label = QLabel("Enter setup information:")
        self.setup_input = QLineEdit(self)
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.submit_form)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.setup_input)
        layout.addWidget(submit_button)

    def submit_form(self):
        setup_info = self.setup_input.text()
        print(f"Setup information submitted: {setup_info}")

        # Extract information from the setup and create a new RemoteScreen instance
        name, url = setup_info.split(",")  # Assuming input format is "name,url"
        new_remote_screen = RemoteScreen(name, url)

        # Check if main_app is not None and has the add_remote_screen method
        if self.main_app and hasattr(self.main_app, 'add_remote_screen'):
            # Add the new remote screen to the main application
            self.main_app.add_remote_screen(new_remote_screen)
        else:
            print("Error: main_app does not have the add_remote_screen method.")

        self.accept()



# class RemoteScreen:
#     def __init__(self, name, url):
#         self.name = name
#         self.url = url
#         self.available = True  # Assume all screens are initially available
class RemoteScreen:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.available = True  # Assume all screens are initially available
        self.video_frame = None  # Reference to the associated VideoFrame
        self.video_frame_layout_index = -1  # Index in the video_frame_layout



class VideoFrame(QLabel):
    update_signal = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super(VideoFrame, self).__init__(parent)
        self.setFixedSize(400, 200)
        self.setAlignment(Qt.AlignCenter)
        self.active = False
        self.name_label = QLabel(self)
        self.url_label = QLabel(self)

         # Add labels for name and URL at the bottom
        self.name_label = QLabel(self)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.url_label = QLabel(self)
        self.url_label.setAlignment(Qt.AlignCenter)

        # Layout for labels at the bottom
        labels_layout = QVBoxLayout()
        labels_layout.addWidget(self.name_label)
        labels_layout.addWidget(self.url_label)

        # Main layout for the VideoFrame
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(labels_layout)
        main_layout.setAlignment(Qt.AlignBottom)
        main_layout.setContentsMargins(5, 5, 5, 5)

    def set_labels(self, name, url):
        self.name_label.setText(f"Name: {name}")
        self.url_label.setText(f"URL: {url}")

    def set_active(self, active):
        self.active = active
        self.setStyleSheet("border: 2px solid green;" if active else "")

    @pyqtSlot(QImage)
    def update_frame(self, image):
        self.setPixmap(QPixmap.fromImage(image))

        if self.active:
            self.name_label.show()
            self.url_label.show()
        else:
            self.name_label.hide()
            self.url_label.hide()


class FullscreenOptionsPopup(QDialog):
    def __init__(self, parent, current_num_frames):
        super(FullscreenOptionsPopup, self).__init__(parent)
        self.setWindowTitle("Fullscreen Options")
        self.setGeometry(300, 300, 400, 200)

        self.init_ui(current_num_frames)

    def init_ui(self, current_num_frames):
        label = QLabel("Select number of video frames:")
        self.num_frames_spinbox = QSpinBox(self)
        self.num_frames_spinbox.setMinimum(1)
        self.num_frames_spinbox.setMaximum(5)  # Adjust the maximum number as needed
        self.num_frames_spinbox.setValue(current_num_frames)

        confirm_button = QPushButton("Confirm", self)
        confirm_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.clicked.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.num_frames_spinbox)
        layout.addWidget(confirm_button)
        layout.addWidget(cancel_button)

    def get_selected_num_frames(self):
        return self.num_frames_spinbox.value()




class VehicleMonitoringApp(QMainWindow):
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

        self.right_panel_layout = QVBoxLayout(self.right_panel)
        self.right_panel_header = QLabel("Main", self.right_panel)
        self.right_panel_header.setStyleSheet("font-size: 20px; color: #4F94CD;")
        self.right_panel_header.setAlignment(Qt.AlignCenter)
        self.right_panel_layout.addWidget(self.right_panel_header, alignment=Qt.AlignTop)


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
        self.btn_setup.clicked.connect(self.setup_setup_screen)

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

        self.left_panel_layout.addWidget(self.btn_setup)
        self.left_panel_layout.addWidget(self.btn_fullscreen)
        self.left_panel_layout.addWidget(self.btn_upload)

        self.left_panel_layout.addItem(spacer)

        self.btn_main = QPushButton("Main", self.left_panel)
        self.btn_main.setStyleSheet("background-color: #4F94CD; color: white;")
        self.btn_main.clicked.connect(lambda: self.show_content(self.setup_main_screen))

        self.btn_error = QPushButton("Error Report", self.left_panel)
        self.btn_error.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_error.clicked.connect(lambda: self.show_content(self.setup_error_report))

        self.btn_members = QPushButton("Members List", self.left_panel)
        self.btn_members.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_members.clicked.connect(lambda: self.show_content(self.setup_members_list))

        self.left_panel_layout.addWidget(self.btn_main)
        self.left_panel_layout.addWidget(self.btn_error)
        self.left_panel_layout.addWidget(self.btn_members)

        self.tab_main = QWidget()
        self.tab_error = QWidget()
        self.tab_members = QWidget()

        self.upload_button = QPushButton("Upload MP4", self.tab_main)
        self.upload_button.clicked.connect(self.upload_mp4)
        self.preview_button = QPushButton("Preview", self.tab_main)
        self.preview_button.clicked.connect(self.preview)

        self.tab_main_layout = QVBoxLayout(self.tab_main)
        self.tab_main_layout.addWidget(self.upload_button)
        self.tab_main_layout.addWidget(self.preview_button)

        self.footer = QLabel("© 2024 SPONSOR SALES", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color:white")
        self.main_layout.addWidget(self.footer)

        # self.timer = QTimer(self)
        # # self.timer.timeout.connect(self.update_active_video_frame)
        # self.timer.start(1000)
        # Initialize video_frames attribute
        # self.video_frames = []  # Add this line to initialize the attribute

        # self.active_video_frame = None

        # self.remote_screens = []  # Initialize an empty list for remote screens
        # self.current_remote_screen = None


        # self.video_frames = [VideoFrame(self.right_panel)] 
        self.video_frames = []  # Initialize with one video frame

        # Add the following lines to initialize video_frame_layout
        self.video_frame_layout = QHBoxLayout(self.right_panel)
        self.video_frame_layout.setSpacing(0)

        # self.active_video_frame = self.video_frames[0]
        # self.active_video_frame.set_active(True)

        # self.remote_screens = [RemoteScreen("Default Screen", 'http://192.168.1.5:5000/video_feed')]
        # self.current_remote_screen = self.remote_screens[0]

        self.remote_screens = []

        self.stream_threads = [] 

        # Start streaming for the initial video frame
        self.start_streaming()

    # def add_remote_screen(self, remote_screen):
    #     # Add a new remote screen to the list
    #     self.remote_screens.append(remote_screen)

    #     # Create a new video frame for the remote screen
    #     video_frame = VideoFrame(self.right_panel)

    #     # Add the video frame to the layout
    #     self.video_frames.append(video_frame)
    #     self.video_frame_layout.addWidget(video_frame)

    #     # Start streaming for each video frame
    #     self.start_streaming()

    def add_remote_screen(self, remote_screen):
        # Add a new remote screen to the list
        self.remote_screens.append(remote_screen)

        # Create a new video frame for the remote screen
        video_frame = VideoFrame(self.right_panel)
        video_frame.name_label.setText(remote_screen.name)
        video_frame.url_label.setText(remote_screen.url)

       
         # Add the video frame to the layout
        self.video_frames.append(video_frame)
        layout_index = self.video_frame_layout.indexOf(video_frame)
        remote_screen.video_frame = video_frame
        remote_screen.video_frame_layout_index = layout_index

        # Add the video frame to the layout in the right panel
        self.video_frame_layout.insertWidget(layout_index, video_frame)

        # Set labels for the video frame
        video_frame.set_labels(remote_screen.name, remote_screen.url)

        # Start streaming for each video frame
        self.start_streaming()

    def show_fullscreen_options(self):
        if hasattr(self, 'video_frames'):
            options_popup = FullscreenOptionsPopup(self, len(self.video_frames))
            result = options_popup.exec_()
            if result == QDialog.Accepted:
                num_frames = options_popup.get_selected_num_frames()

                # Clear existing video frames and layout
                self.clear_video_frames()

                # Create new video frames and layout
                self.video_frames = [VideoFrame(self.right_panel) for _ in range(num_frames)]
                self.video_frame_layout = QHBoxLayout(self.right_panel)
                for video_frame in self.video_frames:
                    self.video_frame_layout.addWidget(video_frame)

                # Start streaming for each video frame
                self.start_streaming()

                # Update active video frame
                self.active_video_frame = self.video_frames[0]
                self.active_video_frame.set_active(True)
            else:
                print("Fullscreen options canceled")
        else:
            print("Please create video frames first.")

   
    def start_streaming(self):
        if hasattr(self, 'remote_screens'):
            for remote_screen in self.remote_screens:
                video_frame = remote_screen.video_frame
                if video_frame:
                    stream_thread = StreamThread(remote_screen.url)
                    stream_thread.update_frame_signal.connect(video_frame.update_frame)
                    stream_thread.start()
                    self.stream_threads.append(stream_thread)

    def clear_video_frames(self):
        for stream_thread in self.stream_threads:
            stream_thread.stop()

        for video_frame in self.video_frames:
            video_frame.setParent(None)
            video_frame.deleteLater()
            # Remove the video frame from the layout
            self.video_frame_layout.removeWidget(video_frame)

        self.stream_threads = []  # Clear the list

    def setup_upload_screen(self):
        upload_popup = UploadScreenPopup(self)
        result = upload_popup.exec_()
        if result == QDialog.Accepted:
            print("Upload to Screen popup accepted")
        else:
            print("Upload to Screen popup canceled")

    def setup_setup_screen(self):
        setup_popup = SetupScreenPopup(self, main_app=self)
        result = setup_popup.exec_()
        if result == QDialog.Accepted:
            print("Setup New Screen popup accepted")
        else:
            print("Setup New Screen popup canceled")


    def setup_main_screen(self):
        self.right_panel_layout.setCurrentIndex(0)
        self.update_active_button(self.btn_main)

    def setup_error_report(self):
        self.right_panel_layout.setCurrentIndex(1)
        self.update_active_button(self.btn_error)

    def setup_members_list(self):
        self.right_panel_layout.setCurrentIndex(2)
        self.update_active_button(self.btn_members)

    def show_content(self, content_setup_method):
        self.clear_video_frames()
        content_setup_method()

    def update_active_button(self, active_button):
        for button in self.button_group.buttons():
            button.setStyleSheet("background-color: #28282B; color: white;")
        active_button.setStyleSheet("background-color: #4F94CD; color: white;")

    
    @pyqtSlot(QImage)
    def update_video_feed(self, image):
        if self.active_video_frame:
            self.active_video_frame.update_frame(image)

    @pyqtSlot(QImage)
    def update_all_video_frames(self, image):
        for video_frame in self.video_frames:
            video_frame.setPixmap(QPixmap.fromImage(image))

    def upload_mp4(self):
        file_dialog = QFileDialog()
        mp4_path, _ = file_dialog.getOpenFileName(self, 'Select MP4 File', '', 'MP4 Files (*.mp4)')
        if mp4_path:
            files = {'file': open(mp4_path, 'rb')}
            response = requests.post('http://192.168.1.5:5000/upload_mp4', files=files)
            print(response.text)

    def preview(self):
        print("Preview clicked")
        if hasattr(self, 'video_frames'):
            for idx, video_frame in enumerate(self.video_frames):
                stream_thread = StreamThread('http://192.168.1.5:5000/video_feed')
                stream_thread.update_frame_signal.connect(lambda image, frame=video_frame: self.update_video_feed(image, frame))
                stream_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VehicleMonitoringApp()
    ex.show()
    sys.exit(app.exec_())
