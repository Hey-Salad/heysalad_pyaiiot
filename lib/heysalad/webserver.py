"""WebSocket management module for HeySalad Camera Project"""

import json
import time
import gc

class WebSocketManager:
    """Manages WebSocket connections and messaging"""
    
    def __init__(self, max_clients=5):
        """
        Initialize WebSocket manager
        
        :param max_clients: Maximum number of concurrent WebSocket clients
        """
        self.active_websockets = set()
        self.max_clients = max_clients
        self.last_info_broadcast = 0
        self.info_broadcast_interval = 5  # seconds
    
    def add_client(self, websocket):
        """
        Add a new WebSocket client
        
        :param websocket: WebSocket connection to add
        :return: Boolean indicating successful addition
        """
        if len(self.active_websockets) >= self.max_clients:
            print("Maximum WebSocket clients reached")
            return False
        
        self.active_websockets.add(websocket)
        print(f"New WebSocket client connected. Total: {len(self.active_websockets)}")
        return True
    
    def remove_client(self, websocket):
        """
        Remove a WebSocket client
        
        :param websocket: WebSocket connection to remove
        """
        try:
            self.active_websockets.remove(websocket)
            print(f"WebSocket client disconnected. Remaining: {len(self.active_websockets)}")
        except KeyError:
            pass
    
    def broadcast_message(self, message, exclude_websocket=None):
        """
        Broadcast a message to all connected clients
        
        :param message: Message to broadcast
        :param exclude_websocket: Optional WebSocket to exclude from broadcast
        :return: Number of clients message was sent to
        """
        # Create a copy of the set to avoid modification during iteration
        websockets = set(self.active_websockets)
        sent_count = 0
        closed_sockets = set()
        
        for websocket in websockets:
            # Skip the excluded WebSocket if specified
            if websocket == exclude_websocket:
                continue
            
            try:
                websocket.send_message(json.dumps(message))
                sent_count += 1
            except Exception as e:
                print(f"Error sending message to websocket: {e}")
                closed_sockets.add(websocket)
        
        # Remove closed websockets
        self.active_websockets -= closed_sockets
        
        # Log removals if any
        if closed_sockets:
            print(f"Removed {len(closed_sockets)} closed WebSocket connections. {len(self.active_websockets)} remaining.")
        
        return sent_count
    
    def handle_websocket_message(self, websocket, message, device_manager):
        """
        Handle incoming WebSocket messages
        
        :param websocket: WebSocket connection
        :param message: Received message
        :param device_manager: Device management object with methods to handle commands
        """
        try:
            # Parse the message as JSON
            data = json.loads(message)
            
            # Check for commands
            if "command" in data:
                command = data["command"]
                
                # Delegate command handling to device manager
                if command == "start_stream":
                    device_manager.start_streaming()
                elif command == "stop_stream":
                    device_manager.stop_streaming()
                else:
                    # Unknown command
                    error_response = {
                        "type": "error",
                        "message": f"Unknown command: {command}"
                    }
                    websocket.send_message(json.dumps(error_response))
        
        except Exception as e:
            print(f"Error handling WebSocket message: {e}")
            try:
                error_response = {
                    "type": "error",
                    "message": f"Error processing command: {str(e)}"
                }
                websocket.send_message(json.dumps(error_response))
            except:
                pass
    
    def periodic_broadcast(self, device_manager):
        """
        Periodically broadcast device information
        
        :param device_manager: Device management object to get current info
        """
        current_time = time.monotonic()
        
        # Check if it's time to broadcast info
        if current_time - self.last_info_broadcast >= self.info_broadcast_interval:
            # Get current device info
            info_data = device_manager.get_device_info()
            
            # Broadcast to all clients
            self.broadcast_message(info_data)
            
            # Update last broadcast time
            self.last_info_broadcast = current_time
            
            # Optional: Run garbage collection
            gc.collect()