# utils/element_extraction.py

import os
import json
import cv2
import numpy as np
from PIL import Image
import google.generativeai as genai

class ElementExtractor:
    """Handles the extraction of UI elements from screenshots"""
    
    def __init__(self, model_name='gemini-2.5-pro-exp-03-25', template_dir="templates"):
        """Initialize the element extractor"""
        self.model_name = model_name
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)
        
        # Check if API is already configured
        self.model = genai.GenerativeModel(model_name)
    
    def identify_elements(self, screenshot, image_bytes):
        """Identify UI elements from a screenshot using Gemini Vision
        
        Args:
            screenshot: PIL Image of the screen
            image_bytes: Bytes representation of the image for API
            
        Returns:
            List of identified elements with their metadata
        """
        prompt = """
        Analyze this desktop screenshot and identify all clickable UI elements.
        For each element provide:
        - type: The type of UI element (icon, button, menu, checkbox, etc.)
        - name: A descriptive name that uniquely identifies this element
        - bounding_box: Coordinates as [x1, y1, x2, y2] where (x1,y1) is top-left and (x2,y2) is bottom-right
        - description: A brief description of what this element does or represents
        
        Format your response as a JSON array of objects, each with the properties listed above.
        Be precise with the bounding boxes to ensure they tightly contain only the specific element.
        """
        
        try:
            response = self.model.generate_content([prompt, {"mime_type": "image/png", "data": image_bytes}])
            
            # Extract JSON from response
            response_text = response.text
            # Find JSON part
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                elements = json.loads(json_str)
            else:
                print("Couldn't parse JSON response, using empty elements list")
                elements = []
            
            return elements
        except Exception as e:
            print(f"Error identifying elements: {e}")
            return []
    
    def extract_templates(self, screenshot, elements):
        """Extract template images for identified elements
        
        Args:
            screenshot: PIL Image of the screen
            elements: List of element dictionaries with bounding_box
            
        Returns:
            Dictionary mapping element names to template info
        """
        templates = {}
        
        for element in elements:
            if 'bounding_box' in element and 'name' in element:
                try:
                    # Get bounding box
                    x1, y1, x2, y2 = element['bounding_box']
                    
                    # Crop the element from screenshot
                    element_img = screenshot.crop((x1, y1, x2, y2))
                    
                    # Create a safe filename from element name
                    safe_name = ''.join(c if c.isalnum() else '_' for c in element['name']).lower()
                    filename = f"{self.template_dir}/{safe_name}.png"
                    
                    # Save the template image
                    element_img.save(filename)
                    
                    # Store template information
                    templates[element['name']] = {
                        'filename': filename,
                        'bounding_box': element['bounding_box'],
                        'type': element.get('type', 'unknown'),
                        'description': element.get('description', '')
                    }
                    
                except Exception as e:
                    print(f"Error extracting template for {element.get('name', 'unknown')}: {e}")
        
        return templates
    
    def find_templates_on_screen(self, screenshot, templates, confidence=0.8):
        """Find saved templates in the current screenshot
        
        Args:
            screenshot: PIL Image of current screen
            templates: Dictionary of template information
            confidence: Matching threshold (0-1)
            
        Returns:
            Dictionary of template names to locations
        """
        # Convert screenshot to OpenCV format
        screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screenshot_gray = cv2.cvtColor(screenshot_cv, cv2.COLOR_BGR2GRAY)
        
        locations = {}
        
        for name, template_info in templates.items():
            try:
                # Load template image
                template = cv2.imread(template_info['filename'], cv2.IMREAD_GRAYSCALE)
                
                if template is None:
                    print(f"Could not load template '{template_info['filename']}'")
                    continue
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                
                # Get locations where match value is above threshold
                locations_array = np.where(result >= confidence)
                for pt in zip(*locations_array[::-1]):  # Switch columns and rows
                    # Get template dimensions
                    h, w = template.shape
                    
                    # Calculate center of template
                    center_x = pt[0] + w//2
                    center_y = pt[1] + h//2
                    
                    # Store best match (first one found)
                    if name not in locations:
                        locations[name] = {
                            'center': (center_x, center_y),
                            'box': (pt[0], pt[1], pt[0] + w, pt[1] + h),
                            'confidence': float(result[pt[1], pt[0]])
                        }
                        break
            
            except Exception as e:
                print(f"Error finding template {name}: {e}")
        
        return locations
