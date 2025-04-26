# utils/action_execution.py

import time
import pyautogui
import json

class ActionExecutor:
    """Handles the execution of actions on desktop elements"""
    
    def __init__(self, safety_level="high"):
        """Initialize the action executor
        
        Args:
            safety_level: How cautious the executor should be. Options: "high", "medium", "low"
        """
        self.safety_level = safety_level
        self.last_action_time = time.time()
        self.actions_per_minute = 0
        self.action_history = []
        
        # Configure PyAutoGUI safety settings
        pyautogui.PAUSE = 0.5 if safety_level == "high" else 0.2
        pyautogui.FAILSAFE = True  # Moving mouse to corner will abort
        
    def execute_action(self, action_type, target=None, location=None, **kwargs):
        """Execute a specific action
        
        Args:
            action_type: Type of action to perform (click, type, etc.)
            target: Name of the target element
            location: Tuple of (x, y) coordinates for the action
            **kwargs: Additional action-specific parameters
            
        Returns:
            Boolean indicating success
        """
        # Safety checks
        if self.safety_level == "high":
            # Check rate limits
            current_time = time.time()
            if current_time - self.last_action_time < 0.5:
                time.sleep(0.5 - (current_time - self.last_action_time))
            
            # Update action rate tracking
            self.last_action_time = time.time()
            self.actions_per_minute += 1
            
            # If too many actions in a short time, slow down
            if self.actions_per_minute > 30:
                print("Too many actions! Slowing down for safety...")
                time.sleep(2)
                self.actions_per_minute = 0
        
        # Log the action
        action_record = {
            'type': action_type,
            'target': target,
            'location': location,
            'params': kwargs,
            'timestamp': time.time()
        }
        self.action_history.append(action_record)
        
        # Execute the appropriate action
        try:
            if action_type == "click":
                if location:
                    pyautogui.click(location[0], location[1])
                    return True
                    
            elif action_type == "double_click":
                if location:
                    pyautogui.doubleClick(location[0], location[1])
                    return True
                    
            elif action_type == "right_click":
                if location:
                    pyautogui.rightClick(location[0], location[1])
                    return True
                    
            elif action_type == "drag":
                start = location
                end = kwargs.get('end_location')
                if start and end:
                    pyautogui.moveTo(start[0], start[1])
                    pyautogui.dragTo(end[0], end[1], duration=1)
                    return True
                    
            elif action_type == "type":
                text = kwargs.get('text', '')
                if location:
                    pyautogui.click(location[0], location[1])  # Focus first
                    pyautogui.typewrite(text)
                    return True
                    
            elif action_type == "hotkey":
                keys = kwargs.get('keys', [])
                if keys:
                    pyautogui.hotkey(*keys)
                    return True
                    
            elif action_type == "scroll":
                direction = kwargs.get('direction', 'down')
                clicks = kwargs.get('clicks', 3)
                if location:
                    if direction == "down":
                        pyautogui.scroll(-clicks, x=location[0], y=location[1])
                    elif direction == "up":
                        pyautogui.scroll(clicks, x=location[0], y=location[1])
                    elif direction == "left":
                        pyautogui.hscroll(-clicks, x=location[0], y=location[1])
                    elif direction == "right":
                        pyautogui.hscroll(clicks, x=location[0], y=location[1])
                    return True
                    
            elif action_type == "wait":
                seconds = kwargs.get('seconds', 5)
                time.sleep(seconds)
                return True
                
            elif action_type == "finished":
                print("Task completed successfully!")
                return True
                
            elif action_type == "call_user":
                message = kwargs.get('message', 'Attention required')
                print(f"\n!!! {message} !!!")
                input("Press Enter to continue...")
                return True
                
            return False
            
        except Exception as e:
            print(f"Error executing action: {e}")
            return False
            
    def execute_advanced_action(self, action_name, params):
        """Execute predefined advanced actions
        
        Args:
            action_name: Name of the action to perform
            params: Dictionary of parameters for the action
            
        Returns:
            Boolean indicating success
        """
        try:
            if action_name == "click":
                if 'start_box' in params:
                    x1, y1, x2, y2 = eval(params['start_box'])
                    # Click center of the box
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    return self.execute_action("click", location=(center_x, center_y))
                    
            elif action_name == "left_double":
                if 'start_box' in params:
                    x1, y1, x2, y2 = eval(params['start_box'])
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    return self.execute_action("double_click", location=(center_x, center_y))
                    
            elif action_name == "right_single":
                if 'start_box' in params:
                    x1, y1, x2, y2 = eval(params['start_box'])
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    return self.execute_action("right_click", location=(center_x, center_y))
                    
            elif action_name == "drag":
                if 'start_box' in params and 'end_box' in params:
                    x1, y1, x2, y2 = eval(params['start_box'])
                    x3, y3, x4, y4 = eval(params['end_box'])
                    start_x, start_y = (x1 + x2) // 2, (y1 + y2) // 2
                    end_x, end_y = (x3 + x4) // 2, (y3 + y4) // 2
                    
                    return self.execute_action("drag", 
                                              location=(start_x, start_y),
                                              end_location=(end_x, end_y))
                    
            elif action_name == "hotkey":
                if 'key' in params:
                    # Parse keys like "ctrl+c" into ["ctrl", "c"]
                    keys = params['key'].split('+')
                    return self.execute_action("hotkey", keys=keys)
                    
            elif action_name == "type":
                if 'content' in params:
                    content = params['content']
                    if 'start_box' in params:
                        x1, y1, x2, y2 = eval(params['start_box'])
                        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                        return self.execute_action("type", 
                                                 location=(center_x, center_y),
                                                 text=content)
                    else:
                        return self.execute_action("type", text=content)
                    
            elif action_name == "scroll":
                if 'start_box' in params and 'direction' in params:
                    direction = params['direction'].lower()
                    x1, y1, x2, y2 = eval(params['start_box'])
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    return self.execute_action("scroll", 
                                             location=(center_x, center_y),
                                             direction=direction)
                    
            elif action_name == "wait":
                seconds = int(params.get('seconds', 5))
                return self.execute_action("wait", seconds=seconds)
                
            elif action_name == "finished":
                return self.execute_action("finished")
                
            elif action_name == "call_user":
                message = params.get('message', 'Assistance needed')
                return self.execute_action("call_user", message=message)
                
            return False
            
        except Exception as e:
            print(f"Error executing advanced action: {e}")
            return False
