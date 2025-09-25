"""Display module for HeySalad Camera Project"""

import board
import busio
import displayio
import gc9a01
import os
from . import config
from . import __init__ as heysalad

class HeySaladDisplay:
    """Manages the GC9A01 round display"""
    
    def __init__(self, config_settings=None):
        """
        Initialize the display
        
        :param config_settings: Optional dictionary to override default display configuration
        """
        print("Initializing display...")
        
        # Use provided config or default config
        self.display_config = config_settings or config.DISPLAY_CONFIG
        
        # Initialize display components
        self.display = None
        self.main_group = None
        self.display_bus = None
        
        # Display command constants
        self.CASET = 0x2A  # Column Address Set
        self.RASET = 0x2B  # Row Address Set
        self.RAMWR = 0x2C  # Memory Write
        
        # Potential asset directories
        self.asset_dirs = [
            os.path.join(os.path.dirname(__file__), "assets", "bmp"),
            os.path.join(os.path.dirname(__file__), "assets"),
            ".",
            "lib/heysalad/assets/bmp"
        ]
        
        # Try to set up the display
        try:
            self._setup_display()
        except Exception as e:
            print(f"Display initialization error: {e}")
    
    def _find_image(self, image_name):
        """
        Find an image in the predefined asset directories
        
        :param image_name: Name of the image file
        :return: Full path to the image or None
        """
        # Prefer BMP for display
        image_variants = [
            image_name,  # Original name
            image_name.replace('.png', '.bmp'),  # Convert PNG to BMP
            image_name.replace('.bmp', '.png')  # Fallback to PNG
        ]
        
        for directory in self.asset_dirs:
            for variant in image_variants:
                full_path = os.path.join(directory, variant)
                try:
                    if os.path.exists(full_path):
                        return full_path
                except Exception as e:
                    print(f"Error checking {full_path}: {e}")
        
        print(f"Could not find image: {image_name}")
        return None
    
    def _setup_display(self):
        """Internal method to set up the display hardware"""
        # Initialize SPI bus
        spi = busio.SPI(
            clock=board.SCK, 
            MOSI=board.MOSI
        )
        
        # Create display bus
        display_bus = displayio.FourWire(
            spi, 
            command=board.D3, 
            chip_select=board.D1
        )
        
        # Create the GC9A01 display
        self.display = gc9a01.GC9A01(
            display_bus, 
            width=self.display_config['width'], 
            height=self.display_config['height']
        )
        
        # Create main display group
        self.main_group = displayio.Group()
        self.display.root_group = self.main_group
        
        # Store display bus for low-level operations
        self.display_bus = display_bus
        
        print("Display initialized successfully")
    
    def load_image(self, image_name):
        """
        Load an image to the display
        
        :param image_name: Name of the image file
        """
        try:
            print(f"Loading image: {image_name}")
            
            # Clear the main group
            while len(self.main_group) > 0:
                self.main_group.pop()
            
            # Find the image
            image_path = self._find_image(image_name)
            
            if not image_path:
                # Create a fallback colored background
                color_bitmap = displayio.Bitmap(240, 240, 1)
                color_palette = displayio.Palette(1)
                
                # Choose fallback color based on image name
                if 'STANDARD' in image_name:
                    color_palette[0] = 0x00FF00  # Green
                elif 'SPEEDY' in image_name:
                    color_palette[0] = 0xFFFF00  # Yellow
                elif 'SHOCKED' in image_name:
                    color_palette[0] = 0xFF0000  # Red
                else:
                    color_palette[0] = 0x0000FF  # Blue
                
                bg_sprite = displayio.TileGrid(
                    color_bitmap, 
                    pixel_shader=color_palette
                )
                self.main_group.append(bg_sprite)
                print("Using fallback colored background")
                return
            
            # Load the image file
            with open(image_path, "rb") as image_file:
                bitmap = displayio.OnDiskBitmap(image_file)
                tile_grid = displayio.TileGrid(
                    bitmap, 
                    pixel_shader=displayio.ColorConverter()
                )
                
                # Add the TileGrid to the Group
                self.main_group.append(tile_grid)
                print(f"Image loaded: {image_path}")
            
        except Exception as e:
            print(f"Error loading image {image_name}: {e}")
    
    def direct_display_frame(self, frame):
        """
        Display camera frame directly using low-level commands
        
        :param frame: Camera frame data
        :return: Boolean indicating success of frame display
        """
        try:
            if self.display and self.display_bus:
                # Set the address window for the entire display
                import struct
                
                # Set column start/end
                self.display_bus.send(self.CASET, struct.pack(">HH", 0, 239))
                
                # Set row start/end  
                self.display_bus.send(self.RASET, struct.pack(">HH", 0, 239))
                
                # Send the camera frame directly to the display
                self.display_bus.send(self.RAMWR, frame)
                return True
            return False
        except Exception as e:
            print(f"Error displaying frame: {e}")
            return False