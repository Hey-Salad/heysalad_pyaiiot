# HeySalad® Camera Server

A feature-rich ESP32-S3 camera streaming server with GC9A01 round display, WebSocket streaming, and cloud connectivity.

## 🌟 Features

- **Live Camera Streaming**: Real-time camera feed via WebSocket
- **Round Display**: 240x240 GC9A01 circular display integration
- **Web Interface**: Modern responsive web UI for camera control
- **Cloud Connectivity**: Optional HeySalad Cloud API integration
- **Multi-Network Support**: Automatic WiFi network selection
- **Device Monitoring**: CPU temperature, memory usage, and performance metrics
- **RESTful API**: Device information and control endpoints
- **Modular Architecture**: Clean, organized codebase with separate modules

## 🛠️ Hardware Requirements

- **ESP32-S3** with camera module (e.g., ESP32-S3-CAM)
- **GC9A01 Round Display** (240x240 pixels)
- **Camera Module** compatible with ESP32-S3
- **MicroSD Card** (optional, for image storage)

### Pin Configuration

| Component | Pin | Description |
|-----------|-----|-------------|
| Display SPI CLK | SCK | Display clock |
| Display SPI MOSI | MOSI | Display data |
| Display CS | D1 | Chip select |
| Display DC | D3 | Data/Command |
| Camera Data | CAM_DATA | Camera data pins |
| Camera Clock | CAM_XCLK | External clock |
| Camera I2C | CAM_SCL, CAM_SDA | Camera configuration |

## 📦 Installation

### Prerequisites

- **CircuitPython** 8.0+ on ESP32-S3
- Required CircuitPython libraries:
  - `adafruit_httpserver`
  - `adafruit_requests` (for cloud features)
  - `gc9a01`
  - `espcamera`

### Setup Steps

1. **Flash CircuitPython** to your ESP32-S3 device
2. **Install required libraries** in the `lib/` folder
3. **Copy project files** to the device root directory
4. **Configure WiFi** in `lib/heysalad/config.py`:
   ```python
   WIFI_NETWORKS = [
       {"ssid": "YourNetwork", "password": "YourPassword"},
       {"ssid": "BackupNetwork", "password": "BackupPassword"}
   ]
   ```
5. **Add display images** (BMP format recommended):
   - `HSK-STANDARD.bmp` - Default display
   - `HSK-SPEEDY.bmp` - Streaming indicator
   - `HSK-SHOCKED.bmp` - Error display

## 🚀 Usage

### Starting the Server

1. Power on the ESP32-S3 device
2. The device will automatically:
   - Connect to configured WiFi networks
   - Initialize camera and display
   - Start the web server
   - Display the local IP address

### Web Interface

Access the camera stream at: `http://[DEVICE_IP_ADDRESS]`

#### Available Controls:
- **▶️ Start Stream**: Begin camera streaming
- **⏸️ Stop Stream**: Stop camera streaming  
- **🔄 Refresh**: Reconnect to WebSocket

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/ws` | GET | WebSocket connection for streaming |
| `/info` | GET | Device information (JSON) |
| `/logo` | GET | Device logo (base64) |
| `/favicon` | GET | Favicon for web interface |
| `/cloud/status` | GET | Cloud connection status |

## 🏗️ Project Structure

```
heysalad-camera/
├── code.py                    # Main application entry point
├── index.html                 # Web interface (optional)
├── lib/heysalad/             # Core library modules
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration settings
│   ├── camera.py             # Camera management
│   ├── display.py            # Display management
│   ├── network.py            # Network utilities
│   ├── cloud.py              # Cloud connectivity
│   ├── websocket.py          # WebSocket management
│   └── webserver.py          # HTTP server utilities
├── assets/                   # Image assets
│   ├── HSK-STANDARD.bmp      # Default display image
│   ├── HSK-SPEEDY.bmp        # Streaming indicator
│   └── HSK-SHOCKED.bmp       # Error display
└── README.md                 # This file
```

## ⚙️ Configuration

### Camera Settings (`config.py`)

```python
CAMERA_CONFIG = {
    'pixel_format': 'espcamera.PixelFormat.RGB565',
    'frame_size': 'espcamera.FrameSize.R240X240',
    'external_clock_frequency': 20_000_000,
    'framebuffer_count': 2,
}
```

### Display Settings

```python
DISPLAY_CONFIG = {
    'width': 240,
    'height': 240,
    'command_pin': 'board.D3',
    'chip_select_pin': 'board.D1',
}
```

### Streaming Settings

```python
STREAMING_CONFIG = {
    'frame_interval': 0.1,  # 10 FPS
    'max_websocket_clients': 5
}
```

## ☁️ Cloud Features

### HeySalad Cloud API

The project includes optional cloud connectivity to the HeySalad API:

- **Device Registration**: Automatic device registration
- **Remote Commands**: Receive commands from cloud dashboard
- **Telemetry**: Send device metrics and status
- **Image Upload**: Upload captured images to cloud storage
- **Remote Monitoring**: Monitor device health and performance

### Cloud Configuration

1. **Obtain API Key** from HeySalad Cloud Dashboard
2. **Update API Key** in `code.py`:
   ```python
   self.api_key = "YOUR_ACTUAL_API_KEY_HERE"
   ```
3. **Enable Cloud Module** by ensuring `cloud.py` is present

## 🎯 Performance

- **Frame Rate**: Up to 10 FPS (configurable)
- **Resolution**: 240x240 pixels (optimized for round display)
- **Memory Usage**: ~150KB free memory during operation
- **WebSocket Clients**: Supports up to 5 concurrent connections
- **Response Time**: <100ms for command processing

## 🔧 Troubleshooting

### Common Issues

1. **WiFi Connection Failed**
   - Check network credentials in `config.py`
   - Verify network is 2.4GHz (ESP32 limitation)
   - Check signal strength

2. **Camera Initialization Error**
   - Verify camera module connection
   - Check pin configuration in `config.py`
   - Ensure adequate power supply

3. **Display Not Working**
   - Verify GC9A01 connection and pin assignments
   - Check SPI bus configuration
   - Ensure display power supply

4. **WebSocket Connection Issues**
   - Check firewall settings
   - Verify correct IP address
   - Try refreshing the web page

### Debug Mode

Enable debug output by modifying the server initialization:

```python
self.server = Server(self.pool, debug=True)
```

## 🧪 Development

### Adding New Features

The modular architecture makes it easy to extend functionality:

1. **Camera Module** (`camera.py`): Camera-related features
2. **Display Module** (`display.py`): Display management
3. **Network Module** (`network.py`): WiFi and networking
4. **Cloud Module** (`cloud.py`): Cloud API integration
5. **WebSocket Module** (`websocket.py`): Real-time communication

### Testing

Test individual modules using CircuitPython REPL:

```python
from lib.heysalad.camera import HeySaladCamera
cam = HeySaladCamera()
frame = cam.capture_frame()
```

## 📊 Monitoring

### Device Metrics

The system provides real-time monitoring of:

- **CPU Temperature**: Thermal monitoring
- **Memory Usage**: Available RAM
- **Frame Rate**: Streaming performance  
- **Client Count**: Active WebSocket connections
- **Network Status**: WiFi signal strength

### Web Dashboard

Access real-time metrics via the web interface or API endpoints.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

Copyright (C) 2025-2026 HeySalad Inc.

Licensed under the GNU Affero General Public License v3.0 only (AGPL-3.0-only). See [LICENSE](LICENSE) and [NOTICE](NOTICE). If you run a modified version of this software to provide a network service, the AGPL requires you to offer its users the corresponding source code. Versions published before this change remain under their previous licence.

## 🆘 Support

- **Documentation**: Check the code comments and docstrings
- **Issues**: Report bugs and feature requests via GitHub issues
- **Community**: Join the HeySalad developer community

## 🔮 Future Enhancements

- [ ] Motion detection and alerts
- [ ] Time-lapse photography
- [ ] Multiple camera support
- [ ] Advanced image processing filters
- [ ] Mobile app integration
- [ ] Voice command support
- [ ] AI-powered object recognition

---

**HeySalad® Camera Server** - Bringing IoT camera streaming to the next level! 📸✨