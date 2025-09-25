"""Camera module for HeySalad Camera Project"""

import board
import busio
import espcamera
import binascii
from . import config

class HeySaladCamera:
    """Manages the ESP32-S3 camera functionality"""
    
    def __init__(self, config_settings=None):
        """
        Initialize the camera
        
        :param config_settings: Optional dictionary to override default camera configuration
        """
        print("Setting up camera...")
        
        # Use provided config or default config
        self.camera_config = config_settings or config.CAMERA_CONFIG
        
        # Camera instance
        self.camera = None
        
        # Try to set up the camera
        try:
            self._setup_camera()
        except Exception as e:
            print(f"Camera initialization error: {e}")
    
    def _setup_camera(self):
        """Internal method to set up the camera hardware"""
        # Create I2C bus for camera configuration
        cam_i2c = busio.I2C(board.CAM_SCL, board.CAM_SDA)
        
        # Initialize camera with provided configuration
        self.camera = espcamera.Camera(
            data_pins=eval(self.camera_config['data_pins']),
            external_clock_pin=eval(self.camera_config['external_clock_pin']),
            pixel_clock_pin=eval(self.camera_config['pixel_clock_pin']),
            vsync_pin=eval(self.camera_config['vsync_pin']),
            href_pin=eval(self.camera_config['href_pin']),
            pixel_format=eval(self.camera_config['pixel_format']),
            frame_size=eval(self.camera_config['frame_size']),
            i2c=cam_i2c,
            external_clock_frequency=self.camera_config['external_clock_frequency'],
            framebuffer_count=self.camera_config['framebuffer_count'],
            grab_mode=eval(self.camera_config['grab_mode'])
        )
        
        # Perform a test capture to ensure camera works
        self._test_camera()
        
        print("Camera initialized successfully")
    
    def _test_camera(self):
        """
        Perform a test capture to validate camera functionality
        
        :return: Boolean indicating camera test success
        """
        try:
            test_frame = self.camera.take(1)
            if test_frame:
                print("Camera test capture successful")
                return True
            else:
                print("Camera test capture failed")
                return False
        except Exception as e:
            print(f"Camera test capture error: {e}")
            return False
    
    def capture_frame(self):
        """
        Capture a single frame from the camera
        
        :return: Captured frame or None
        """
        if not self.camera:
            print("Camera not initialized")
            return None
        
        try:
            frame = self.camera.take(1)
            return frame
        except Exception as e:
            print(f"Frame capture error: {e}")
            return None
    
    def encode_frame_base64(self, frame):
        """
        Encode a camera frame to base64 for transmission
        
        :param frame: Raw camera frame
        :return: Base64 encoded frame string
        """
        if not frame:
            return None
        
        try:
            frame_base64 = binascii.b2a_base64(frame).decode('ascii').strip()
            return frame_base64
        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None
    
    def prepare_frame_message(self, frame):
        """
        Prepare a frame message for WebSocket transmission
        
        :param frame: Raw camera frame
        :return: Dictionary with frame transmission details
        """
        if not frame:
            return None
        
        try:
            return {
                "type": "frame",
                "width": 240,  # From config
                "height": 240,  # From config
                "format": "rgb565",
                "data": self.encode_frame_base64(frame)
            }
        except Exception as e:
            print(f"Frame message preparation error: {e}")
            return None