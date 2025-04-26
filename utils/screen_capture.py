# utils/screen_capture.py

import io
import time
from PIL import ImageGrab, Image
import numpy as np
import cv2

class ScreenCapture:
    """Handles screen capture functionality with various options"""
    
    def __init__(self, screenshot_dir="screenshots"):
        """Initialize the screen capture module"""
        import os
        self.screenshot_dir = screenshot_dir
        os.makedirs(screenshot_dir, exist_ok=True)
    
    def capture_full_screen(self):
        """Capture the entire screen as a PIL Image"""
        return ImageGrab.grab()
    
    def capture_region(self, bbox):
        """Capture a specific region of the screen
        
        Args:
            bbox: Tuple of (x1, y1, x2, y2) coordinates
        
        Returns:
            PIL Image of the specified region
        """
        return ImageGrab.grab(bbox=bbox)
    
    def capture_with_timestamp(self):
        """Capture screen with timestamp in filename"""
        screenshot = self.capture_full_screen()
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{self.screenshot_dir}/screenshot_{timestamp}.png"
        screenshot.save(filename)
        return screenshot, filename
    
    def capture_to_bytes(self, format="PNG"):
        """Capture screen and convert to bytes for API transmission"""
        screenshot = self.capture_full_screen()
        img_byte_arr = io.BytesIO()
        screenshot.save(img_byte_arr, format=format)
        img_byte_arr.seek(0)
        return screenshot, img_byte_arr.getvalue()
    
    def capture_to_cv2(self):
        """Capture screen and convert to OpenCV format (for processing)"""
        screenshot = self.capture_full_screen()
        # Convert PIL Image to CV2 format (numpy array)
        return screenshot, cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def compare_screenshots(self, image1, image2, threshold=0.95):
        """Compare two screenshots and return similarity score"""
        # Convert to grayscale and CV2 format if needed
        if isinstance(image1, Image.Image):
            image1 = cv2.cvtColor(np.array(image1), cv2.COLOR_RGB2GRAY)
        if isinstance(image2, Image.Image):
            image2 = cv2.cvtColor(np.array(image2), cv2.COLOR_RGB2GRAY)
        
        # Ensure same size
        if image1.shape != image2.shape:
            image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
        
        # Compare using structural similarity index
        try:
            from skimage.metrics import structural_similarity as ssim
            score, _ = ssim(image1, image2, full=True)
            return score
        except ImportError:
            # Fallback if skimage not available
            result = cv2.matchTemplate(image1, image2, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            return max_val
