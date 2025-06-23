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

## How to Set Up
### Hardware Setup on Raspberry Pi:

1. Connect Raspberry Pi 5 with Hailo AI kit and a camera module.
2. Flash Raspberry Pi OS and connect RPi to desktop monitor (optional) or access via RealVNC from a laptop

### Software Setup on Raspberry Pi:

```bash
# Update your Raspberry Pi OS packages
sudo apt update && sudo apt upgrade -y

# Install required dependencies
sudo apt install python3-pip python3-opencv python3-numpy git -y

# Enable camera module and configure the Raspberry Pi Hardware if connected for the first time
# For camera - Interface Options → Camera → Enable
sudo raspi-config

# Then reboot Pi
sudo reboot

# Install Hailo TAPPAS SDK - Follow the instructions provided by Hailo for installing the TAPPAS SDK on Raspberry Pi 5 with the Hailo-8 AI Module

# After reboot and SDK install, open Terminal and Clone the Hailo Pi example repository
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git

# Navigate into the folder
cd hailo-rpi5-examples

# Create a new folder to store snapshots
mkdir alerts

# Navigate to the detection pipeline
cd basic_pipelines

# Open the detection script and paste the detection code from this project (detection.py) into that file
# Modify as per use case and make sure to update the sender/receiver E-Mails and authenticate your own 16 letter App password
nano detection.py

# Go back to root folder
cd ..

# Activate the environment
source setup_env.sh

# Run the detection program using Raspberry Pi camera
python3 basic_pipelines/detection.py --input rpi

```
## For starting the application on Boot
```bash
~/.config/autostart/person-detection.desktop

[Desktop Entry]
Type=Application
Name=Person Detection
Exec=sh -c "sleep 10 && x-terminal-emulator -e bash -c 'cd /home/pi/hailo-rpi5-examples && source setup_env.sh && python3
basic_pipelines/detection.py --input rpi'"

sudo reboot
```
## For disabling the application running on Boot
```bash
nano ~/.config/AutoStart/person-detection.desktop

#comment out line:
#Exec=sh -c "sleep 10 && x-terminal-emulator -e bash -c 'cd /home/pi/hailo-rpi5-examples && source setup_env.sh && python3 basic_pipelines/detection.py --input rpi'"

```
ctrl+X, y, Enter

## Note
Ensure that:

1. App password is enabled on your Gmail account for SMTP (NOT Normal login password).

2. Email credentials are updated in the script.

3. GPIO pin 27 is connected to an LED/buzzer for alerts.

4. You have proper internet connection on RPi as it's required for sending E-Mails

## Output to expect
1. Detect people with >96% confidence
2. Wait 2 seconds for confirmation
3. Take a snapshot of the frame and save it as jpg file in alerts folder
4. Sends alert email with an image attachment
5. Triggers GPIO pin 27 HIGH for LEDs, alarms, etc.
6. Enters 10-minute cooldown period before allowing new alerts