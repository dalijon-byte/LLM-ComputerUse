# template_automation.py

import os
import time
import json
import io
from PIL import ImageGrab
import google.generativeai as genai
from dotenv import load_dotenv

# Import our utility modules
from utils.screen_capture import ScreenCapture
from utils.element_extraction import ElementExtractor
from utils.action_execution import ActionExecutor

# Load environment variables
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

# Configure Gemini API
genai.configure(api_key=api_key)
model_name = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-pro-exp-03-25') # Use env var, fallback to default
model = genai.GenerativeModel(model_name)

# Create instance of our utility classes
screen_capture = ScreenCapture(screenshot_dir="screenshots")
element_extractor = ElementExtractor(model_name=os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-pro-exp-03-25'), template_dir="templates")
action_executor = ActionExecutor(safety_level="high")

def process_user_request(request, elements, templates):
    """Ask Gemini which element to interact with based on user request"""
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
    
    Available actions are:
    - click: Simple click on element
    - double_click: Double-click on element
    - right_click: Right-click on element
    - drag: Drag from one element to another (needs start_element and end_element)
    - type: Type text (needs content parameter with the text)
    - hotkey: Press keyboard shortcut (needs keys parameter, e.g. ["ctrl", "c"])
    - scroll: Scroll in specified direction (needs direction parameter: "up", "down", "left", "right")
    
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

def process_advanced_action_request(request, elements):
    """Ask Gemini to generate one of the advanced actions based on user request"""
    # First create a clear description of available actions for the model
    available_actions = [
        "click(start_box='[x1, y1, x2, y2]')",
        "left_double(start_box='[x1, y1, x2, y2]')",
        "right_single(start_box='[x1, y1, x2, y2]')",
        "drag(start_box='[x1, y1, x2, y2]', end_box='[x3, y3, x4, y4]')",
        "hotkey(key='key1+key2')",
        "type(content='text to type')",
        "scroll(start_box='[x1, y1, x2, y2]', direction='down or up or right or left')",
        "wait()",
        "finished()",
        "call_user(message='Help needed')"
    ]
    
    # Format the elements nicely for the prompt
    elements_formatted = []
    for e in elements:
        elements_formatted.append({
            'name': e.get('name', 'unnamed'),
            'type': e.get('type', 'unknown'),
            'description': e.get('description', ''),
            'bounding_box': e.get('bounding_box', [0, 0, 0, 0])
        })
    
    prompt = f"""
    User Request: "{request}"
    
    Available Desktop Elements: {json.dumps(elements_formatted)}
    
    Based on the user's request, determine the best action to take from the following available actions:
    {json.dumps(available_actions, indent=2)}
    
    Return a JSON object with:
    {{
        "action_name": "name of action function to call",
        "parameters": {{
            "param1": "value1",
            "param2": "value2"
        }},
        "reasoning": "brief explanation of why this action was chosen"
    }}
    
    For element selection, use the appropriate bounding_box from the provided elements.
    If no suitable action is possible, return {{"error": "reason"}}.
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

def main():
    print("Enhanced Desktop Automation with Gemini 2.5 Vision and Template Matching")
    print("--------------------------------------------------------------------")
    print("1. Basic Mode - Using Template Matching")
    print("2. Advanced Mode - Using Bounding Box Actions")
    mode = input("Select mode (1 or 2): ")
    
    while True:
        # Get user instruction
        user_request = input("\nWhat would you like me to do? (type 'exit' to quit): ")
        
        if user_request.lower() == 'exit':
            print("Exiting program.")
            break
        
        # Take screenshot
        print("Capturing screen...")
        screenshot, image_bytes = screen_capture.capture_to_bytes()
        
        # Identify elements
        print("Analyzing desktop elements...")
        elements = element_extractor.identify_elements(screenshot, image_bytes)
        print(f"Found {len(elements)} clickable elements")
        
        if mode == "1":  # Basic Template Matching Mode
            # Extract templates
            print("Extracting element templates...")
            templates = element_extractor.extract_templates(screenshot, elements)
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
            
            # Find the target on screen using template matching
            print("Locating target on screen...")
            current_screen = screen_capture.capture_full_screen()
            template_locations = element_extractor.find_templates_on_screen(
                current_screen, {target: templates[target]}, confidence=0.7
            )
            
            if target in template_locations:
                location = template_locations[target]['center']
                
                # Determine action parameters
                action_params = {}
                if action_type == "drag":
                    # For drag, we need to find end element too
                    end_target = action.get("action_parameters", {}).get("end_target")
                    if end_target and end_target in templates:
                        end_locations = element_extractor.find_templates_on_screen(
                            current_screen, {end_target: templates[end_target]}, confidence=0.7
                        )
                        if end_target in end_locations:
                            action_params['end_location'] = end_locations[end_target]['center']
                        else:
                            print(f"Could not locate end target '{end_target}' on screen")
                            continue
                elif action_type == "type":
                    action_params['text'] = action.get("action_parameters", {}).get("content", "")
                elif action_type == "hotkey":
                    action_params['keys'] = action.get("action_parameters", {}).get("keys", [])
                elif action_type == "scroll":
                    action_params['direction'] = action.get("action_parameters", {}).get("direction", "down")
                
                # Execute the action
                success = action_executor.execute_action(
                    action_type, 
                    target=target,
                    location=location,
                    **action_params
                )
                
                if success:
                    print("Action completed successfully!")
                else:
                    print("Failed to execute the action.")
            else:
                print(f"Could not locate target '{target}' on screen")
        
        elif mode == "2":  # Advanced Actions Mode
            # Process request for advanced actions
            print("Processing your request for advanced action...")
            action = process_advanced_action_request(user_request, elements)
            
            if "error" in action:
                print(f"Could not determine what to do: {action['error']}")
                continue
            
            # Display the planned action
            action_name = action.get("action_name", "unknown")
            parameters = action.get("parameters", {})
            reasoning = action.get("reasoning", "No reason provided")
            
            print(f"\nI'll execute: {action_name}")
            print(f"With parameters: {json.dumps(parameters, indent=2)}")
            print(f"Reason: {reasoning}")
            
            # Confirm with user
            confirm = input("Proceed with this action? (y/n): ")
            if confirm.lower() != 'y':
                print("Action cancelled.")
                continue
            
            # Execute the advanced action
            success = action_executor.execute_advanced_action(action_name, parameters)
            
            if success:
                print("Advanced action completed successfully!")
            else:
                print("Failed to execute the advanced action.")
        
        # Optional: wait to see results
        time.sleep(1)

if __name__ == "__main__":
    main()
