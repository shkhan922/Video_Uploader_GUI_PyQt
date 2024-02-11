from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog
from PyQt5.QtCore import Qt
import sys
import cv2
from threading import Thread
import requests

class MainUnit(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Video Uploader')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        # Header
        header_label = QLabel('<h1 align="center">Video Uploader</h1>', self)
        layout.addWidget(header_label)

        # Video Preview Frame
        self.video_frame = QLabel(self)
        self.video_frame.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_frame)

        # Upload Button
        upload_button = QPushButton('Upload MP4 to Remote', self)
        upload_button.clicked.connect(self.upload_mp4)
        layout.addWidget(upload_button)

        # Show Preview Button
        show_preview_button = QPushButton('Show Preview', self)
        show_preview_button.clicked.connect(self.show_preview)
        layout.addWidget(show_preview_button)

        self.setLayout(layout)

    def upload_mp4(self):
        file_dialog = QFileDialog()
        mp4_path, _ = file_dialog.getOpenFileName(self, 'Select MP4 File', '', 'MP4 Files (*.mp4)')

        if mp4_path:
            files = {'file': open(mp4_path, 'rb')}
            response = requests.post('http://192.168.1.3:5000/upload_mp4', files=files)
            print(response.text)  # Print the response from the REMOTE unit


    def show_preview(self):
        stream_url = "http://192.168.1.3:5000/video_feed"  # Assuming this is the URL for the video feed

        # Start a thread to continuously read and display the video stream
        preview_thread = Thread(target=self.preview_video_stream, args=(stream_url,))
        preview_thread.start()

    def preview_video_stream(self, stream_url):
        cap = cv2.VideoCapture(stream_url)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert the frame from BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert the frame to QImage
            height, width, channel = rgb_frame.shape
            bytesPerLine = 3 * width
            qImg = QImage(rgb_frame.data, width, height, bytesPerLine, QImage.Format_RGB888)

            # Display the QImage in the QLabel (video frame)
            self.video_frame.setPixmap(qImg.scaled(self.video_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            # Add a small delay to control the frame rate
            cv2.waitKey(30)

        cap.release()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_unit = MainUnit()
    main_unit.show()
    sys.exit(app.exec_())
