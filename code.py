"""
HeySalad Camera Server for ESP32-S3 with GC9A01 Display
Main entry point for the application

This code initializes the camera, display, and web server components
and handles the interaction between them.
"""
import board
import busio
import displayio
import espcamera
import time
import gc
import json
import binascii
import struct
import socketpool
import wifi
import microcontroller
import traceback
from displayio import release_displays

# HTTP Server and WebSocket libraries
from adafruit_httpserver import Server, Request, Response, Websocket, GET

# Display-related imports
import gc9a01
try:
    from fourwire import FourWire
except ImportError:
    from displayio import FourWire

# Import configuration
from lib.heysalad import config

# Import cloud connection module if available
try:
    from lib.heysalad.cloud import CloudConnection
    cloud_available = True
    print("Cloud connection module found")
except ImportError:
    cloud_available = False
    print("Cloud connection module not found")

# Release any resources currently in use for the displays
release_displays()
print(f"Memory before init: {gc.mem_free()} bytes")

class HeySaladCameraServer:
    """Main application class for HeySalad Camera Web Server"""
    
    def __init__(self):
        """Initialize all system components"""
        print("Initializing HeySalad Camera Web Server...")
        
        # Initialize state variables
        self.current_state = config.STATE_IDLE
        self.error_message = None
        self.active_websockets = set()
        self.last_frame_time = time.monotonic()
        self.frame_interval = config.STREAMING_CONFIG['frame_interval']
        self.streaming_enabled = False  # Start with streaming disabled
        self.frame_count = 0
        self.last_fps_time = time.monotonic()
        self.last_info_time = time.monotonic()
        self.pool = None
        self.server = None
        
        # Cloud connectivity
        self.cloud = None
        self.cloud_connected = False
        self.api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
        self.last_cloud_check = time.monotonic()
        self.cloud_check_interval = 30  # Check every 30 seconds
        
        # Initialize hardware components
        self.init_display()
        self.init_camera()
        
        # Try to connect to WiFi and set up the server
        self.init_wifi()
        
        # Show standard image on startup
        self.load_image(config.STANDARD_IMAGE)
        print(f"Memory after init: {gc.mem_free()} bytes")
        print("HeySalad Camera Web Server initialized")
    
    def init_display(self):
        """Initialize the round GC9A01 display"""
        try:
            print("Initializing display...")
            # Initialize SPI bus
            spi = busio.SPI(
                clock=eval(config.DISPLAY_CONFIG['clock_pin']), 
                MOSI=eval(config.DISPLAY_CONFIG['mosi_pin'])
            )
            display_bus = FourWire(
                spi, 
                command=eval(config.DISPLAY_CONFIG['command_pin']), 
                chip_select=eval(config.DISPLAY_CONFIG['chip_select_pin'])
            )
            
            # Create the GC9A01 display with configured resolution
            self.display = gc9a01.GC9A01(
                display_bus, 
                width=config.DISPLAY_CONFIG['width'], 
                height=config.DISPLAY_CONFIG['height']
            )
            
            # Create main display group
            self.main_group = displayio.Group()
            self.display.root_group = self.main_group
            
            # GC9A01 display commands for direct frame updates
            self.CASET = 0x2A  # Column Address Set
            self.RASET = 0x2B  # Row Address Set
            self.RAMWR = 0x2C  # Memory Write
            self.display_bus = display_bus
            
            print("Display initialized successfully")
        except Exception as e:
            print(f"Display initialization error: {e}")
            print(traceback.format_exception(None, e, e.__traceback__))
            self.display = None
            self.main_group = None
    
    def init_camera(self):
        """Initialize the ESP32-S3 camera"""
        try:
            print("Setting up camera...")
            cam_i2c = busio.I2C(board.CAM_SCL, board.CAM_SDA)
            
            self.camera = espcamera.Camera(
                data_pins=eval(config.CAMERA_CONFIG['data_pins']),
                external_clock_pin=eval(config.CAMERA_CONFIG['external_clock_pin']),
                pixel_clock_pin=eval(config.CAMERA_CONFIG['pixel_clock_pin']),
                vsync_pin=eval(config.CAMERA_CONFIG['vsync_pin']),
                href_pin=eval(config.CAMERA_CONFIG['href_pin']),
                pixel_format=eval(config.CAMERA_CONFIG['pixel_format']),
                frame_size=eval(config.CAMERA_CONFIG['frame_size']),
                i2c=cam_i2c,
                external_clock_frequency=config.CAMERA_CONFIG['external_clock_frequency'],
                framebuffer_count=config.CAMERA_CONFIG['framebuffer_count'],
                grab_mode=eval(config.CAMERA_CONFIG['grab_mode'])
            )
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Camera initialization error: {e}")
            print(traceback.format_exception(None, e, e.__traceback__))
            self.camera = None
    
    def init_wifi(self):
        """Connect to WiFi network and set up the HTTP server"""
        print("Attempting to connect to WiFi...")
        connected = False
        
        for network in config.WIFI_NETWORKS:
            try:
                print(f"Trying to connect to '{network['ssid']}'...")
                wifi.radio.connect(network['ssid'], network['password'])
                
                # If we get here, connection was successful
                print(f"Connected to '{network['ssid']}'")
                connected = True
                print(f"IP address: {wifi.radio.ipv4_address}")
                
                # Initialize HTTP server
                self.init_server()
                break  # Exit the loop if we connect successfully
                
            except Exception as e:
                print(f"Failed to connect to '{network['ssid']}': {e}")
        
        if not connected:
            print("Could not connect to any WiFi network")
            self.show_error("WiFi connection failed")
    
    def connect_to_cloud(self):
        """Connect to the HeySalad Cloud service"""
        try:
            if not self.pool:
                print("Socket pool not initialized, cannot connect to cloud")
                return False
                
            if not cloud_available:
                print("Cloud module not available")
                return False
                
            print("Connecting to HeySalad Cloud...")
            # Initialize cloud connection if not already done
            if self.cloud is None and cloud_available:
                self.cloud = CloudConnection()
                
            if self.cloud.connect(self.pool, self.api_key):
                self.cloud_connected = True
                print("Connected to HeySalad Cloud")
                
                # Send initial telemetry
                self.send_cloud_telemetry()
                
                return True
            else:
                print(f"Cloud connection failed: {self.cloud.last_error if self.cloud else 'Cloud not initialized'}")
                return False
        except Exception as e:
            print(f"Cloud connection error: {e}")
            return False
    
    def send_cloud_telemetry(self):
        """Send telemetry data to the cloud"""
        if not self.cloud_connected or not self.cloud:
            return False
            
        try:
            # Gather telemetry data
            telemetry = {
                "cpu_temperature": microcontroller.cpu.temperature,
                "memory_free": gc.mem_free(),
                "streaming": self.streaming_enabled,
                "wifi_rssi": wifi.radio.ap_info.rssi if wifi.radio.ap_info else 0,
                "clients": len(self.active_websockets)
            }
            
            # Send telemetry to cloud
            return self.cloud.send_telemetry(telemetry)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
            return False

    def process_cloud_commands(self, commands):
        """Process commands received from the cloud"""
        if not commands or not self.cloud:
            return
            
        for command in commands:
            try:
                # Get command details
                command_id = command.get("id")
                command_type = command.get("type")
                command_params = command.get("params", {})
                
                print(f"Processing cloud command: {command_type}")
                
                # Handle different command types
                if command_type == "start_stream":
                    self.streaming_enabled = True
                    self.load_image(config.SPEEDY_IMAGE)
                    self.cloud.send_command_response(command_id, "success")
                    
                elif command_type == "stop_stream":
                    self.streaming_enabled = False
                    self.load_image(config.STANDARD_IMAGE)
                    self.cloud.send_command_response(command_id, "success")
                    
                elif command_type == "capture_image":
                    if self.camera:
                        frame = self.camera.take(1)
                        if frame:
                            metadata = {
                                "width": config.DISPLAY_CONFIG['width'],
                                "height": config.DISPLAY_CONFIG['height'],
                                "format": "rgb565"
                            }
                            # Upload the image to the cloud
                            result = self.cloud.upload_image(frame, metadata)
                            if result:
                                self.cloud.send_command_response(command_id, "success", result)
                            else:
                                self.cloud.send_command_response(command_id, "failure", {"error": "Image upload failed"})
                        else:
                            self.cloud.send_command_response(command_id, "failure", {"error": "Failed to capture image"})
                    else:
                        self.cloud.send_command_response(command_id, "failure", {"error": "Camera not initialized"})
                        
                elif command_type == "reboot":
                    # Send response before rebooting
                    self.cloud.send_command_response(command_id, "success")
                    # Reboot the device
                    microcontroller.reset()
                    
                else:
                    # Unknown command
                    self.cloud.send_command_response(command_id, "failure", {"error": f"Unknown command: {command_type}"})
                    
            except Exception as e:
                print(f"Error processing command: {e}")
                # Try to send failure response
                try:
                    if command_id and self.cloud:
                        self.cloud.send_command_response(command_id, "failure", {"error": str(e)})
                except:
                    pass
                    
    def check_cloud(self):
        """Periodically check for cloud commands and send heartbeats"""
        # Skip if cloud is not available
        if not cloud_available or not self.cloud:
            return
            
        current_time = time.monotonic()
        
        if current_time - self.last_cloud_check >= self.cloud_check_interval:
            self.last_cloud_check = current_time
            
            if not self.cloud_connected:
                # Try to reconnect
                self.connect_to_cloud()
                return
                
            try:
                # Perform periodic update
                commands = self.cloud.periodic_update()
                
                # Process any commands received
                if commands:
                    self.process_cloud_commands(commands)
                    
                # Send telemetry periodically
                if int(current_time) % 300 == 0:  # Every 5 minutes
                    self.send_cloud_telemetry()
                    
            except Exception as e:
                print(f"Cloud check error: {e}")
                # Mark as disconnected to trigger reconnection attempt
                self.cloud_connected = False
    
    def init_server(self):
        """Initialize the HTTP server with routes"""
        try:
            print("Setting up HTTP server...")
            # Create socket pool
            self.pool = socketpool.SocketPool(wifi.radio)
            
            # Initialize server
            self.server = Server(self.pool, debug=True)
            
            # Try to connect to cloud service if available
            if cloud_available:
                self.connect_to_cloud()
            
            # Configure routes
            @self.server.route("/")
            def index(request: Request):
                """Serve the main HTML page"""
                try:
                    with open("index.html", "r") as f:
                        return Response(request, f.read(), content_type="text/html")
                except OSError:
                    # If index.html can't be read, use the template
                    return Response(request, config.HTML_TEMPLATE, content_type="text/html")
            
            @self.server.route("/ws", GET)
            def websocket_handler(request: Request):
                """Handle WebSocket connections for streaming camera data"""
                try:
                    websocket = Websocket(request)
                    self.active_websockets.add(websocket)
                    print(f"New WebSocket client connected. Total: {len(self.active_websockets)}")
                    return websocket
                except Exception as e:
                    print(f"WebSocket connection error: {e}")
                    return Response(request, f"WebSocket error: {str(e)}", content_type="text/plain")
            
            @self.server.route("/info", GET)
            def info_handler(request: Request):
                """Return device information as JSON"""
                info = {
                    "type": "info",
                    "cpu_temp": microcontroller.cpu.temperature,
                    "memory": gc.mem_free(),
                    "device": "ESP32-S3",
                    "version": config.VERSION,
                    "streaming": self.streaming_enabled,
                    "cloud_connected": self.cloud_connected
                }
                return Response(request, json.dumps(info), content_type="application/json")
            
            @self.server.route("/logo", GET)
            def logo_handler(request: Request):
                """Return the logo as base64 encoded image"""
                try:
                    # First try JPG logo
                    try:
                        with open("HeySalad_Launchericon.jpg", "rb") as f:
                            logo_data = f.read()
                        
                        # Convert to base64
                        logo_base64 = binascii.b2a_base64(logo_data).decode('ascii').strip()
                        return Response(request, json.dumps({"image": logo_base64, "format": "jpeg"}), content_type="application/json")
                        
                    except OSError:
                        # Try PNG if JPG fails
                        try:
                            with open("HSK-STANDARD.png", "rb") as f:
                                logo_data = f.read()
                            
                            # Convert to base64
                            logo_base64 = binascii.b2a_base64(logo_data).decode('ascii').strip()
                            return Response(request, json.dumps({"image": logo_base64, "format": "png"}), content_type="application/json")
                                
                        except OSError:
                            # Fall back to BMP if both fail
                            print("JPG and PNG logos failed, using BMP fallback")
                            with open(config.SPEEDY_IMAGE, "rb") as f:
                                logo_data = f.read()
                            
                            # Convert to base64
                            logo_base64 = binascii.b2a_base64(logo_data).decode('ascii').strip()
                            
                            # Return as JSON
                            return Response(request, json.dumps({"image": logo_base64, "format": "bmp"}), content_type="application/json")
                        
                except Exception as e:
                    print(f"Error serving logo: {e}")
                    return Response(request, json.dumps({"error": str(e)}), content_type="application/json")
            
            @self.server.route("/favicon", GET)
            def favicon_handler(request: Request):
                """Serve the favicon image"""
                try:
                    # Use the .ico file as favicon
                    favicon_file = "HeySalad_Launchericon.ico"
                    with open(favicon_file, "rb") as f:
                        favicon_data = f.read()
                    
                    return Response(request, favicon_data, content_type="image/x-icon")
                except OSError:
                    # If .ico fails, try .jpg
                    try:
                        favicon_file = "HeySalad_Launchericon.jpg"
                        with open(favicon_file, "rb") as f:
                            favicon_data = f.read()
                        
                        return Response(request, favicon_data, content_type="image/jpeg")
                    except OSError:
                        # Try PNG if JPG fails
                        try:
                            fallback_file = "HSK-STANDARD.png"
                            with open(fallback_file, "rb") as f:
                                fallback_data = f.read()
                            return Response(request, fallback_data, content_type="image/png")
                        except Exception as e2:
                            print(f"Error serving fallback favicon: {e2}")
                            # Return a 204 No Content response if all files not found
                            return Response(request, "", status=204)
            
            # Add cloud status endpoint
            @self.server.route("/cloud/status", GET)
            def cloud_status_handler(request: Request):
                """Return cloud connection status"""
                status = {
                    "connected": self.cloud_connected,
                    "available": cloud_available,
                    "device_id": self.cloud.device_id if self.cloud else "Not available",
                    "last_error": self.cloud.last_error if self.cloud else None,
                    "last_heartbeat": time.monotonic() - self.cloud.last_heartbeat if self.cloud and self.cloud.last_heartbeat else None
                }
                return Response(request, json.dumps(status), content_type="application/json")
            
            # Start the server
            print(f"Starting server on http://{wifi.radio.ipv4_address}")
            self.server.start(str(wifi.radio.ipv4_address))
            self.current_state = config.STATE_STREAMING
            
            # Show success on display
            self.load_image(config.SPEEDY_IMAGE)
            time.sleep(1)
            self.load_image(config.STANDARD_IMAGE)
            
            print("HTTP server started successfully")
        except Exception as e:
            print(f"Server initialization error: {e}")
            print(traceback.format_exception(None, e, e.__traceback__))
            self.server = None
            self.show_error(f"Server initialization failed: {e}")
    
    def load_image(self, image_path):
        """Load an image to the display"""
        if self.display is None or self.main_group is None:
            print("Cannot load image: Display not initialized")
            return
            
        try:
            print(f"Loading image: {image_path}")
            # Clear the main group
            while len(self.main_group) > 0:
                self.main_group.pop()
            
            # Load the BMP file
            try:
                image_file = open(image_path, "rb")
                bitmap = displayio.OnDiskBitmap(image_file)
                tile_grid = displayio.TileGrid(bitmap, pixel_shader=displayio.ColorConverter())
                
                # Add the TileGrid to the Group
                self.main_group.append(tile_grid)
                print(f"Image loaded: {image_path}")
            except OSError as e:
                print(f"Image file not found: {e}")
                # Create a colored background as fallback
                color_bitmap = displayio.Bitmap(
                    config.DISPLAY_CONFIG['width'], 
                    config.DISPLAY_CONFIG['height'], 
                    1
                )
                color_palette = displayio.Palette(1)
                if image_path == config.STANDARD_IMAGE:
                    color_palette[0] = 0x00FF00  # Green
                elif image_path == config.SPEEDY_IMAGE:
                    color_palette[0] = 0xFFFF00  # Yellow
                else:
                    color_palette[0] = 0xFF0000  # Red
                bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette)
                self.main_group.append(bg_sprite)
                print("Using fallback colored background")
                
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
    
    def show_error(self, message):
        """Display error state"""
        print(f"ERROR: {message}")
        self.current_state = config.STATE_ERROR
        self.error_message = message
        try:
            self.load_image(config.SHOCKED_IMAGE)
            time.sleep(3)  # Show error face for 3 seconds
            self.load_image(config.STANDARD_IMAGE)
        except Exception as e:
            print(f"Error displaying error state: {e}")
        self.current_state = config.STATE_IDLE
    
    def direct_display_frame(self, frame):
        """Display camera frame directly to the display using low-level commands"""
        if self.display is None or self.display_bus is None:
            return False
            
        try:
            # Set the address window for the entire display
            width = config.DISPLAY_CONFIG['width']
            height = config.DISPLAY_CONFIG['height']
            self.display_bus.send(self.CASET, struct.pack(">HH", 0, width - 1))  # Column start/end
            self.display_bus.send(self.RASET, struct.pack(">HH", 0, height - 1))  # Row start/end
            
            # Send the camera frame directly to the display
            self.display_bus.send(self.RAMWR, frame)
            return True
        except Exception as e:
            print(f"Error displaying frame: {e}")
            return False
    
    def broadcast_to_websockets(self, message):
        """Send a message to all connected WebSocket clients"""
        # Create a copy of the set to avoid "Set changed size during iteration" errors
        websockets = set(self.active_websockets)
        closed_sockets = set()
        
        for websocket in websockets:
            try:
                websocket.send_message(message)
            except Exception as e:
                print(f"Error sending to websocket: {e}")
                # Mark this websocket for removal
                closed_sockets.add(websocket)
        
        # Remove closed websockets
        self.active_websockets -= closed_sockets
        
        # If any were removed, log it
        if closed_sockets:
            print(f"Removed {len(closed_sockets)} closed WebSocket connections. {len(self.active_websockets)} remaining.")
    
    def process_websocket_messages(self):
        """Process any incoming WebSocket messages"""
        # Skip if no websockets are active
        if not self.active_websockets:
            return
            
        # Make a copy to avoid modifying the set during iteration
        websockets = set(self.active_websockets)
        closed_websockets = set()
        
        for websocket in websockets:
            try:
                message = websocket.receive(fail_silently=True)
                if message:
                    try:
                        print(f"Received WebSocket message: {message}")
                        data = json.loads(message)
                        
                        # Handle commands
                        if "command" in data:
                            command = data["command"]
                            
                            if command == "start_stream":
                                print("Starting camera stream")
                                self.streaming_enabled = True
                                self.load_image(config.SPEEDY_IMAGE)
                                
                                # Respond to the client
                                response = {
                                    "type": "command_response",
                                    "command": "start_stream",
                                    "success": True,
                                    "streaming": True
                                }
                                websocket.send_message(json.dumps(response))
                                
                            elif command == "stop_stream":
                                print("Stopping camera stream")
                                self.streaming_enabled = False
                                self.load_image(config.STANDARD_IMAGE)
                                
                                # Respond to the client
                                response = {
                                    "type": "command_response",
                                    "command": "stop_stream",
                                    "success": True,
                                    "streaming": False
                                }
                                websocket.send_message(json.dumps(response))
                                
                            else:
                                print(f"Unknown command: {command}")
                                # Respond with error
                                response = {
                                    "type": "error",
                                    "message": f"Unknown command: {command}"
                                }
                                websocket.send_message(json.dumps(response))
                                
                    except json.JSONDecodeError:
                        print(f"Invalid JSON in WebSocket message: {message}")
                    except Exception as e:
                        print(f"Error processing WebSocket message: {e}")
                        closed_websockets.add(websocket)
            except Exception as e:
                print(f"Error receiving from WebSocket: {e}")
                closed_websockets.add(websocket)
        
        # Remove any closed websockets
        if closed_websockets:
            self.active_websockets -= closed_websockets
            print(f"Removed {len(closed_websockets)} problematic websockets. {len(self.active_websockets)} remaining.")
    
    def capture_and_broadcast_frame(self):
        """Capture a frame and broadcast it to all connected clients"""
        if not self.camera or not self.streaming_enabled:
            return False
            
        try:
            # Only proceed if we have websocket clients
            if not self.active_websockets:
                return False
                
            # Capture frame
            frame = self.camera.take(1)
            
            if not frame:
                print("Failed to capture frame")
                return False
            
            # Display the frame locally on the round display
            self.direct_display_frame(frame)
            
            # Convert frame to base64 for WebSocket transmission
            frame_base64 = binascii.b2a_base64(frame).decode('ascii').strip()
            
            # Create frame message
            frame_message = {
                "type": "frame",
                "width": config.DISPLAY_CONFIG['width'],
                "height": config.DISPLAY_CONFIG['height'],
                "format": "rgb565",
                "data": frame_base64
            }
            
            # Broadcast the frame to all WebSocket clients
            self.broadcast_to_websockets(json.dumps(frame_message))
            
            # Count frame for FPS calculation
            self.frame_count += 1
            
            # Periodically upload a frame to the cloud for monitoring
            current_time = time.monotonic()
            if self.cloud_connected and self.cloud and int(current_time) % 300 == 0:  # Every 5 minutes
                try:
                    metadata = {
                        "width": config.DISPLAY_CONFIG['width'],
                        "height": config.DISPLAY_CONFIG['height'],
                        "format": "rgb565",
                        "reason": "periodic"
                    }
                    self.cloud.upload_image(frame, metadata)
                except Exception as e:
                    print(f"Error uploading periodic image: {e}")
            
            return True
            
        except Exception as e:
            print(f"Frame capture/broadcast error: {e}")
            return False
    
    def broadcast_device_info(self):
        """Broadcast device information to all connected clients"""
        if not self.active_websockets:
            return
            
        info = {
            "type": "info",
            "cpu_temp": microcontroller.cpu.temperature,
            "memory": gc.mem_free(),
            "device": "ESP32-S3",
            "version": config.VERSION,
            "streaming": self.streaming_enabled,
            "cloud_connected": self.cloud_connected
        }
        self.broadcast_to_websockets(json.dumps(info))
    
    def run(self):
        """Main application loop"""
        print("Running HeySalad Camera Server main loop...")
        
        while True:
            try:
                # Poll the HTTP server for client requests if it's initialized
                if self.server:
                    self.server.poll()
                
                # Process WebSocket messages
                self.process_websocket_messages()
                
                # Check cloud for commands if cloud is available
                if cloud_available:
                    self.check_cloud()
                
                current_time = time.monotonic()
                
                # Stream camera frames if enabled
                if self.streaming_enabled and (current_time - self.last_frame_time) >= self.frame_interval:
                    self.capture_and_broadcast_frame()
                    self.last_frame_time = current_time
                
                # Calculate and print FPS periodically
                if self.frame_count >= 30:
                    fps = 30 / (current_time - self.last_fps_time)
                    print(f"{fps:.1f} FPS, {len(self.active_websockets)} clients, {gc.mem_free()} bytes free, CPU: {microcontroller.cpu.temperature:.1f}°C")
                    self.frame_count = 0
                    self.last_fps_time = current_time
                
                # Broadcast device info periodically (every 5 seconds)
                if current_time - self.last_info_time >= 5:
                    self.broadcast_device_info()
                    self.last_info_time = current_time
                
                # Run garbage collection periodically
                if int(current_time) % 30 == 0:  # Every 30 seconds
                    gc.collect()
                
                # Add a small delay to prevent tight loop
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                print(traceback.format_exception(None, e, e.__traceback__))
                self.show_error(str(e))
                
                # Sleep a bit longer after an error
                time.sleep(1)

# Create and run the camera server
if __name__ == "__main__":
    try:
        print("Starting HeySalad Camera Web Server...")
        server = HeySaladCameraServer()
        server.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        print(traceback.format_exception(None, e, e.__traceback__))
        # Wait before potential restart
        time.sleep(5)