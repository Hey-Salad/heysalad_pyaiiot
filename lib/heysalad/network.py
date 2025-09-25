"""Network management module for HeySalad Camera Project"""

import time
import wifi
import socketpool
from . import __init__ as heysalad

class NetworkManager:
    """Manages WiFi connection and network-related functionalities"""
    
    def __init__(self, networks=None):
        """
        Initialize network manager
        
        :param networks: List of network configurations (optional)
        """
        # Use provided networks or default from __init__
        self.networks = networks or heysalad.WIFI_NETWORKS
        
        # Connection status
        self.connected = False
        self.current_network = None
        self.ip_address = None
        
        # Attempt to connect to WiFi
        self.connect()
    
    def connect(self, max_attempts=3):
        """
        Connect to WiFi network
        
        :param max_attempts: Maximum number of connection attempts per network
        :return: Boolean indicating successful connection
        """
        print("Attempting to connect to WiFi...")
        
        for network in self.networks:
            attempts = 0
            while attempts < max_attempts:
                try:
                    print(f"Trying to connect to '{network['ssid']}'...")
                    
                    # Disconnect from any existing connection
                    try:
                        wifi.radio.stop_station()
                    except:
                        pass
                    
                    # Attempt connection
                    wifi.radio.connect(network['ssid'], network['password'])
                    
                    # If connection is successful
                    self.connected = True
                    self.current_network = network
                    self.ip_address = str(wifi.radio.ipv4_address)
                    
                    print(f"Connected to '{network['ssid']}'")
                    print(f"IP address: {self.ip_address}")
                    
                    return True
                
                except Exception as e:
                    print(f"Failed to connect to '{network['ssid']}': {e}")
                    attempts += 1
                    time.sleep(2)  # Wait before retrying
        
        # If no network connection was successful
        print("Could not connect to any WiFi network")
        self.connected = False
        return False
    
    def create_socket_pool(self):
        """
        Create a socket pool for network communications
        
        :return: socketpool.SocketPool instance
        """
        if not self.connected:
            raise RuntimeError("No network connection available")
        
        return socketpool.SocketPool(wifi.radio)
    
    def get_ip_address(self):
        """
        Get the current IP address
        
        :return: IP address as string or None
        """
        return self.ip_address
    
    def disconnect(self):
        """
        Disconnect from the current WiFi network
        """
        try:
            wifi.radio.stop_station()
            self.connected = False
            self.current_network = None
            self.ip_address = None
            print("WiFi disconnected")
        except Exception as e:
            print(f"Error disconnecting from WiFi: {e}")
    
    def is_connected(self):
        """
        Check if currently connected to a WiFi network
        
        :return: Boolean indicating network connection status
        """
        return self.connected