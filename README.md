# LLM Desktop Automation with Gemini 2.5 Vision

Automate desktop interactions using AI vision & language capabilities.

![Project Banner](https://repository-images.githubusercontent.com/803307245/b4eb447e-fdb7-4b00-baf5-0a3e66a5b492)

## Overview

**LLM Desktop Automation** is a Python framework that empowers you to control your desktop UI by natural language prompts.
Harness the power of **Gemini 2.5 Vision's API** to visually understand your desktop, process commands, and perform intelligent mouse clicks using AI reasoning.

![LLM Desktop Automation Demo](LLM-PoweredDestopApp666.png)

## Features

-   Vision-powered recognition of desktop icons and windows
-   Smart mouse movement & click via `pyautogui`
-   Natural language instructions powered by Gemini 2.5 LLM
-   Built-in safety prompts before high-impact actions
-   Pythonic and readable code, ready to extend

## How It Works

1.  User types a command: `Open Recycle Bin`
2.  Screenshot of desktop is taken
3.  Screenshot is sent to **Gemini 2.5 Vision** for detection of clickable elements
4.  Structured screen analysis (elements + coordinates) is returned
5.  LLM matches user instruction to visual data, selects the target
6.  Python script uses `pyautogui` to move mouse and click the target
7.  (Optional) User is prompted to confirm risky actions

## Installation

```bash
# Clone the repository
git clone https://github.com/dalijon-byte/LLM-ComputerUse.git
cd LLM-ComputerUse.git

# Install Python dependencies (Python 3.8+ recommended)
pip install -r requirements.txt
```

## Configuration

1.  **Set up Gemini API key:**
    *   Sign up for Gemini API and get your key: [Get API Key](https://aistudio.google.com/app/apikey)
    *   Create a `.env` file in your project root:
        ```dotenv
        GEMINI_API_KEY=your_gemini_2.5_vision_api_key_here
        ```
2.  **Adjust permissions:** This script requires permission to capture your screen and control your mouse.

## Usage Example

```bash
python desktop_automation.py
```

When prompted, type commands like:
`Click the Chrome icon`
`Open Notepad`
`Open the Recycle Bin`

## Minimal Example

```python
import os, pyautogui
from PIL import ImageGrab
import google.generativeai as genai
# ... Set up Gemini as in documentation

screenshot = ImageGrab.grab()
# Send screenshot and prompt to Gemini
# Parse result, get coordinates
pyautogui.moveTo(x, y)
pyautogui.click()
```

## Security Warning

> **Warning:** Running this code gives the AI limited control of your mouse and keyboard.
> Only use in safe, controlled environments. Carefully review all actions before confirming.

## Project Structure

```
llm-desktop-automation/
├─ desktop_automation.py
├─ requirements.txt
└─ README.md
```

## Dependencies

-   `python-dotenv`
-   `google-generativeai`
-   `pyautogui`
-   `pillow` (PIL)

## Extending

You can add:

-   Voice command input via `SpeechRecognition`
-   Better vision models with OpenCV, YOLO, or LLaVA
-   Self-verification for critical clicks

## Troubleshooting

-   Errors about permissions? See your OS's privacy/accessibility settings for screen and input control
-   Mouse not clicking where expected? Check your display scaling and resolution settings
-   Gemini errors? Ensure API key is correct and you have quota

## FAQ

<details open>
  <summary>Is this production ready?</summary>
  <p>No – it is a research/prototype tool. Use in controlled environments only.</p>
</details>
<details>
  <summary>Can I use other LLMs?</summary>
  <p>Yes, via API adjustments, but Gemini 2.5 Vision recommended for best multi-modal performance.</p>
</details>
<details>
  <summary>Can it close popups or interact with notifications?</summary>
  <p>If they appear in the screenshot, and are visually distinct, yes.</p>
</details>

## License

This project is **MIT Licensed**.
Copyright © 2025 Dalibor JONIC, MSc

```text
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---
*Powered by Gemini 2.5 Vision · Built for research and innovation.*
