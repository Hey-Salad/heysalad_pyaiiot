"""
HeySalad Cloud Connection Module

This module provides functions to connect to the HeySalad cloud service at
https://api.kelly.ai.heysalad.app/
"""
import json
import time
import ssl
import binascii
import microcontroller
import gc
import wifi

try:
    import adafruit_requests
except ImportError:
    print("Error: adafruit_requests module required. Please install with:")
    print("  pip install adafruit_requests")

# API configuration
API_ENDPOINT = "https://api.kelly.ai.heysalad.app"
DEVICE_API_PATH = "/api/v1/devices"
TELEMETRY_API_PATH = "/api/v1/telemetry"
COMMANDS_API_PATH = "/api/v1/commands"
HEARTBEAT_INTERVAL = 60  # seconds

class CloudConnection:
    """
    Manages connection to the HeySalad Cloud API
    """
    
    def __init__(self, device_id=None, api_key=None):
        """
        Initialize cloud connection
        
        Args:
            device_id: Unique identifier for this device
            api_key: API key for authentication
        """
        # Use device unique ID if not provided
        self.device_id = device_id or self._generate_device_id()
        self.api_key = api_key
        self.session = None
        self.last_heartbeat = 0
        self.connected = False
        self.last_error = None
    
    def _generate_device_id(self):
        """Generate a unique device ID based on hardware identifiers"""
        # Use CPU unique ID or another hardware identifier
        try:
            uid = binascii.hexlify(microcontroller.cpu.uid).decode('utf-8')
            return f"esp32-{uid}"
        except:
            # Fallback to MAC address if UID isn't available
            try:
                mac = binascii.hexlify(wifi.radio.mac_address).decode('utf-8')
                return f"esp32-{mac}"
            except:
                # Last resort random ID
                import random
                return f"esp32-{random.randint(10000, 99999)}"
    
    def connect(self, pool, api_key=None):
        """
        Connect to the cloud API
        
        Args:
            pool: Socket pool for network connections
            api_key: API key for authentication (optional if provided at init)
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if api_key:
            self.api_key = api_key
            
        try:
            print(f"Connecting to HeySalad Cloud API at {API_ENDPOINT}...")
            
            # Setup SSL context
            ssl_context = ssl.create_default_context()
            
            # Create session
            self.session = adafruit_requests.Session(pool, ssl_context)
            
            # Register device
            success = self.register_device()
            if success:
                self.connected = True
                print("Connected to HeySalad Cloud API")
                
                # Send initial heartbeat
                self.send_heartbeat()
                
            return success
            
        except Exception as e:
            self.last_error = str(e)
            print(f"Cloud connection error: {e}")
            self.connected = False
            return False
    
    def register_device(self):
        """
        Register this device with the cloud service
        
        Returns:
            bool: True if registered successfully, False otherwise
        """
        if not self.session or not self.api_key:
            return False
            
        try:
            # Build device info
            device_info = {
                "device_id": self.device_id,
                "device_type": "ESP32-S3-CAM",
                "firmware_version": "1.0.0",
                "capabilities": ["camera", "display"],
                "ip_address": str(wifi.radio.ipv4_address)
            }
            
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send registration request
            response = self.session.post(
                f"{API_ENDPOINT}{DEVICE_API_PATH}/register",
                json=device_info,
                headers=headers
            )
            
            if response.status_code in (200, 201):
                # Parse response
                data = response.json()
                print(f"Device registered: {data.get('message', 'Success')}")
                return True
            else:
                print(f"Device registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Device registration error: {e}")
            return False
    
    def send_heartbeat(self):
        """
        Send a heartbeat signal to the cloud
        
        Returns:
            bool: True if heartbeat was sent successfully, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Update last heartbeat time
            self.last_heartbeat = time.monotonic()
            
            # Build heartbeat data
            data = {
                "device_id": self.device_id,
                "timestamp": time.time(),
                "status": "online",
                "memory": gc.mem_free(),
                "cpu_temp": microcontroller.cpu.temperature
            }
            
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send heartbeat request
            response = self.session.post(
                f"{API_ENDPOINT}{DEVICE_API_PATH}/heartbeat",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                # Check for any commands from the server
                data = response.json()
                commands = data.get("commands", [])
                
                if commands:
                    print(f"Received {len(commands)} commands from cloud")
                    return commands
                
                return True
            else:
                print(f"Heartbeat failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Heartbeat error: {e}")
            return False
    
    def send_telemetry(self, data):
        """
        Send telemetry data to the cloud
        
        Args:
            data: Dictionary of telemetry data to send
            
        Returns:
            bool: True if data was sent successfully, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Add device ID and timestamp
            telemetry = {
                "device_id": self.device_id,
                "timestamp": time.time(),
                "data": data
            }
            
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send telemetry request
            response = self.session.post(
                f"{API_ENDPOINT}{TELEMETRY_API_PATH}",
                json=telemetry,
                headers=headers
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Telemetry failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Telemetry error: {e}")
            return False
    
    def check_for_updates(self):
        """
        Check for firmware updates from the cloud
        
        Returns:
            dict or False: Update information if available, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send update check request
            response = self.session.get(
                f"{API_ENDPOINT}{DEVICE_API_PATH}/updates?device_id={self.device_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("update_available", False):
                    return data
                
                return False
            else:
                print(f"Update check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Update check error: {e}")
            return False
    
    def get_pending_commands(self):
        """
        Get any pending commands from the cloud
        
        Returns:
            list or False: List of commands if available, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send command check request
            response = self.session.get(
                f"{API_ENDPOINT}{COMMANDS_API_PATH}?device_id={self.device_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                commands = data.get("commands", [])
                
                if commands:
                    print(f"Retrieved {len(commands)} pending commands")
                    return commands
                
                return []
            else:
                print(f"Command check failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Command check error: {e}")
            return False
    
    def send_command_response(self, command_id, status, result=None):
        """
        Send a command execution response to the cloud
        
        Args:
            command_id: ID of the command being responded to
            status: Status of the command execution (success, failure)
            result: Optional result data from the command
            
        Returns:
            bool: True if response was sent successfully, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Build response data
            response_data = {
                "device_id": self.device_id,
                "command_id": command_id,
                "status": status
            }
            
            # Add result data if provided
            if result:
                response_data["result"] = result
            
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send command response
            response = self.session.post(
                f"{API_ENDPOINT}{COMMANDS_API_PATH}/response",
                json=response_data,
                headers=headers
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Command response failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Command response error: {e}")
            return False
    
    def upload_image(self, image_data, metadata=None):
        """
        Upload an image to the cloud
        
        Args:
            image_data: Binary image data to upload
            metadata: Optional metadata about the image
            
        Returns:
            dict or False: Response data if successful, False otherwise
        """
        if not self.session or not self.connected:
            return False
            
        try:
            # Encode image data as base64
            image_base64 = binascii.b2a_base64(image_data).decode('utf-8')
            
            # Build upload data
            upload_data = {
                "device_id": self.device_id,
                "timestamp": time.time(),
                "image": image_base64,
                "format": "jpeg"  # Adjust based on your image format
            }
            
            # Add metadata if provided
            if metadata:
                upload_data["metadata"] = metadata
            
            # Add the API key to headers
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            # Send image upload request
            response = self.session.post(
                f"{API_ENDPOINT}{DEVICE_API_PATH}/images",
                json=upload_data,
                headers=headers
            )
            
            if response.status_code in (200, 201):
                return response.json()
            else:
                print(f"Image upload failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.last_error = str(e)
            print(f"Image upload error: {e}")
            return False
    
    def periodic_update(self):
        """
        Perform periodic updates, including heartbeat and command checking
        
        Returns:
            list or None: Any pending commands if available
        """
        current_time = time.monotonic()
        
        # Check if it's time to send a heartbeat
        if current_time - self.last_heartbeat >= HEARTBEAT_INTERVAL:
            heartbeat_result = self.send_heartbeat()
            
            # If heartbeat returned commands, return them
            if isinstance(heartbeat_result, list):
                return heartbeat_result
        
        # Check for pending commands
        return self.get_pending_commands()