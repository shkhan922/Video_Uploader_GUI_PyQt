import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton,
    QWidget, QFrame, QSplitter, QFileDialog, QSpacerItem, QButtonGroup,
    QDialog,QHBoxLayout,QHeaderView,QSizePolicy,QLineEdit, QSpinBox,QGridLayout,QToolButton
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import   QFormLayout, QDateEdit, QSpinBox
from PyQt5.QtGui import QPalette, QColor
from base64 import b64decode
from PyQt5.QtCore import pyqtSlot
import requests
import cv2
import numpy as np
import pickle

class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage)

    def __init__(self, url, update_interval=100):
        super().__init__()
        self.url = url
        self.update_interval = update_interval
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        with requests.get(self.url, stream=True) as r:
            bytes_data = bytes()
            while not self.stopped:
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


# class VideoFrameWidget(QLabel):

#     deleteRequested = pyqtSignal(QWidget)
#     streamStateChanged = pyqtSignal(bool, str)  # Signal for stream state change (on/off)

#     def __init__(self, url, parent=None):
#         super(VideoFrameWidget, self).__init__(parent)
#         self.setFixedSize(400, 400)
#         self.setAlignment(Qt.AlignCenter)
#         self.active = False  # Set initially to False
#         self.url = url
#         self.size_label = QLabel(f"Size: {self.width()} x {self.height()}", self)  # Corrected
#         self.url_label = QLabel(f"Stream URL: {self.url}", self)  # Corrected
#         self.setup_ui()

#     def to_dict(self):
#         return {
#             'stream_url': self.url,
#             'active': self.active
#         }

#     def setup_ui(self):
#     # Create a main layout for the VideoFrame
#         main_layout = QVBoxLayout(self)
#         main_layout.setAlignment(Qt.AlignBottom)

#     # Create a widget to hold the static labels and button
#         info_widget = QWidget(self)

#     # Create info_layout here
#         info_layout = QVBoxLayout(info_widget)

#     # Add a delete button to the widget
#         delete_button = QToolButton(self)
#         delete_button.setIcon(QIcon("delete_icon.png"))  # Replace with the actual path to your delete icon
#         delete_button.clicked.connect(self.handle_delete_request)

#     # Add the delete button to the layout
#         info_layout.addWidget(delete_button)

#     # Button to toggle stream on/off
#         self.stream_button = QPushButton("Toggle Stream", info_widget)
#         self.stream_button.clicked.connect(self.toggle_stream)

#     # Add labels and button to the widget's layout
#         self.size_label = QLabel(f"Size: {self.width()} x {self.height()}", info_widget)
#         self.url_label = QLabel(f"Stream URL: {self.url}", info_widget)
#         info_layout.addWidget(self.size_label)
#         info_layout.addWidget(self.url_label)
#         info_layout.addWidget(self.stream_button)
#         info_layout.addStretch()

#     # # Indicator label for stream status
#     #     self.status_indicator = QLabel("Stream Not Started", self)
#     #     self.status_indicator.setAlignment(Qt.AlignCenter)
#     #     self.status_indicator.setStyleSheet("background-color: #e0e0e0;")
#     #     self.status_indicator.setGeometry(0, 0, self.width(), self.height())
#     #     self.status_indicator.show()

#     # Border styling
#         self.setStyleSheet("border: 2px solid red;")

#     # Add the info widget to the main layout
#         main_layout.addWidget(info_widget)

#     def toggle_stream(self):
#     # Implement the logic to start/stop the stream based on the button click
#         self.active = not self.active

#     # Toggle button text
#         self.stream_button.setText("Toggle Stream (On)" if self.active else "Toggle Stream (Off)")

#     # Always show labels
#         self.show_labels()

#         if self.active:
#         # Start stream
#             self.streamStateChanged.emit(True, self.url)
#             self.status_indicator.setText("Stream Started")
#         else:
#         # Stop stream
#             self.streamStateChanged.emit(False, self.url)
#             self.status_indicator.setText("Stream Stopped")

#         self.set_active(self.active)  # Call set_active to update the appearance

#     def show_labels(self):
#         self.size_label.show()
#         self.url_label.show()
#         self.stream_button.show()


#     def set_active(self, active):
#         self.active = active
#         self.setStyleSheet("border: 2px solid green;" if active else "")
#         if active:
#             self.hide_status_indicator()
#         else:
#             self.show_status_indicator()

#     def show_status_indicator(self):
#         self.status_indicator.show()

#     def hide_status_indicator(self):
#         self.status_indicator.hide()

#     def handle_delete_request(self):
#         # Emit the deleteRequested signal when the delete button is clicked
#         self.deleteRequested.emit(self)


class VideoFrameWidget(QLabel):
    deleteRequested = pyqtSignal(QWidget)
    streamStateChanged = pyqtSignal(bool, str)  # Signal for stream state change (on/off)

    def __init__(self, url, parent=None):
        super(VideoFrameWidget, self).__init__(parent)
        self.setFixedSize(400, 400)
        self.setAlignment(Qt.AlignCenter)
        self.active = False  # Set initially to False
        self.url = url
        self.stream_thread = None  # Placeholder for StreamThread
        self.setup_ui()

    def to_dict(self):
        return {
            'stream_url': self.url,
            'active': self.active
        }

    def setup_ui(self):
         # Create a main layout for the VideoFrame
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignBottom)

    # Create a QSplitter to divide the frame into two panels (top and bottom)
        splitter = QSplitter(Qt.Vertical)

    # Create a widget for streaming video (top panel)
        video_widget = QLabel(self)
        video_widget.setAlignment(Qt.AlignCenter)
        video_widget.setStyleSheet("border: 2px solid blue; color: white;")  # Set text color to white
        splitter.addWidget(video_widget)

    # Create a widget for info labels and buttons (bottom panel)
        info_widget = QWidget(self)
        info_layout = QVBoxLayout(info_widget)

    # Add a delete button to the widget
        delete_button = QToolButton(self)
        delete_button.setIcon(QIcon("bin.png"))  # Replace with the actual path to your delete icon
        delete_button.clicked.connect(self.handle_delete_request)
        delete_button.setStyleSheet("color: white;")  # Set text color to white
        info_layout.addWidget(delete_button)

    # Button to toggle stream on/off
        self.stream_button = QPushButton("Toggle Stream", info_widget)
        self.stream_button.clicked.connect(self.toggle_stream)
        self.stream_button.setStyleSheet("color: white;")  # Set text color to white
        info_layout.addWidget(self.stream_button)

    # Add labels and button to the widget's layout
        self.size_label = QLabel(f"Size: {self.width()} x {self.height()}", info_widget)
        self.size_label.setStyleSheet("color: white;")  # Set text color to white
        self.url_label = QLabel(f"Stream URL: {self.url}", info_widget)
        self.url_label.setStyleSheet("color: white;")  # Set text color to white
        info_layout.addWidget(self.size_label)
        info_layout.addWidget(self.url_label)
        info_layout.addStretch()

    # Add widgets to the splitter
        splitter.addWidget(info_widget)

    # Add the splitter to the main layout
        main_layout.addWidget(splitter)

    def toggle_stream(self):
        # Implement the logic to start/stop the stream based on the button click
        self.active = not self.active

        # Toggle button text
        self.stream_button.setText("Turn Stream (Off)" if self.active else "Turn Stream (On)")

        if self.active:
            # Start stream
            self.streamStateChanged.emit(True, self.url)
            self.start_stream()
        else:
            # Stop stream
            self.streamStateChanged.emit(False, self.url)
            self.stop_stream()

        self.set_active(self.active)  # Call set_active to update the appearance

    def set_active(self, active):
        self.active = active
        self.setStyleSheet("border: 2px solid green;" if active else "")

    def start_stream(self):
        # TODO: Implement logic to start streaming from the URL and update the QLabel
        self.stream_thread = StreamThread(self.url)
        self.stream_thread.update_frame_signal.connect(self.update_video_frame)
        self.stream_thread.start()

    def stop_stream(self):
        # TODO: Implement logic to stop streaming and clear the QLabel
        if self.stream_thread is not None:
            self.stream_thread.stop()
            self.stream_thread.wait()
            self.stream_thread = None
            self.findChild(QLabel).clear()

    def update_video_frame(self, qImg):
        # Update the QLabel with the new frame
        self.findChild(QLabel).setPixmap(QPixmap.fromImage(qImg))

    def handle_delete_request(self):
        # Emit the deleteRequested signal when the delete button is clicked
        self.deleteRequested.emit(self)

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
    def __init__(self, parent=None):
        super(SetupScreenPopup, self).__init__(parent)
        self.setWindowTitle("Setup New Screen")
        self.setGeometry(300, 300, 800, 400)

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
        self.accept()


class RemoteScreen:
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.available = True  # Assume all screens are initially available

# Add the FullscreenOptionsPopup class
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
    
class AddStreamDialog(QDialog):
    def __init__(self, parent=None):
        super(AddStreamDialog, self).__init__(parent)
        self.setWindowTitle("Add New Screen")
      
        self.setGeometry(100, 100, 1000, 600)

        self.init_ui()

    # def init_ui(self):
    #     label_url = QLabel("Enter Stream URL:", self)
    #     self.url_input = QLineEdit(self)

    #     add_button = QPushButton("Add Stream", self)
    #     add_button.clicked.connect(self.accept)

    #     layout = QVBoxLayout(self)
    #     layout.addWidget(label_url)
    #     layout.addWidget(self.url_input)
    #     layout.addWidget(add_button)

    def init_ui(self):
        form_layout = QFormLayout(self)

        # Set black background and white text color
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

        # Add Stream URL field (Replace with YouTube URL)
        label_url = QLabel("Enter YouTube URL:", self)
        self.url_input = QLineEdit(self)
        form_layout.addRow(label_url, self.url_input)

        # Add additional fields
        form_layout.addRow("Screen No.", QLineEdit(self))
        form_layout.addRow("Id", QLineEdit(self))
        form_layout.addRow("Psw", QLineEdit(self))
        form_layout.addRow("Place", QLineEdit(self))
        form_layout.addRow("Slide Show", QLineEdit(self))
        form_layout.addRow("Created", QDateEdit(self))
        form_layout.addRow("Length", QSpinBox(self))
        form_layout.addRow("Start date", QDateEdit(self))
        form_layout.addRow("Expiry date", QDateEdit(self))

        # Add Stream Button
        add_button = QPushButton("Add New Screen", self)
        add_button.clicked.connect(self.accept)
        add_button.setStyleSheet("background-color: #4F94CD; color: white;")
        form_layout.addRow(add_button)

        def add_form_field(self, label_text, widget):
            label = QLabel(label_text, self)
            label.setStyleSheet("background-color: black; color: white;")
            form_layout.addRow(label, widget)

        # # Set stylesheets for each widget
        # for item in self.findChildren((QLabel, QLineEdit, QDateEdit, QSpinBox, QPushButton)):
        #     item.setStyleSheet("background-color: white; color: black;")

    

    def get_stream_url(self):
        return self.url_input.text()


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

        

        logo_pixmap = QPixmap("./logo.png").scaled(350, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label = QLabel(self.header)
        self.logo_label.setPixmap(logo_pixmap)
        self.header_layout.addWidget(self.logo_label)

        self.header_layout.addStretch()

        self.left_panel = QFrame(self)
        self.left_panel.setStyleSheet("background-color: #28282B;")

        self.right_panel = QFrame(self)
        self.right_panel.setStyleSheet("background-color: #28282B;")

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
        # self.btn_setup.clicked.connect(self.setup_setup_screen)
        self.btn_setup.clicked.connect(self.add_stream)
        self.left_panel_layout.addWidget(self.btn_setup)


        self.btn_fullscreen = QPushButton("Full Screen", self.left_panel)
        self.btn_fullscreen.setStyleSheet("background-color: #28282B; color: white;")
        self.btn_fullscreen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        # self.btn_fullscreen.clicked.connect(self.show_fullscreen_options)

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

       
        self.video_frames = [] 
        self.video_frame_layout = QGridLayout(self.right_panel)
        # self.video_frame_layout.setAlignment(Qt.AlignTop)
        # self.video_frame_layout.setVerticalSpacing(10) 
        

        # Initialize the video frame grid layout
        self.video_frame_grid_layout = QGridLayout(self.right_panel)
        self.right_panel.setLayout(self.video_frame_grid_layout)
        self.video_frame_grid_layout.setAlignment(Qt.AlignTop)
        self.video_frame_grid_layout.setVerticalSpacing(50)


        self.footer = QLabel("© 2024 SPONSOR SALES", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color:black")
        self.main_layout.addWidget(self.footer)

        self.timer = QTimer(self)
        # self.timer.timeout.connect(self.update_active_video_frame)
        self.timer.start(1000)
        # Load previously saved video frames
        self.load_video_frames()


    

    def save_video_frames(self):
        video_frame_data = [frame.to_dict() for frame in self.video_frames]
        with open('video_frames.pkl', 'wb') as file:
            pickle.dump(video_frame_data, file)

    def load_video_frames(self):
        try:
            with open('video_frames.pkl', 'rb') as file:
                video_frame_data = pickle.load(file)
                self.video_frames = [VideoFrameWidget(frame['stream_url'], self.right_panel) for frame in video_frame_data]
                # for frame in self.video_frames:
                #     # self.video_frame_layout.addWidget(frame)
                #     row, col = divmod(len(self.video_frames) - 2, 2)  # Adjust the number of columns as needed
                #     self.video_frame_layout.addWidget(frame, row, col)
                #     print(f"Loaded video frame: {frame.to_dict()}")

                for idx, frame in enumerate(self.video_frames):
                    row, col = divmod(idx, 3)  # Adjust the number of columns as needed
                    self.video_frame_layout.addWidget(frame, row, col)
                    print(f"Loaded video frame: {frame.to_dict()}")
        except FileNotFoundError:
            self.video_frames = []

    def add_stream(self):
        add_stream_dialog = AddStreamDialog(self)
        result = add_stream_dialog.exec_()
        if result == QDialog.Accepted:
            stream_url = add_stream_dialog.get_stream_url()
            self.add_video_frame(stream_url)

    def add_video_frame(self, stream_url):
        video_frame = VideoFrameWidget(stream_url, self.right_panel)
        video_frame.deleteRequested.connect(self.delete_video_frame)
        self.video_frames.append(video_frame)

        video_frame.toggle_stream()

    # Add the video frame to the grid layout
        row, col = divmod(len(self.video_frames) - 1, 2)  # Adjust the number of columns as needed
        self.video_frame_layout.addWidget(video_frame, row, col)

        self.save_video_frames()
        # self.load_video_frames()

    def update_active_video_frame(self):
        for video_frame in self.video_frames:
            video_frame.set_active(video_frame == self.active_video_frame)

    # Adjust the splitter sizes to make sure the right panel gets resized properly
        self.splitter.setSizes([int(self.width() * 0.3), int(self.width() * 0.7)])

    def delete_video_frame(self, video_frame):
    # Remove the video frame from the list and layout
        self.video_frames.remove(video_frame)
        self.video_frame_grid_layout.removeWidget(video_frame)
        video_frame.setParent(None)
        video_frame.deleteLater()


    def setup_upload_screen(self):
        upload_popup = UploadScreenPopup(self)
        result = upload_popup.exec_()
        if result == QDialog.Accepted:
            print("Upload to Screen popup accepted")
        else:
            print("Upload to Screen popup canceled")
 

    # def setup_setup_screen(self):
    #     upload_popup = SetupScreenPopup(self)
    #     result = upload_popup.exec_()
    #     if result == QDialog.Accepted:
    #         # Get the stream URL from the upload form (you may need to modify this based on your form implementation)
    #         print(result)
    #         stream_url = "http://example.com/stream"  # Replace this with the actual URL from your form

    #         # Create a new video frame and start streaming for the uploaded stream URL
    #         video_frame = VideoFrame(self.right_panel)
    #         self.video_frames.append(video_frame)
    #         self.video_frame_layout.addWidget(video_frame)

    #         stream_thread = StreamThread(stream_url)
    #         stream_thread.update_frame_signal.connect(lambda image, frame=video_frame: self.update_video_feed(image, frame))
    #         stream_thread.start()

    #     else:
    #         print("Setup New Screen popup canceled")

    def closeEvent(self, event):
        # Stop the stream threads before closing the application
        for stream_thread in getattr(self, 'stream_threads', []):
            stream_thread.stop()
            stream_thread.wait()  # Wait for the thread to finish

        event.accept()

    def update_active_video_frame(self):
        for video_frame in self.video_frames:
            video_frame.set_active(video_frame == self.active_video_frame)

    def start_stream(self, video_frame_idx):
        self.active_video_frame = self.video_frames[video_frame_idx]
        self.active_video_frame.set_active(True)

    @pyqtSlot(QImage, int)
    def update_video_feed(self, image, video_frame_idx):
        video_frame = self.video_frames[video_frame_idx]
        video_frame.setPixmap(QPixmap.fromImage(image))

    @pyqtSlot(QImage)
    def update_all_video_frames(self, image):
        for idx, video_frame in enumerate(self.video_frames):
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
        self.stream_threads = [StreamThread('http://192.168.1.5:5000/video_feed') for _ in self.video_frames]
        for idx, stream_thread in enumerate(self.stream_threads):
            stream_thread.update_frame_signal.connect(lambda image, idx=idx: self.update_video_feed(image, idx))
            stream_thread.start()

app = QApplication(sys.argv)
ex = VideoUploaderApp()
ex.show()
sys.exit(app.exec_())
