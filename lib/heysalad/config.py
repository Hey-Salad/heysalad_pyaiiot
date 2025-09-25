"""
Configuration settings for HeySalad Camera Server
"""

# Application states
STATE_IDLE = 0
STATE_STREAMING = 1
STATE_ERROR = 2

# Version information
VERSION = "1.0.0"

# Image paths for different states
STANDARD_IMAGE = "HSK-STANDARD.bmp"
SPEEDY_IMAGE = "HSK-SPEEDY.bmp"
SHOCKED_IMAGE = "HSK-SHOCKED.bmp"

# WiFi Networks configuration
WIFI_NETWORKS = [
    {"ssid": "HeySalad_02", "password": "---------"},
    {"ssid": "iPhone von Chilu", "password": "--------"},
    {"ssid": "VM7464351", "password": "-----------"}
]

# Camera Configuration
CAMERA_CONFIG = {
    'data_pins': 'board.CAM_DATA',
    'external_clock_pin': 'board.CAM_XCLK',
    'pixel_clock_pin': 'board.CAM_PCLK',
    'vsync_pin': 'board.CAM_VSYNC',
    'href_pin': 'board.CAM_HREF',
    'pixel_format': 'espcamera.PixelFormat.RGB565',
    'frame_size': 'espcamera.FrameSize.R240X240',
    'external_clock_frequency': 20_000_000,
    'framebuffer_count': 2,
    'grab_mode': 'espcamera.GrabMode.WHEN_EMPTY'
}

# Display Configuration
DISPLAY_CONFIG = {
    'width': 240,
    'height': 240,
    'command_pin': 'board.D3',
    'chip_select_pin': 'board.D1',
    'clock_pin': 'board.SCK',
    'mosi_pin': 'board.MOSI'
}

# Streaming Configuration
STREAMING_CONFIG = {
    'frame_interval': 0.1,  # 10 FPS
    'max_websocket_clients': 5
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Error Handling Configuration
ERROR_CONFIG = {
    'max_reconnect_attempts': 3,
    'reconnect_delay': 5  # seconds
}

# HTML Template for web interface (in case index.html is not found)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HeySalad Camera Stream</title>
    <style>
        :root {
            --primary-color: #ed4c4c; /* Cherry Red */
            --secondary-color: #faa09a; /* Peach */
            --tertiary-color: #ffd0cd; /* Light Peach */
            --bg-color: #ffffff; /* White */
            --card-color: #FFFFFF;
            --text-color: #333333;
            --error-color: #ed4c4c; /* Using Cherry Red for errors too */
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        
        .container {
            max-width: 360px;
            width: 95%;
            margin: 20px auto;
        }
        
        header {
            text-align: center;
            margin-bottom: 20px;
        }
        
        h1 {
            color: var(--primary-color);
        }
        
        .stream-container {
            position: relative;
            width: 100%;
            max-width: 300px;
            height: 0;
            padding-bottom: 100%;
            background-color: #000;
            border-radius: 50%;
            overflow: hidden;
            margin: 0 auto;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        }
        
        #camera-feed {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .status {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 20px 0;
            padding: 10px;
            border-radius: 5px;
            background-color: var(--tertiary-color);
            color: var(--primary-color);
            font-weight: bold;
        }
        
        .status.connected {
            background-color: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
        }
        
        .status.disconnected {
            background-color: rgba(244, 67, 54, 0.2);
            color: var(--error-color);
        }
        
        .controls {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }
        
        .logo {
            width: 100px;
            height: 100px;
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
        }
        
        .btn {
            background-color: var(--tertiary-color);
            color: var(--primary-color);
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .btn svg {
            width: 30px;
            height: 30px;
            fill: currentColor;
        }
        
        .btn:hover {
            background-color: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        
        .btn.primary {
            background-color: var(--primary-color);
            color: white;
        }
        
        .btn.primary:hover {
            background-color: var(--secondary-color);
        }
        
        .btn.active {
            background-color: var(--secondary-color);
            border: 2px solid var(--primary-color);
            transform: scale(1.05);
        }
        
        .info-panel {
            background-color: var(--card-color);
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            max-width: 300px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .info-panel h3 {
            margin-top: 0;
            color: var(--primary-color);
        }
        
        #cpu-temp {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-container">
                <div class="logo" id="heysalad-logo"></div>
            </div>
            <h1>HeySalad<sup>®</sup> Camera Stream</h1>
            <p>Live stream from ESP32-S3 with GC9A01 round display</p>
        </header>
        
        <div class="stream-container">
            <canvas id="camera-feed" width="240" height="240"></canvas>
        </div>
        
        <div id="connection-status" class="status">Connecting to websocket...</div>
        
        <div class="controls">
            <button id="start-stream-btn" class="btn primary">
                <svg viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            </button>
            <button id="stop-stream-btn" class="btn">
                <svg viewBox="0 0 24 24">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                </svg>
            </button>
            <button id="refresh-btn" class="btn">
                <svg viewBox="0 0 24 24">
                    <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 9h7V2l-2.35 4.35z"/>
                </svg>
            </button>
        </div>
        
        <div class="info-panel">
            <h3>Device Information</h3>
            <p>CPU Temperature: <span id="cpu-temp">-</span>°C</p>
            <p>Memory Available: <span id="memory-available">-</span> bytes</p>
        </div>
    </div>

    <script>
        // DOM elements
        const canvas = document.getElementById('camera-feed');
        const ctx = canvas.getContext('2d');
        const statusEl = document.getElementById('connection-status');
        const cpuTempEl = document.getElementById('cpu-temp');
        const memoryEl = document.getElementById('memory-available');
        const refreshBtn = document.getElementById('refresh-btn');
        const startStreamBtn = document.getElementById('start-stream-btn');
        const stopStreamBtn = document.getElementById('stop-stream-btn');
        const heySaladLogo = document.getElementById('heysalad-logo');
        
        // WebSocket variables
        let ws = null;
        let connected = false;
        let reconnectAttempts = 0;
        const MAX_RECONNECT_ATTEMPTS = 5;
        
        // Connect to WebSocket
        function connectWebSocket() {
            // Close existing connection if any
            if (ws) {
                ws.close();
            }
            
            // Update status
            statusEl.className = 'status';
            statusEl.textContent = 'Connecting to websocket...';
            
            // Create new WebSocket connection
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            // WebSocket event handlers
            ws.onopen = () => {
                connected = true;
                reconnectAttempts = 0;
                statusEl.className = 'status connected';
                statusEl.textContent = 'Connected to camera stream';
            };
            
            ws.onclose = () => {
                connected = false;
                statusEl.className = 'status disconnected';
                statusEl.textContent = 'Disconnected from camera stream';
                
                // Attempt to reconnect
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    reconnectAttempts++;
                    setTimeout(connectWebSocket, 3000);
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                statusEl.className = 'status disconnected';
                statusEl.textContent = 'Connection error';
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    // Handle different message types
                    if (data.type === 'frame') {
                        // Handle camera frame
                        drawFrame(data.width, data.height, data.format, data.data);
                    } else if (data.type === 'info') {
                        // Update device information
                        if (data.cpu_temp) {
                            cpuTempEl.textContent = data.cpu_temp.toFixed(1);
                        }
                        if (data.memory) {
                            memoryEl.textContent = data.memory;
                        }
                        
                        // Update streaming status buttons
                        if (data.streaming) {
                            startStreamBtn.classList.add('active');
                            stopStreamBtn.classList.remove('active');
                        } else {
                            startStreamBtn.classList.remove('active');
                            stopStreamBtn.classList.add('active');
                        }
                    } else if (data.type === 'command_response') {
                        console.log('Command response:', data);
                        
                        // Update streaming status buttons based on response
                        if (data.streaming !== undefined) {
                            if (data.streaming) {
                                startStreamBtn.classList.add('active');
                                stopStreamBtn.classList.remove('active');
                            } else {
                                startStreamBtn.classList.remove('active');
                                stopStreamBtn.classList.add('active');
                            }
                        }
                    }
                } catch (error) {
                    console.error('Error processing message:', error);
                }
            };
        }
        
        // Draw frame on canvas
        function drawFrame(width, height, format, data) {
            if (format === 'rgb565') {
                // Convert binary RGB565 data to ImageData
                const imageData = new ImageData(width, height);
                const buffer = new Uint8Array(width * height * 4); // RGBA
                
                const binary = atob(data); // Base64 decode
                
                // Convert RGB565 to RGBA
                for (let i = 0; i < binary.length; i += 2) {
                    const idx = i / 2;
                    const pixelVal = (binary.charCodeAt(i) << 8) | binary.charCodeAt(i + 1);
                    
                    // RGB565: RRRRRGGG GGGBBBBB
                    const r = ((pixelVal >> 11) & 0x1F) << 3;
                    const g = ((pixelVal >> 5) & 0x3F) << 2;
                    const b = (pixelVal & 0x1F) << 3;
                    
                    const rgbaIdx = idx * 4;
                    buffer[rgbaIdx] = r;
                    buffer[rgbaIdx + 1] = g;
                    buffer[rgbaIdx + 2] = b;
                    buffer[rgbaIdx + 3] = 255; // Alpha
                }
                
                imageData.data.set(buffer);
                ctx.putImageData(imageData, 0, 0);
            }
        }
        
        // Initialize connection
        connectWebSocket();
        
        // Set logo background
        // We'll load the base64 encoded logo when the page loads
        fetch('/logo')
            .then(response => response.json())
            .then(data => {
                if (data && data.image) {
                    const imgFormat = data.format || 'jpeg';
                    heySaladLogo.style.backgroundImage = `url(data:image/${imgFormat};base64,${data.image})`;
                }
            })
            .catch(error => {
                console.error('Failed to load logo:', error);
                // Use a color as fallback
                heySaladLogo.style.backgroundColor = 'var(--primary-color)';
            });
        
        // Event listeners
        refreshBtn.addEventListener('click', () => {
            connectWebSocket();
        });
        
        startStreamBtn.addEventListener('click', () => {
            startStreamBtn.classList.add('active');
            stopStreamBtn.classList.remove('active');
            
            // Send command to start streaming
            if (ws && connected) {
                ws.send(JSON.stringify({ command: 'start_stream' }));
            } else {
                connectWebSocket();
                setTimeout(() => {
                    if (ws && connected) {
                        ws.send(JSON.stringify({ command: 'start_stream' }));
                    }
                }, 1000);
            }
        });
        
        stopStreamBtn.addEventListener('click', () => {
            stopStreamBtn.classList.add('active');
            startStreamBtn.classList.remove('active');
            
            // Send command to stop streaming
            if (ws && connected) {
                ws.send(JSON.stringify({ command: 'stop_stream' }));
            }
        });
        
        // Reconnect WebSocket when window gains focus
        window.addEventListener('focus', () => {
            if (!connected) {
                connectWebSocket();
            }
        });
    </script>
</body>
</html>"""

# Import any site-specific overrides, if they exist
try:
    from . import local_config
    locals().update({k: v for k, v in local_config.__dict__.items() 
                     if not k.startswith('_') and k.isupper()})
except ImportError:
    pass