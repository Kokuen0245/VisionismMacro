import tkinter as tk
from tkinter import ttk
from threading import Thread
import time
import cv2
import numpy as np
import pyautogui
import keyboard
import json
import pytesseract
import requests

# Global variables
pytesseract.pytesseract.tesseract_cmd = r'Tesseract\\tesseract.exe'
keys = ['W', 'A', 'S', 'D']
key_paths = {"W": "assets/W.png", "A": "assets/A.png", "S": "assets/S.png", "D": "assets/D.png"}
speed_button_path = "assets/speedButton.png"
stam_button_path = "assets/stamButton.png"
start_button_path = "assets/startButton.png"
cooldown_period = 1.8
last_pressed_timestamps = {key: 0 for key in keys}
active_farm = None
watch_fatigue = False

# Functions
def click_stam_button():
    try:
        stam_button_location = pyautogui.locateCenterOnScreen(stam_button_path)
        if stam_button_location:
            pyautogui.click(stam_button_location)
            print("Clicked stamina.")
    except Exception as e:
        print(f"Error in click_stam_button: {e}")

def click_speed_button():
    try:
        speed_button_location = pyautogui.locateCenterOnScreen(speed_button_path)
        if speed_button_location:
            pyautogui.click(speed_button_location)
            print("Clicked speed.")
    except Exception as e:
        print(f"Error in click_speed_button: {e}")

def click_start_button():
    try:
        start_button_location = pyautogui.locateCenterOnScreen(start_button_path)
        if start_button_location:
            pyautogui.click(start_button_location)
            print("Clicked start.")
    except Exception as e:
        print(f"Error in click_start_button: {e}")

def detect_and_press_keys():
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    for key in keys:
        current_time = time.time()
        if current_time - last_pressed_timestamps[key] < cooldown_period:
            continue

        key_image = cv2.imread(key_paths[key], cv2.IMREAD_GRAYSCALE)
        result = cv2.matchTemplate(screenshot_gray, key_image, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        locations = np.where(result >= threshold)

        if locations[0].any():
            time.sleep(0.1)
            keyboard.press(key)
            keyboard.release(key)
            print(f"Pressed key {key}")
            last_pressed_timestamps[key] = current_time

def start_farm():
    global active_farm
    active_farm = farm_type_var.get()
    farm_thread = Thread(target=automate_farm)
    farm_thread.daemon = True
    farm_thread.start()

def stop_farm():
    global active_farm
    active_farm = None

def automate_farm():
    while active_farm:
        try:
            if active_farm == "stam":
                click_stam_button()
            elif active_farm == "speed":
                click_speed_button()
            elif active_farm == "pullup" or active_farm == "bench":
                click_start_button()
            detect_and_press_keys()
        except Exception as e:
            print(f"Error: {e}")

def start_fatigue_watcher():
    global watch_fatigue
    watch_fatigue = fatigue_watcher_var.get()
    fatigue_thread = Thread(target=watch_fatigue_function)
    fatigue_thread.daemon = True
    fatigue_thread.start()

def stop_fatigue_watcher():
    global watch_fatigue
    watch_fatigue = False

def watch_fatigue_function():
    while watch_fatigue:
        try:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            fatigue_text = pytesseract.image_to_string(screenshot)

            fatigue_value = None

            if "Fatigue" in fatigue_text:
                fatigue_value = fatigue_text.split("Fatigue: ")[1].split("%")[0]
            
            if fatigue_value >= "70":
                send_to_webhook("fatigue")

            time.sleep(5)
        except Exception as e:
            print(f"Error in fatigue watcher: {e}")

def save_webhook(url):
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}

    config['webhook_url'] = url

    with open('config.json', 'w') as f:
        json.dump(config, f)

    print(f"Webhook URL saved: {url}")

def test_webook():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"webhook_url": "null"}

    payload = {
        "content": "@everyone\nTesting webhook."
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    requests.post(config['webhook_url'], data=json.dumps(payload), headers=headers)

def send_to_webhook(alert_val):
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"webhook_url": "null"}

    if alert_val == "fatigue":
        payload = {
            "content": "@everyone\nFatigue is over 70%."
        }
    else:
        payload = {
            "content": "@everyone\nProblem with alert value."
        }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    requests.post(config['webhook_url'], data=json.dumps(payload), headers=headers)

# UI
root = tk.Tk()

root.title("Farm Automation")
root.geometry("500x300")

tab_control = ttk.Notebook(root)
tab1 = ttk.Frame(tab_control)
tab2 = ttk.Frame(tab_control)
tab3 = ttk.Frame(tab_control)

tab_control.add(tab1, text="Main")
tab_control.add(tab2, text="Watcher")
tab_control.add(tab3, text="Webhook")

fatigue_watcher_var = tk.BooleanVar()

farm_type_var = tk.StringVar()
farm_type_label = ttk.Label(tab1, text="Choose Farm Type:")
farm_type_combo = ttk.Combobox(tab1, textvariable=farm_type_var, values=["stam", "speed", "pullup", "bench"])
start_button = ttk.Button(tab1, text="Start Farm", command=start_farm)
stop_button = ttk.Button(tab1, text="Stop Farm", command=stop_farm)

fatigue_checkbox = ttk.Checkbutton(tab2, text="Watch Fatigue", variable=fatigue_watcher_var)
start_fatigue_button = ttk.Button(tab2, text="Start Watcher", command=start_fatigue_watcher)
stop_fatigue_button = ttk.Button(tab2, text="Stop Watcher", command=stop_fatigue_watcher)

webhook_label = ttk.Label(tab3, text="Discord Webhook URL:")
webhook_entry = ttk.Entry(tab3)
save_button = ttk.Button(tab3, text="Save", command=lambda: save_webhook(webhook_entry.get()))
test_button = ttk.Button(tab3, text="Test Webhook", command=lambda: test_webook())

farm_type_label.pack(pady=10)
farm_type_combo.pack(pady=5)
start_button.pack(pady=5)
stop_button.pack(pady=5)

fatigue_checkbox.pack(pady=5)
start_fatigue_button.pack(pady=5)
stop_fatigue_button.pack(pady=5)

webhook_label.pack(pady=10)
webhook_entry.pack(pady=5)
save_button.pack(pady=5)
test_button.pack(pady=5)

tab_control.pack(expand=1, fill="both")

root.mainloop()