# main_unit.py
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys
import requests

class MainUnit(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('MAIN Unit')
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.stream_label = QLabel(self)
        layout.addWidget(self.stream_label)

        upload_button = QPushButton('Upload MP4 to Remote', self)
        upload_button.clicked.connect(self.upload_mp4)
        layout.addWidget(upload_button)

        self.setLayout(layout)

    def upload_mp4(self):
        file_dialog = QFileDialog()
        mp4_path, _ = file_dialog.getOpenFileName(self, 'Select MP4 File', '', 'MP4 Files (*.mp4)')

        if mp4_path:
            files = {'file': open(mp4_path, 'rb')}
            response = requests.post('http://192.168.1.2:5000/upload_mp4', files=files)
            print(response.text)  # Print the response from the REMOTE unit

    def display_stream(self, stream_url):
        # Code to display the stream from the REMOTE unit
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_unit = MainUnit()
    main_unit.show()
    sys.exit(app.exec_())
