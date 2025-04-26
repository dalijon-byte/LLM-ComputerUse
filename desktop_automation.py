import os
import time
import json
import pyautogui
import io
from PIL import ImageGrab
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

# Configure Gemini API
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-pro-exp-03-25')

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
    """Use Gemini to identify elements on screen"""
    image_bytes = screenshot_to_bytes(screenshot)
    
    prompt = """
    Analyze this desktop screenshot and identify all clickable elements.
    For each element provide: type, name, and approximate (x,y) coordinates.
    Format as JSON with fields: type, name, coordinates (as [x,y]), description.
    Focus on desktop icons, taskbar buttons, start menu, and application windows.
    """
    
    response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_bytes}])
    
    # Extract JSON from response
    try:
        # This assumes the response text contains JSON data
        response_text = response.text
        # Find JSON part - simple approach looking for array
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = response_text[start_idx:end_idx]
            elements = json.loads(json_str)
        else:
            # Fallback if response isn't properly formatted JSON
            print("Couldn't parse JSON response, using empty elements list")
            elements = []
    except Exception as e:
        print(f"Error parsing elements: {e}")
        elements = []
    
    return elements

def process_user_request(request, desktop_elements):
    """Ask Gemini which element to click based on user request"""
    prompt = f"""
    User Request: "{request}"
    
    Desktop Elements: {json.dumps(desktop_elements)}
    
    Based on the user's request, which desktop element should be clicked?
    Return a JSON object with:
    {{
        "target_element": "name of element to click",
        "coordinates": [x, y],
        "click_type": "single" or "double",
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

def execute_action(action):
    """Move mouse and click based on the action"""
    if "error" in action:
        print(f"Cannot execute: {action['error']}")
        return False
    
    if "coordinates" not in action:
        print("No coordinates provided in action")
        return False
    
    try:
        x, y = action["coordinates"]
        # Move mouse
        pyautogui.moveTo(x, y, duration=0.5)
        
        # Click appropriately
        click_type = action.get("click_type", "single")
        if click_type == "double":
            pyautogui.doubleClick()
        else:
            pyautogui.click()
            
        print(f"Clicked at coordinates ({x}, {y})")
        return True
    except Exception as e:
        print(f"Error executing action: {e}")
        return False

def main():
    print("Desktop Automation with Gemini 2.5 Vision")
    print("----------------------------------------")
    
    while True:
        # Get user instruction
        user_request = input("\nWhat would you like me to click on? (type 'exit' to quit): ")
        
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
        
        # Process request
        print("Processing your request...")
        action = process_user_request(user_request, elements)
        
        if "error" in action:
            print(f"Could not determine what to click: {action['error']}")
            continue
            
        # Show what will be clicked
        target = action.get("target_element", "unknown element")
        reason = action.get("reasoning", "No reason provided")
        print(f"\nI'll click on: {target}")
        print(f"Reason: {reason}")
        
        # Confirm with user
        confirm = input("Proceed with this action? (y/n): ")
        if confirm.lower() != 'y':
            print("Action cancelled.")
            continue
        
        # Execute the action
        success = execute_action(action)
        if success:
            print("Action completed successfully!")
        else:
            print("Failed to execute the action.")

if __name__ == "__main__":
    main()
