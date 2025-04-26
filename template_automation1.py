import os
import time
import json
import pyautogui
import io
from PIL import Image, ImageGrab
import cv2
import numpy as np
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

# Configure Gemini API
genai.configure(api_key=api_key)
model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-pro-vision') # Use env var, fallback to default
model = genai.GenerativeModel(model_name)

# Ensure templates directory exists
os.makedirs('templates', exist_ok=True)

def screenshot_to_bytes(screenshot):
    """Convert PIL Image to bytes for API"""
    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

def capture_screen():
    """Capture the current screen"""
    return ImageGrab.grab()

def identify_desktop_elements(screenshot):
    """Use Gemini to identify elements on screen and return as JSON"""
    image_bytes = screenshot_to_bytes(screenshot)
    
    prompt = """
    Analyze this desktop screenshot and identify all clickable elements.
    For each element provide: 
    - type: The type of UI element (icon, button, menu, etc.)
    - name: A descriptive name that uniquely identifies this element
    - bounding_box: Coordinates as [x1, y1, x2, y2] where (x1,y1) is top-left and (x2,y2) is bottom-right
    - description: A brief description of what this element does
    
    Format your response as a JSON array of objects, each with the properties listed above.
    Be precise with the bounding boxes to ensure they tightly contain only the specific element.
    """
    
    response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_bytes}])
    
    # Extract JSON from response
    try:
        response_text = response.text
        # Find JSON part - simple approach looking for array
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            elements = json.loads(json_str)
        else:
            print("Couldn't parse JSON response, using empty elements list")
            elements = []
    except Exception as e:
        print(f"Error parsing elements: {e}")
        elements = []
    
    return elements

def extract_element_templates(screenshot, elements):
    """Extract template images for each identified element"""
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
                filename = f"templates/{safe_name}.png"
                
                # Save the template image
                element_img.save(filename)
                
                # Store template information
                templates[element['name']] = {
                    'filename': filename,
                    'bounding_box': element['bounding_box'],
                    'type': element.get('type', 'unknown'),
                    'description': element.get('description', '')
                }
                
                print(f"Extracted template for '{element['name']}' at {filename}")
            except Exception as e:
                print(f"Error extracting template for {element.get('name', 'unknown')}: {e}")
    
    return templates

def process_user_request(request, elements, templates):
    """Ask Gemini which element to click based on user request"""
    prompt = f"""
    User Request: "{request}"
    
    Available Desktop Elements: {json.dumps([{
        'name': e['name'], 
        'type': e.get('type', 'unknown'), 
        'description': e.get('description', '')
    } for e in elements])}
    
    Based on the user's request, which desktop element should be interacted with?
    Return a JSON object with:
    {{
        "target_element": "name of element to interact with",
        "action": "click", // one of: click, double_click, right_click, drag, type, hotkey, scroll
        "action_parameters": {{}}, // additional parameters needed for the action
        "reasoning": "brief explanation"
    }}
    
    If no suitable element found, return {{"error": "reason"}}.
    """
    
    response = model.generate_content(prompt)
    
    # Parse response to get action
    try:
        # Extract JSON
        response_text = response.text
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            action = json.loads(json_str)
        else:
            action = {"error": "Could not parse response"}
    except Exception as e:
        print(f"Error parsing action: {e}")
        action = {"error": f"Parse error: {e}"}
    
    return action

def execute_action_with_template(action, templates):
    """Execute action using template matching instead of direct coordinates"""
    if "error" in action:
        print(f"Cannot execute: {action['error']}")
        return False
    
    target = action.get("target_element")
    if not target or target not in templates:
        print(f"Target element '{target}' not found in templates")
        return False
    
    template_info = templates[target]
    template_file = template_info['filename']
    
    try:
        # Locate the template on screen
        print(f"Looking for template '{template_file}' on screen...")
        location = pyautogui.locateCenterOnScreen(template_file, confidence=0.8)
        
        if location:
            x, y = location
            print(f"Found template at coordinates ({x}, {y})")
            
            # Determine action type
            action_type = action.get("action", "click").lower()
            
            # Execute the appropriate action
            if action_type == "click":
                pyautogui.click(x, y)
                print("Performed click")
            elif action_type == "double_click":
                pyautogui.doubleClick(x, y)
                print("Performed double-click")
            elif action_type == "right_click":
                pyautogui.rightClick(x, y)
                print("Performed right-click")
            elif action_type == "drag":
                # Get end coordinates from action parameters
                end_target = action.get("action_parameters", {}).get("end_target")
                if end_target and end_target in templates:
                    end_template = templates[end_target]['filename']
                    end_location = pyautogui.locateCenterOnScreen(end_template, confidence=0.8)
                    if end_location:
                        end_x, end_y = end_location
                        pyautogui.dragTo(end_x, end_y, duration=1, button='left')
                        print(f"Dragged from ({x}, {y}) to ({end_x}, {end_y})")
                    else:
                        print(f"Could not find drag destination '{end_target}'")
                        return False
                else:
                    print("Drag operation requires valid end_target")
                    return False
            elif action_type == "type":
                content = action.get("action_parameters", {}).get("content", "")
                pyautogui.click(x, y)  # First click to focus
                pyautogui.typewrite(content)
                print(f"Typed: '{content}'")
            elif action_type == "hotkey":
                keys = action.get("action_parameters", {}).get("keys", [])
                if keys:
                    pyautogui.hotkey(*keys)
                    print(f"Pressed hotkey: {'+'.join(keys)}")
                else:
                    print("Hotkey operation requires valid keys parameter")
                    return False
            elif action_type == "scroll":
                direction = action.get("action_parameters", {}).get("direction", "down")
                clicks = action.get("action_parameters", {}).get("clicks", 3)
                if direction == "down":
                    pyautogui.scroll(-clicks, x=x, y=y)
                elif direction == "up":
                    pyautogui.scroll(clicks, x=x, y=y)
                elif direction == "left":
                    pyautogui.hscroll(-clicks, x=x, y=y)
                elif direction == "right":
                    pyautogui.hscroll(clicks, x=x, y=y)
                print(f"Scrolled {direction} at ({x}, {y})")
            else:
                print(f"Unsupported action type: {action_type}")
                return False
                
            return True
        else:
            print(f"Could not locate template '{template_file}' on screen")
            return False
    except Exception as e:
        print(f"Error executing action: {e}")
        return False

def main():
    print("Enhanced Desktop Automation with Gemini 2.5 Vision and Template Matching")
    print("--------------------------------------------------------------------")
    
    while True:
        # Get user instruction
        user_request = input("\nWhat would you like me to do? (type 'exit' to quit): ")
        
        if user_request.lower() == 'exit':
            print("Exiting program.")
            break
        
        # Take screenshot
        print("Capturing screen...")
        screenshot = capture_screen()
        
        # Identify elements
        print("Analyzing desktop elements...")
        elements = identify_desktop_elements(screenshot)
        print(f"Found {len(elements)} clickable elements")
        
        # Extract templates
        print("Extracting element templates...")
        templates = extract_element_templates(screenshot, elements)
        print(f"Extracted {len(templates)} templates")
        
        # Process request
        print("Processing your request...")
        action = process_user_request(user_request, elements, templates)
        
        if "error" in action:
            print(f"Could not determine what to do: {action['error']}")
            continue
            
        # Show what will be clicked
        target = action.get("target_element", "unknown element")
        action_type = action.get("action", "click")
        reason = action.get("reasoning", "No reason provided")
        print(f"\nI'll {action_type} on: {target}")
        print(f"Reason: {reason}")
        
        # Confirm with user
        confirm = input("Proceed with this action? (y/n): ")
        if confirm.lower() != 'y':
            print("Action cancelled.")
            continue
        
        # Execute the action
        success = execute_action_with_template(action, templates)
        if success:
            print("Action completed successfully!")
        else:
            print("Failed to execute the action.")
            
        # Optional: wait to see results
        time.sleep(1)

if __name__ == "__main__":
    main()
