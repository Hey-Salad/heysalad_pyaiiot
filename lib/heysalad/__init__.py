# HeySalad Camera Project Initialization

# Version information
__version__ = "1.0.0"
__author__ = "HeySalad Team"
__description__ = "ESP32-S3 Camera Server with GC9A01 Display"

# Import configuration
from . import config

# Define constants for application states
STATE_IDLE = 0
STATE_STREAMING = 1
STATE_ERROR = 2

# Image paths
STANDARD_IMAGE = "HSK-STANDARD.bmp"
SPEEDY_IMAGE = "HSK-SPEEDY.bmp"
SHOCKED_IMAGE = "HSK-SHOCKED.bmp"

# WiFi Networks configuration
WIFI_NETWORKS = getattr(config, 'WIFI_NETWORKS', [
    {"ssid": "HeySalad_02", "password": "GutenTag%800"},
    {"ssid": "iPhone von Chilu", "password": "123456789"},
    {"ssid": "VM7464351", "password": "zpijfcisoFw6cveh"}
])