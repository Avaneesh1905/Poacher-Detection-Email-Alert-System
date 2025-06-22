import gi #GObject Introspection
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib # Used for processing the video stream
import os
import numpy as np
import cv2 # For image processing and computer vision
import hailo # To access detection results from the Hailo pipeline
import sys
import time
from datetime import datetime # For date and time handling
from gpiozero import LED # To control LED or GPIO pins when person is detected
import threading # Provides a way to run multiple threads concurrently within a single process
import smtplib # To send the E-mails via SMTP protocol
from email.message import EmailMessage # To build the E-mail messages
from hailo_apps_infra.hailo_rpi_common import (
    get_caps_from_pad,
    get_numpy_from_buffer,
    app_callback_class,
)
from hailo_apps_infra.detection_pipeline import GStreamerDetectionApp
# Hailo-specific utility functions and classes

Gst.init(None) # Initialize Gstreamer

# Setup GPIO
person_gpio = LED(27) #BCM 27

# Configuration Constants
SENDER_EMAIL = "Insert Sender's E-mail"
SENDER_PASSWORD = "16 letter password"

# Setup folder to store the snapshots
ALERT_FOLDER = "alerts"
os.makedirs(ALERT_FOLDER, exist_ok=True)
COOLDOWN_TIME = 10 * 60  # 10 minutes in seconds

# Email Sending Function
def send_email_with_image(image_path):
    try:
        msg = EmailMessage()
        msg["Subject"] = f"Person Detected Alert at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        msg["From"] = "SENDER_ENAIL"
        msg["To"] = "RECEIVER_EMAIL"
        msg.set_content(f'''
        A person has been detected by the Raspberry Pi surveillance system.

        Type of Life detected: Human
        Date: {datetime.now().strftime('%Y-%m-%d')}
        Time: {datetime.now().strftime('%H:%M:%S')}

        The attached snapshot was captured automatically. Please verify if this activity is authorized.

        Regards,
        Forest Surveillance System.
        ''')

        with open(image_path, 'rb') as f:
            img_data = f.read()
            msg.add_attachment(img_data, maintype='image', subtype='jpeg', filename=os.path.basename(image_path))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login("SENDER_EMAIL", "16 letter password")
            smtp.send_message(msg)
        print(f"Email alert sent successfully")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# User Application Callback Class - Tracks when to send alerts and cooldowns
class user_app_callback_class(app_callback_class):
    def __init__(self):
        super().__init__()
        self.cooldown_flag = False
        self.person_detection_start_time = None  # Start time for 2-sec hold
        self.use_frame = True

    def start_cooldown(self):
        self.cooldown_flag = True
        threading.Thread(target=self._cooldown_timer, daemon=True).start()

    def _cooldown_timer(self):
        print("[INFO] Cooldown started.")
        time.sleep(COOLDOWN_TIME)
        self.cooldown_flag = False
        print("[INFO] Cooldown ended. System is ready.")

# Main Callback Function - The Heart of the System - Main detection logic (runs for each frame captured by the camera)
def app_callback(pad, info, user_data):
    buffer = info.get_buffer()
    if buffer is None:
        return Gst.PadProbeReturn.OK

    # Get the caps from the pad
    format, width, height = get_caps_from_pad(pad)
    # Get video frame - try to get frame regardless of use_frame setting
    frame = None
    if format is not None and width is not None and height is not None:
        try:
            frame = get_numpy_from_buffer(buffer, format, width, height)
        except Exception as e:
            frame = None
    # Get the detections from the buffer
    roi = hailo.get_roi_from_buffer(buffer)
    detections = roi.get_objects_typed(hailo.HAILO_DETECTION)
    detection_count = 0
    string_to_print = None
    current_time = time.time()
    # Track which persons are detected in this frame
    detected_persons = set()
    # Parse the detections
    detection_found = False

    for detection in detections:
        label = detection.get_label()
        confidence = detection.get_confidence()
        if label == "person" and confidence > 0.96:
            detection_found = True
            bbox = detection.get_bbox()
            x1 = int(bbox.xmin() * width)
            y1 = int(bbox.ymin() * height)
            w = int(bbox.width() * width)
            h = int(bbox.height() * height)

            string_to_print = (
                f"\033[2J\033[HPerson Detection (High Confidence >96%):\n"
                f"Label: {label}\n"
                f"Confidence: {confidence:.2f}\n"
                f"BBox: x={x1}, y={y1}, w={w}, h={h}\n"
                f"Frame Size: {width}x{height}\n"
                f"{'-' * 40}\n"
            )
            if user_data.person_detection_start_time is None:
                user_data.person_detection_start_time = current_time
            elif not user_data.cooldown_flag and (current_time - user_data.person_detection_start_time >= 2):
                alert_filename = f"alert_person_{int(current_time)}.jpg"
                alert_path = os.path.join(ALERT_FOLDER, alert_filename)

                if frame is not None:
                    alert_frame = frame.copy()
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(alert_frame, f"Person Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                    if len(alert_frame.shape) == 3 and alert_frame.shape[2] == 3:
                        alert_frame = cv2.cvtColor(alert_frame, cv2.COLOR_RGB2BGR)

                    success = cv2.imwrite(alert_path, alert_frame)
                    if success:
                        print(f"Snapshot saved at: {alert_path}")
                        if send_email_with_image(alert_path):
                            print("Email sent.")
                            user_data.start_cooldown()
                            user_data.person_detection_start_time = None
                            person_gpio.on()
                            time.sleep(1)
                            person_gpio.off()
                        else:
                            print("Failed to send email.")
                    else:
                        print("Failed to save snapshot.")
                else:
                    print("Frame was None. Cannot send alert.")
                    user_data.start_cooldown()
                    user_data.person_detection_start_time = None
            break  # Only process first person detection

    if not detection_found:
        user_data.person_detection_start_time = None
    # Print detection info if available
    if string_to_print:
        print(string_to_print)
    # Update frame if needed
    if user_data.use_frame and frame is not None:
        # Convert frame to BGR for OpenCV display
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        date_str, time_str = now.split()
        # Create a blank margin on the left
        left_margin = 300
        new_frame = np.zeros((frame.shape[0], frame.shape[1] + left_margin, 3), dtype=np.uint8)
        new_frame[:, left_margin:] = frame

        # Add all info to the margin
        cv2.putText(new_frame, "Person Detected", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(new_frame, "Type of Life: Human", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(new_frame, f"Detections: {detection_count}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(new_frame, f"DATE: {date_str}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(new_frame, f"TIME: {time_str}", (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        user_data.set_frame(new_frame)

    return Gst.PadProbeReturn.OK

# Main Application
if __name__ == "__main__":
    # Create an instance of the user app callback class
    user_data = user_app_callback_class() 
    # Enable frame capture
    user_data.use_frame = True

    print("Starting detection app with email alerts...")
    print(f"Alert folder: {ALERT_FOLDER}")
    print(f"Cooldown time: {COOLDOWN_TIME} seconds")
   
    app = GStreamerDetectionApp(app_callback, user_data)
    app.run()