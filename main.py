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
stat_start_button_path = "assets/startButton.png"
hold_e_button_path = "assets/holdEButton.png"
cooldown_period = 1.8
last_pressed_timestamps = {key: 0 for key in keys}
active_stat_farm = None
active_money_farm = None
watch_fatigue = False
watch_combat = False
has_insomnia = False

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

def click_stat_start_button():
    try:
        stat_start_button_location = pyautogui.locateCenterOnScreen(stat_start_button_path)
        if stat_start_button_location:
            pyautogui.click(stat_start_button_location)
            print("Clicked start.")
    except Exception as e:
        print(f"Error in click_stat_start_button: {e}")

def get_on_training():
    try:
        hold_e_button_location = pyautogui.locateCenterOnScreen(hold_e_button_path)
        if hold_e_button_location:
            hold_key(e, 2)
            print("Got on training.")
    except Exception as e:
        print(f"Error in click_stat_start_button: {e}")

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

def hold_key(key, duration):
    keyboard.press(key)
    time.sleep(duration)
    keyboard.release(key)

def start_stat_farm():
    global active_stat_farm
    active_stat_farm = stat_type_var.get()
    stat_farm_thread = Thread(target=automate_stat_farm)
    stat_farm_thread.daemon = True
    stat_farm_thread.start()

def stop_stat_farm():
    global active_stat_farm
    active_stat_farm = None

def start_money_farm():
    global active_money_farm
    active_money_farm = money_type_var.get()
    money_farm_thread = Thread(target=automate_money_farm)
    money_farm_thread.daemon = True
    money_farm_thread.start()

def stop_money_farm():
    global active_money_farm
    active_money_farm = None

def automate_stat_farm():
    while active_stat_farm:
        try:
            get_on_training()
            if active_stat_farm == "stam":
                click_stam_button()
            elif active_stat_farm == "speed":
                click_speed_button()
            elif active_stat_farm == "pullup" or active_stat_farm == "bench":
                click_stat_start_button()
            detect_and_press_keys()
        except Exception as e:
            print(f"Error: {e}")

def automate_money_farm():
    print('idk bro')

def start_watcher():
    global watch_fatigue
    global watch_combat
    global has_insomnia
    watch_fatigue = fatigue_watcher_var.get()
    watch_combat = combat_watcher_var.get()
    has_insomnia = has_insomnia_var.get()
    watcher_thread = Thread(target=watcher_function)
    watcher_thread.daemon = True
    watcher_thread.start()

def stop_watcher():
    global watch_fatigue
    global watch_combat
    watch_fatigue = False
    watch_combat = False

def watcher_function():
    while watch_fatigue:
        try:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            fatigue_text = pytesseract.image_to_string(screenshot)

            fatigue_value = None

            if "Fatigue" in fatigue_text:
                fatigue_value = fatigue_text.split("Fatigue: ")[1].split("%")[0]
            
            if fatigue_value is not None:
                fatigue_value = float(fatigue_value)
                if fatigue_value >= 70 and not has_insomnia:
                    send_to_webhook("fatigue")
                elif fatigue_value >= 82 and has_insomnia:
                    send_to_webhook("fatigue")

            time.sleep(5)
        except Exception as e:
            print(f"Error in fatigue watcher: {e}")
    while watch_combat:
        try:
            screenshot = pyautogui.screenshot()
            screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            combat_tag = pytesseract.image_to_string(screenshot)

            if "COMBAT" in combat_tag:
                send_to_webhook("combat")

            time.sleep(5)
        except Exception as e:
            print(f"Error in combat watcher: {e}")

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

def delete_webhook():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"webhook_url": "null"}

    config['webhook_url'] = "null"

    with open('config.json', 'w') as f:
        json.dump(config, f)

    print("Webhook successfully deleted")

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
    elif alert_val == "combat":
        payload = {
            "content": "@everyone\nYou are in combat."
        }
    else:
        payload = {
            "content": "@everyone\nProblem with alert value."
        }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    requests.post(config['webhook_url'], data=json.dumps(payload), headers=headers)

def get_version_number():
    version_url = "https://raw.githubusercontent.com/Kokuen0245/VisionismMacro/main/version.txt"

    try:
        response = requests.get(version_url)
        
        if response.status_code == 200:
            version_number = response.text.strip()
            return version_number
        else:
            print(f"Failed to fetch version file. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error fetching version file: {e}")
        return None

# Setup
version = get_version_number()

# UI
root = tk.Tk()

root.title("Visionism Macro | " + version)
root.geometry("500x300")

tab_control = ttk.Notebook(root)
stat_auto = ttk.Frame(tab_control)
money_auto = ttk.Frame(tab_control)
watcher = ttk.Frame(tab_control)
webhook = ttk.Frame(tab_control)
credits = ttk.Frame(tab_control)

tab_control.add(stat_auto, text="Stat Automation")
tab_control.add(money_auto, text="Money Automation")
tab_control.add(watcher, text="Watcher")
tab_control.add(webhook, text="Webhook")
tab_control.add(credits, text="Credits")

fatigue_watcher_var = tk.BooleanVar()
combat_watcher_var = tk.BooleanVar()
has_insomnia_var = tk.BooleanVar()

stat_type_var = tk.StringVar()
stat_type_label = ttk.Label(stat_auto, text="Choose Farm Type:")
stat_type_combo = ttk.Combobox(stat_auto, textvariable=stat_type_var, values=["stam", "speed", "pullup", "bench"])
stat_start_button = ttk.Button(stat_auto, text="Start Farm", command=start_stat_farm)
stat_stop_button = ttk.Button(stat_auto, text="Stop Farm", command=stop_stat_farm)

money_type_var = tk.StringVar()
money_type_label = ttk.Label(money_auto, text="Choose Farm Type:")
money_type_combo = ttk.Combobox(money_auto, textvariable=money_type_var, values=["Macro Based", "AI Based"])
money_start_button = ttk.Button(money_auto, text="Start Farm", command=start_money_farm)
money_stop_button = ttk.Button(money_auto, text="Stop Farm", command=stop_money_farm)

fatigue_checkbox = ttk.Checkbutton(watcher, text="Watch Fatigue", variable=fatigue_watcher_var)
combat_checkbox = ttk.Checkbutton(watcher, text="Watch Combat Tag", variable=combat_watcher_var)
start_watcher_button = ttk.Button(watcher, text="Start Watcher", command=start_watcher)
stop_watcher_button = ttk.Button(watcher, text="Stop Watcher", command=stop_watcher)
modification_label = ttk.Label(watcher, text="Modifications for watcher:")
insomnia_checkbox = ttk.Checkbutton(watcher, text="Has Insomnia", variable=has_insomnia_var)

webhook_label = ttk.Label(webhook, text="Discord Webhook URL:")
webhook_entry = ttk.Entry(webhook)
save_button = ttk.Button(webhook, text="Save", command=lambda: save_webhook(webhook_entry.get()))
test_button = ttk.Button(webhook, text="Test Webhook", command=lambda: test_webook())
delete_button = ttk.Button(webhook, text="Delete Webhook", command=lambda: delete_webhook())

credit_label_1 = ttk.Label(credits, text="Created by kokuen_.")
credit_label_2 = ttk.Label(credits, text="Tested by rust3631")

stat_type_label.pack(pady=10)
stat_type_combo.pack(pady=5)
stat_start_button.pack(pady=5)
stat_stop_button.pack(pady=5)

money_type_label.pack(pady=10)
money_type_combo.pack(pady=5)
money_start_button.pack(pady=5)
money_stop_button.pack(pady=5)

fatigue_checkbox.pack(pady=5)
combat_checkbox.pack(pady=5)
start_watcher_button.pack(pady=5)
stop_watcher_button.pack(pady=5)
modification_label.pack(pady=10)
insomnia_checkbox.pack(pady=5)

webhook_label.pack(pady=10)
webhook_entry.pack(pady=5)
save_button.pack(pady=5)
test_button.pack(pady=5)
delete_button.pack(pady=5)

credit_label_1.pack(pady=5)
credit_label_2.pack(pady=5)

tab_control.pack(expand=1, fill="both")

root.mainloop()