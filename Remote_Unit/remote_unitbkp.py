# remote_unit.py
from flask import Flask, render_template, Response, request, send_file, jsonify
import cv2
import os
from threading import Thread
import subprocess
import pygame
from pygame.locals import *


app = Flask(__name__)

UPLOAD_FOLDER = '/home/admin-dell/Desktop/uploaded_videos'  # Replace with the desired path
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class RemoteUnit:
    # Dictionary to map remote unit names to their respective stream URLs
    REMOTE_UNITS = {
        'Remote Unit 1': 'http://192.168.1.2',
        'Remote Unit 2': 'http://remote_unit_2_stream_url',
        # Add more remote units as needed
    }

# Flag to track if preview is enabled
preview_enabled = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
   

@app.route('/upload_mp4', methods=['POST'])
def upload_mp4():
    uploaded_file = request.files['file']

    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Generate a unique filename for the uploaded video
    video_number = get_next_video_number()
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f'video_{video_number}.mp4')

    uploaded_file.save(file_path)

    # Start a new thread to handle video playback without blocking the main thread
    playback_thread = Thread(target=play_video, args=(file_path,))
    playback_thread.start()

    # Return a response indicating successful upload
    return jsonify({'status': 'success', 'message': f'MP4 file uploaded. Video will be played shortly.'})

def play_video(file_path):
    
    try:
        # Initialize Pygame
        pygame.init()

        # Set the video display mode
        screen = pygame.display.set_mode((640, 480), pygame.DOUBLEBUF)
        pygame.display.set_caption("Video Player")

        # Load the video file
        video = pygame.movie.Movie(file_path)

        # Create a clock to control the frame rate
        clock = pygame.time.Clock()

        # Play the video in a loop
        video.play()
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    video.stop()
                    pygame.quit()
                    return jsonify({'status': 'success', 'message': 'Video played successfully.'})

            # Update the video display
            screen.blit(video.get_surface(), (0, 0))
            pygame.display.flip()

            # Cap the frame rate (adjust as needed)
            clock.tick(30)

    except Exception as e:
        # Log the error
        print(f"Error playing video: {e}")
        return jsonify({'status': 'error', 'message': 'Failed to play video.'}), 500

    # # Play the uploaded video using OpenCV
    # cap = cv2.VideoCapture(file_path)

    # # Check if the video file opened successfully
    # if not cap.isOpened():
    #     print("Error opening video file")
    #     return

    # print(f"Video properties: Width={cap.get(cv2.CAP_PROP_FRAME_WIDTH)}, Height={cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

    # while cap.isOpened():
    #     ret, frame = cap.read()
    #     if not ret:
    #         # Restart video playback when it reaches the end
    #         cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    #         continue

    #     cv2.imshow('Uploaded Video', frame)

    #     # Break the loop if the 'Escape' key is pressed
    #     if cv2.waitKey(30) & 0xFF == 27:
    #         break

    # # Release the video capture object and close OpenCV windows
    # cap.release()
    # cv2.destroyAllWindows()


def enable_preview(stream_url):
    global preview_enabled
    # Additional logic to customize the preview based on the stream_url
    # For now, simply enable the preview
    preview_enabled = True

def generate_stream():
    while True:
        video_list = get_video_list()
        for video_path in video_list:
            cap = cv2.VideoCapture(video_path)
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    # Restart video playback when it reaches the end
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                ret, jpeg = cv2.imencode('.jpg', frame)
                frame_bytes = jpeg.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')
                
            cap.release()

def get_next_video_number():
    # Find the highest video number in the upload folder and increment it
    video_numbers = [int(file.split('_')[1].split('.')[0]) for file in os.listdir(app.config['UPLOAD_FOLDER']) if file.startswith('video_')]
    return max(video_numbers, default=0) + 1

def get_video_list():
    # Get the list of video files in the upload folder
    video_files = [file for file in os.listdir(app.config['UPLOAD_FOLDER']) if file.endswith('.mp4')]
    return [os.path.join(app.config['UPLOAD_FOLDER'], file) for file in video_files]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
