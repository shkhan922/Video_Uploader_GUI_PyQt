import sys
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QPushButton,
    QWidget, QFrame, QSplitter, QFileDialog, QSpacerItem, QButtonGroup,
    QDialog,QHBoxLayout,QHeaderView,QSizePolicy,QLineEdit, QSpinBox,QGridLayout,QToolButton,QMessageBox
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import   QFormLayout, QDateEdit, QSpinBox,QDialogButtonBox
from PyQt5.QtGui import QPalette, QColor
from base64 import b64decode
from PyQt5.QtCore import pyqtSlot
import requests
import cv2
import numpy as np
import pickle
import json
from pathlib import Path  



class StreamThread(QThread):
    update_frame_signal = pyqtSignal(QImage)
    error_signal = pyqtSignal(str)

    def __init__(self, url, update_interval=100):
        super().__init__()
        self.url = url
        self.update_interval = update_interval
        self.stopped = False

    def stop(self):
        self.stopped = True

    def run(self):
        try:
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
                        jpg = bytes_data[a:b + 2]
                        bytes_data = bytes_data[b + 2:]
                        self.emit_frame(jpg)
        except Exception as e:
            self.error_signal.emit(str(e))

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


class VideoFrameWidget(QLabel):
    deleteRequested = pyqtSignal(QWidget)
    streamStateChanged = pyqtSignal(bool, str)  # Signal for stream state change (on/off)

    def __init__(self, url, screen_name, screen_number, parent=None):
        super(VideoFrameWidget, self).__init__(parent)
        self.setFixedSize(400, 400)
        self.setAlignment(Qt.AlignCenter)
        self.active = False  # Set initially to False
        self.screen_name = screen_name  # Store the screen name as an instance attribute
        self.screen_number = screen_number
        self.url = url
        self.stream_thread = None  # Placeholder for StreamThread
        self.setup_ui()

        print(self.screen_name)
        print(self.screen_number)

    def to_dict(self):
        return {
            'stream_url': self.url,
            'screen_name': self.screen_name,
            'screen_number': self.screen_number,
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
        video_widget.setStyleSheet("border: 2px solid red; color: white;")  # Set text color to white
        splitter.addWidget(video_widget)

    # Create a widget for info labels and buttons (bottom panel)
        info_widget = QWidget(self)
        info_layout = QVBoxLayout(info_widget)


        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

# Add the delete button
        # Add the delete button
        delete_button = QToolButton(self)
        delete_button.setIcon(QIcon("bin.png")) 
        delete_button.setText("Delete")  # Add text to the button
        delete_button.clicked.connect(self.confirm_delete)
        delete_button.setStyleSheet("color: white;")  # Set text color to white
        delete_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Display icon and text beside each other
        button_layout.addWidget(delete_button)

# Add the edit button
        edit_button = QToolButton(self)
        edit_button.setIcon(QIcon("edit.png"))  # Provide appropriate icon
        edit_button.setText("Edit")  # Add text to the button
        edit_button.clicked.connect(self.handle_edit_request)
        edit_button.setStyleSheet("color: white;")  # Set text color to white
        edit_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Display icon and text beside each other
        button_layout.addWidget(edit_button)

        # Add the fullscreen button
        fullscreen_button = QToolButton(self)
        fullscreen_button.setIcon(QIcon("fullscreen.png"))  # Provide appropriate icon
        fullscreen_button.setText("Fullscreen")  # Add text to the button
        fullscreen_button.clicked.connect(self.toggle_fullscreen)
        fullscreen_button.setStyleSheet("color: white;")  # Set text color to white
        fullscreen_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)  # Display icon and text beside each other
        button_layout.addWidget(fullscreen_button)

# Add the button layout to the info layout
        info_layout.addLayout(button_layout)

    # Button to toggle stream on/off
        self.stream_button = QPushButton("Start Stream", info_widget)
        self.stream_button.clicked.connect(self.toggle_stream)
        self.stream_button.setStyleSheet("color: white;")  # Set text color to white
        info_layout.addWidget(self.stream_button)

        # Create a horizontal layout for the screen details
        screen_layout = QHBoxLayout()

# Add the monitor icon
        

# Add the screen name label
        screen_name_label = QLabel(f" {self.screen_name}", info_widget)
        screen_name_label.setStyleSheet("color: white;")  # Set text color to white
        screen_layout.addWidget(screen_name_label)

    #     monitor_label = QLabel(self)
    #     monitor_label.setPixmap(QPixmap("monitor_icon.png")) 
    #    # Set the monitor icon
    #     screen_layout.addWidget(monitor_label)

        monitor_label = QToolButton(self)
        monitor_label.setIcon(QIcon("monitor_icon.png"))  # Provide appropriate icon
        monitor_label.setText(f" {self.screen_number}")  # Add text to the button
        # monitor_label.clicked.connect(self.handle_edit_request)
        monitor_label.setStyleSheet("color: white;")  # Set text color to white
        monitor_label.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

          # Display icon and text beside each other
        screen_layout.addWidget(monitor_label)

# Add the screen number label
        # screen_number_label = QLabel(f" {self.screen_number}", info_widget)
        # screen_number_label.setStyleSheet("color: white;")  # Set text color to white
        # screen_layout.addWidget(screen_number_label)

# Add the size label
        self.size_label = QLabel(f" {self.width()} : {self.height()}", info_widget)
        self.size_label.setStyleSheet("color: white;")  # Set text color to white
        screen_layout.addWidget(self.size_label)



# Add the screen details layout to the info layout
        info_layout.addLayout(screen_layout)   

    # Add labels and button to the widget's layout
        
        self.url_label = QLabel(f"{self.url}", info_widget)
        self.url_label.setStyleSheet("color: #4F94CD;")  # Set text color to white
        # info_layout.addWidget(self.size_label)
        info_layout.addWidget(self.url_label)
        info_layout.addStretch()

    # Add widgets to the splitter
        splitter.addWidget(info_widget)

    # Add the splitter to the main layout
        main_layout.addWidget(splitter)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()  # Exit fullscreen mode
        else:
            self.showFullScreen()

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
        self.setStyleSheet("border: 2px solid;" if active else "")

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
    # Get the parent widget
        current_parent = self.parent()
        app_instance = None

    # Traverse the parent hierarchy until a VideoUploaderApp instance is found
        while current_parent:
            if isinstance(current_parent, VideoUploaderApp):
                app_instance = current_parent
                break
            current_parent = current_parent.parent()

    # Check if the VideoUploaderApp instance is found
        if app_instance:
        # Remove the widget from the parent's video_frames list
            if self in app_instance.video_frames:
                app_instance.video_frames.remove(self)
            # Update JSON file
                app_instance.save_video_frames()
            else:
                print("Widget not found in video_frames list.")
        else:
            print("Parent widget not found or is not an instance of VideoUploaderApp.")

    # Remove from UI
        self.setParent(None)
        self.deleteLater()


    def confirm_delete(self):
        reply = QMessageBox.question(self, 'Delete Confirmation', 'Are you sure you want to delete this stream?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        msg_box = QMessageBox()
        msg_box.setStyleSheet("QMessageBox { color: white; }")
        if reply == QMessageBox.Yes:
            self.handle_delete_request()

    def handle_edit_request(self):
        # Open a dialog to edit the URL and other options
        edit_dialog = EditDialog(self.url, parent=self)
        if edit_dialog.exec_() == QDialog.Accepted:
            # Update the URL and other options
            self.url = edit_dialog.get_url()
            # Update the label or any other UI components as needed
            self.url_label.setText(f"Stream URL: {self.url}")

    def handle_stream_error(self, error_msg):
        # Handle errors when the stream is not available
        self.active = False
        self.stream_button.setText("Turn Stream (On)")  # Reset button text
        self.set_active(False)  # Update appearance
        self.update_video_frame(QImage())  # Clear video frame
        self.stream_thread = None
        QMessageBox.warning(self, "Stream Error", f"Error accessing stream: {error_msg}")

class EditDialog(QDialog):
    def __init__(self, initial_url, parent=None):
        super(EditDialog, self).__init__(parent)
        self.setWindowTitle("Edit Stream Details")
        self.setGeometry(300, 300, 400, 200)

        self.init_ui(initial_url)

    def init_ui(self, initial_url):
        layout = QVBoxLayout(self)

        self.url_label = QLabel("Stream URL:", self)
        self.url_input = QLineEdit(initial_url, self)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(buttons)

        # Set text color to white
        self.setStyleSheet("color: white;")

    def get_url(self):
        return self.url_input.text()




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
        self.screen_name_input = QLineEdit(self)
        self.screen_number_input = QLineEdit(self)
        form_layout.addRow("Screen Name:", self.screen_name_input)
        form_layout.addRow("Screen Number:", self.screen_number_input)

        # Add additional fields
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
    
    def get_screen_name(self):
        return self.screen_name_input.text()

    def get_screen_number(self):
        return self.screen_number_input.text()


class UploadVideoDialog(QDialog):
    def __init__(self, parent=None):
        super(UploadVideoDialog, self).__init__(parent)
        self.setWindowTitle("Upload Video")
        self.setGeometry(100, 100, 1000, 700)
        self.init_ui()

    
    def init_ui(self):
        layout = QGridLayout(self)

    # Set background color and text color
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor('#28282B'))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)

    # Add header label
        header_label = QLabel("Upload MP4 to Remote Client", self)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label, 0, 0, 1, 2)

    # Add IP/URL field
        ip_label = QLabel("Enter IP/URL of Remote Client:", self)
        self.ip_input = QLineEdit(self)
        layout.addWidget(ip_label, 1, 0)
        layout.addWidget(self.ip_input, 1, 1)

    # Add file selection button
        self.file_button = QPushButton("Choose MP4 File", self)
        self.file_button.clicked.connect(self.choose_file)
        self.file_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addWidget(self.file_button, 2, 0, 1, 2)

    # Add upload button
        upload_button = QPushButton("Upload MP4", self)
        upload_button.clicked.connect(self.upload_mp4)
        upload_button.setStyleSheet("background-color: #4F94CD; color: white;")
        upload_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        layout.addWidget(upload_button, 3, 0, 1, 2)

    # Set column stretch to make the input field stretch horizontally
        layout.setColumnStretch(1, 1)

    # Set layout alignment
        layout.setAlignment(Qt.AlignCenter)

    def choose_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Choose MP4 File", "", "MP4 Files (*.mp4)", options=options)
        if file_name:
            self.file_button.setText(file_name)

   
    def upload_mp4(self):
        mp4_path = self.file_button.text().strip()  # Get the selected file path from the button text
        ip_url = self.ip_input.text().strip()

        if not mp4_path or not ip_url:
            QMessageBox.warning(self, "Warning", "Please enter the IP/URL and choose an MP4 file.")
            return

        print("Upload button clicked")
        try:
            with open(mp4_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(f'http://{ip_url}/upload_mp4', files=files)
                response_data = response.json()
                print(response_data)

                if response_data.get('status') == 'success':
                    QMessageBox.information(self, "Success", "MP4 file uploaded successfully.")
                    self.accept()  # Close the dialog window
                else:
                    QMessageBox.warning(self, "Error", "Failed to upload MP4 file. Please try again.")
        except Exception as e:
            print(f"Error uploading MP4 file: {e}")

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
        self.header.setFixedHeight(100)
        self.header_layout = QVBoxLayout(self.header)
        self.header.setStyleSheet("background-color: #28282B;")
        self.main_layout.addWidget(self.header)

        
        

        logo_pixmap = QPixmap("./logo.png").scaled(350, 130, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label = QLabel(self.header)
        self.logo_label.setPixmap(logo_pixmap)
        self.header_layout.addWidget(self.logo_label)

        self.header_layout.addStretch()

        # Add the header label below the logo label in the header layout
        self.header_label = QLabel("Main", self.header)
        # self.header_label.setFixedWidth(180)
        # self.header_label.setStyleSheet("color: #4F94CD; font-size: 20px;")
        self.header_label.setStyleSheet("background-color: #4F94CD; color: white; font-size: 30px; border: 2px solid #4F94CD; border-radius: 5px;")

        self.header_label.setAlignment(Qt.AlignCenter)
        # self.header_layout.setAlignment(Qt.AlignHCenter)

        self.header_layout.addWidget(self.header_label)

       

# Adjust the logo label alignment to center
        # self.logo_label.setAlignment(Qt.AlignCenter)

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
        

        # Initialize the video frame grid layout
        self.video_frame_grid_layout = QGridLayout(self.right_panel)
        self.right_panel.setLayout(self.video_frame_grid_layout)
        self.video_frame_grid_layout.setAlignment(Qt.AlignTop)
        self.video_frame_grid_layout.setVerticalSpacing(50)

        # self.header_label = QLabel("Main", self.right_panel)
        # self.header_label.setStyleSheet("color: #4F94CD; font-size: 20px;")
        # self.header_label.setAlignment(Qt.AlignCenter)

        # # Get the number of columns in the right panel's grid layout
        # num_columns = self.video_frame_grid_layout.columnCount()
        # self.video_frame_grid_layout.addWidget(self.header_label, 0, 0, 1, num_columns)


        self.footer = QLabel("© 2024 SPONSOR SALES", self)
        self.footer.setAlignment(Qt.AlignCenter)
        self.footer.setFixedHeight(20)
        self.footer.setStyleSheet("background-color:black; color: #e5b73b; font-size: 20px;")
        self.main_layout.addWidget(self.footer)

        self.timer = QTimer(self)
        # self.timer.timeout.connect(self.update_active_video_frame)
        self.timer.start(1000)
        # Load previously saved video frames
        self.load_video_frames()

     
    def save_video_frames(self):
        video_frame_data = [frame.to_dict() for frame in self.video_frames]
        with open('video_frames.json', 'w') as file:  # Open file in text mode ('w')
            json.dump(video_frame_data, file)

    def load_video_frames(self):
        file_path = Path('video_frames.json')
        if file_path.exists():
            try:
                with open(file_path, 'r') as file:
                    video_frame_data = json.load(file)
                    for frame_data in video_frame_data:
                        stream_url = frame_data['stream_url']
                        screen_name = frame_data['screen_name']
                        screen_number = frame_data['screen_number']
                        video_frame = VideoFrameWidget(stream_url, screen_name, screen_number, self.right_panel)
                        self.video_frames.append(video_frame)

                    # Add loaded video frames to layout
                        row, col = divmod(len(self.video_frames) - 1, 2)
                        self.video_frame_layout.addWidget(video_frame, row, col)
                        print(f"Loaded video frame: {frame_data}")
            except json.JSONDecodeError:
                QMessageBox.critical(self, "Error", "Invalid JSON data in the file.")
                self.video_frames = []
        else:
            self.video_frames = []

    # def add_stream(self):
    #     add_stream_dialog = AddStreamDialog(self)
    #     result = add_stream_dialog.exec_()
    #     if result == QDialog.Accepted:
    #         stream_url = add_stream_dialog.get_stream_url()
    #         self.add_video_frame(stream_url)

    def add_stream(self):
        add_stream_dialog = AddStreamDialog(self)
        result = add_stream_dialog.exec_()
        if result == QDialog.Accepted:
            stream_url = add_stream_dialog.get_stream_url()
            screen_name = add_stream_dialog.get_screen_name()  # Example method to get screen name
            screen_number = add_stream_dialog.get_screen_number()  # Example method to get screen number
            self.add_video_frame(stream_url, screen_name, screen_number)


    def add_video_frame(self, stream_url, screen_name, screen_number):
        # Create a new instance of VideoFrameWidget with screen name and number
        video_frame = VideoFrameWidget(stream_url, parent=self.right_panel,
                                       screen_name=screen_name, screen_number=screen_number)
        
        


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
        if video_frame in self.video_frames:
            self.video_frames.remove(video_frame)
            self.video_frame_layout.removeWidget(video_frame)
            video_frame.setParent(None)
            video_frame.deleteLater()
            self.save_video_frames()


    def setup_upload_screen(self):
        upload_popup = UploadVideoDialog(self)
        result = upload_popup.exec_()
        if result == QDialog.Accepted:
            print("Upload to Screen popup accepted")
        else:
            print("Upload to Screen popup canceled")
 

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
