# Poacher Detection and E-Mail Alert System

A real-time AI-based edge surveillance system designed to detect unauthorized human presence (like poachers or trespassers) in forest zones and alert authorities through an automated email with image evidence.

Developed during my summer internship at **Ni Logic Pvt Ltd (Ni2 Designs), Pune**.

## Introduction 
In forest areas and other restricted zones, unauthorized human entry poses a serious threat to wildlife and security. Deploying a real-time alert system can play a crucial role in wildlife conservation.
This project detects people in camera feeds using Raspberry Pi 5 and the Hailo-8L AI accelerator. When a person is detected, it captures a snapshot, sends an email alert, saves the image, and triggers GPIO alerts.

## Components Used

- Raspberry Pi 5
- Hailo-8L AI Kit (Edge AI Accelerator)
- Raspberry Pi OS (64-bit)
- Camera Module
- Python 3
- OpenCV
- GStreamer
- GPIOZero
- Hailo TAPPAS SDK
- Gmail SMTP (App Password Required)

## Features
- Real-time inference using Hailo-8L
- High-confidence person detection (>96%)
- Email alerts with image attachments
- 10-minute cooldown between alerts to prevent inbox spamming
- GPIO support for LEDs/alarms
- Runs autonomously on boot

## 🛠️ How to Set Up

### 📦 Software Setup on Raspberry Pi:

```bash
# Clone the Hailo Pi example repository
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git

cd hailo-rpi5-examples

# Create alerts folder
mkdir alerts

cd basic_pipelines

# Edit detection.py and paste your custom detection code
nano detection.py

# Go back to root folder and activate the environment
cd ..
source setup_env.sh

# Run the detection program using Raspberry Pi camera
python3 basic_pipelines/detection.py --input rpi

```
## For starting the application on Boot
~/.config/autostart/person-detection.desktop

[Desktop Entry]
Type=Application
Name=Person Detection
Exec=sh -c "sleep 10 && x-terminal-emulator -e bash -c 'cd /home/pi/hailo-rpi5-examples && source setup_env.sh && python3
basic_pipelines/detection.py --input rpi'"

sudo reboot

## For disabling the application running on Boot
nano ~/.config/AutoStart/person-detection.desktop

comment out line:
#Exec=sh -c "sleep 10 && x-terminal-emulator -e bash -c 'cd /home/pi/hailo-rpi5-examples && source setup_env.sh && python3 basic_pipelines/detection.py --input rpi'"

ctrl+X, y, enter

## Note
Ensure that:

1. App password is enabled on your Gmail account for SMTP.

2. Email credentials are updated in the script.

3. GPIO pin 27 is connected to an LED/buzzer for alerts.