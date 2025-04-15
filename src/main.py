# main.py

import time, ujson
from machine import Pin, I2C, Timer
from smart_pid_pwm import SmartPIDPWM
import ssd1306

# ====== HARDWARE SETUP ======
BUZZER = Pin(19, Pin.OUT)
BUZZER.off()
BUTTON1 = Pin(17, Pin.IN, Pin.PULL_UP)
BUTTON2 = Pin(18, Pin.IN, Pin.PULL_UP)
button1_target = config.get("button1_target", 40)
button2_target = config.get("button2_target", 80)
button1_pressed_time = 0
button2_pressed_time = 0
RELAY_PIN = Pin(16, Pin.OUT)
if config.get("use_relay", True):
        RELAY_PIN.off()
ENC_A = Pin(12, Pin.IN, Pin.PULL_UP)
ENC_B = Pin(13, Pin.IN, Pin.PULL_UP)
ENC_BTN = Pin(14, Pin.IN, Pin.PULL_UP)
HEATER_PIN = 15

i2c = I2C(0, scl=Pin(5), sda=Pin(4))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# ====== CONFIG STORAGE ======
CONFIG_FILE = 'config.json'
def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return ujson.load(f)
    except:
        default = {
            "Kp": 2.0,
            "Ki": 0.5,
            "Kd": 0.1,
            "min_temp": 20,
            "max_temp": 150,
            "timeout": 0,
            "use_relay": True,
            "use_second_probe": False,
            "max_temp_diff": 5,
            "use_slow_pwm": True,
            "button1_target": 40,
            "button2_target": 80,
            "button_labels": True,
            "button1_label": "Coffee",
            "button2_label": "Steam",
            "use_buzzer": True}
        save_config(default)
        return default
    except:
        default = {
            "Kp": 2.0,
            "Ki": 0.5,
            "Kd": 0.1,
            "min_temp": 20,
            "max_temp": 150,
            "timeout": 0
        }
        save_config(default)
        return default

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        ujson.dump(cfg, f)

config = load_config()

# ====== HEATER PID SETUP ======
pid = SmartPIDPWM(pin=HEATER_PIN, slow_pwm=True, pwm_period=2.0)
pid.Kp = config["Kp"]
pid.Ki = config["Ki"]
pid.Kd = config["Kd"]

# State
target_temp = 60
heater_enabled = False
menu_index = 0
in_menu = False
editing = False
last_encoder = ENC_A.value()
last_press = time.ticks_ms()

# Real sensor read (e.g. NTC on ADC pin 26)
from machine import ADC
TEMP_SENSOR = ADC(26)

def read_temp():
    # Basic 10k thermistor linear mapping example (adjust to your sensor)
    voltage = TEMP_SENSOR.read_u16() * 3.3 / 65535
    resistance = (3.3 - voltage) * 10000 / voltage
    temp = 1 / (0.001129148 + 0.000234125 * (resistance / 10000) + 0.0000000876741 * (resistance / 10000)**3)
    return temp - 273.15

# Timeout logic
timeout_timer = Timer()
last_active_time = time.time()

def check_timeout():
    if config["timeout"] > 0 and heater_enabled:
        if time.time() - last_active_time > config["timeout"] * 60:
            disable_heater()

def enable_heater():
    global heater_enabled, last_active_time
    heater_enabled = True
    last_active_time = time.time()
    if config.get("use_relay", True):
        RELAY_PIN.on()

def disable_heater():
    global heater_enabled
    heater_enabled = False
    pid._set_duty_cycle(0)
    RELAY_PIN.off()

# ====== MENU OPTIONS ======
menu_items = ["Use Buzzer", "Show Labels", "Set Min Temp", "Set Max Temp", "Set Kp", "Set Ki", "Set Kd", "Set Timeout", "Use Relay", "Use Second Probe", "Max Temp Diff", "Use Slow PWM", "Run Optimization", "Enable Heater"]

# ====== DISPLAY ======
def draw_main(temp):
    oled.fill(0)
    oled.text("Current: {:.1f}C".format(temp), 0, 0)
    if config.get("button_labels", True):
        oled.text("[{}:{}C {}:{}C]".format(
        config.get("button1_label", "1"), config.get("button1_target", 40),
        config.get("button2_label", "2"), config.get("button2_target", 80)
    ), 0, 8)
    oled.text("Target: {:.1f}C".format(target_temp), 0, 16)
    oled.text("Heater: {}".format("ON" if heater_enabled else "OFF"), 0, 32)
    oled.text("Hold btn: Menu", 0, 48)
    oled.show()

def draw_menu():
    oled.fill(0)
    for i, item in enumerate(menu_items):
        prefix = ">" if i == menu_index else " "
        oled.text(prefix + item, 0, i * 8)
    oled.show()

def draw_edit(value):
    oled.fill(0)
    oled.text("Edit:", 0, 0)
    oled.text(str(value), 0, 16)
    oled.text("Click to Save", 0, 48)
    oled.show()

# ====== ENCODER HANDLER ======
def handle_encoder():
    global last_encoder, target_temp, menu_index, editing, in_menu, last_press
    clk = ENC_A.value()
    dt = ENC_B.value()
    btn = ENC_BTN.value()
    now = time.ticks_ms()

    if clk != last_encoder:
        direction = -1 if dt == clk else 1
        if in_menu:
            if editing:
                adjust_menu_value(direction)
            else:
                menu_index = (menu_index + direction) % len(menu_items)
        else:
            target_temp += direction
            target_temp = max(config["min_temp"], min(config["max_temp"], target_temp))
        last_encoder = clk

    if btn == 0 and time.ticks_diff(now, last_press) > 1000:
        last_press = now
        if not in_menu:
            in_menu = True
        elif not editing:
            enter_menu_item()
        else:
            save_menu_value()

# ====== MENU LOGIC ======
def adjust_menu_value(dir):
    if menu_index == 0:
        config["use_buzzer"] = not config.get("use_buzzer", True)
        return
    index_offset = 1
    if menu_index == index_offset + 0:
        config["button_labels"] = not config.get("button_labels", True)
        return
    index_offset = 1
    global config
    if menu_index == 0:
        config["min_temp"] += dir
    elif menu_index == index_offset + 1:
        config["max_temp"] += dir
    elif menu_index == index_offset + 2:
        config["Kp"] += dir * 0.1
    elif menu_index == index_offset + 3:
        config["Ki"] += dir * 0.1
    elif menu_index == index_offset + 4:
        config["Kd"] += dir * 0.1
    elif menu_index == index_offset + 5:
        config["timeout"] += dir
        if config["timeout"] < 0:
            config["timeout"] = 0
    elif menu_index == index_offset + 6:
        config["use_relay"] = not config.get("use_relay", True)
    elif menu_index == index_offset + 7:
        config["use_second_probe"] = not config.get("use_second_probe", False)
    elif menu_index == index_offset + 8:
        config["max_temp_diff"] += dir
        if config["max_temp_diff"] < 0:
            config["max_temp_diff"] = 0
    elif menu_index == index_offset + 9:
        config["use_slow_pwm"] = not config.get("use_slow_pwm", True)

def save_menu_value():
    global editing, in_menu
    save_config(config)
    pid.Kp = config["Kp"]
    pid.Ki = config["Ki"]
    pid.Kd = config["Kd"]
    editing = False
    in_menu = False

def enter_menu_item():
    global editing, in_menu, heater_enabled
    if menu_index <= 5:
        editing = True
    elif menu_index == 6:
        run_autotune()
        in_menu = False
    elif menu_index == 7:
        enable_heater()
        in_menu = False

def run_autotune():
    draw_edit("Tuning...")
    new_kp, new_ki, new_kd = pid.find_best_pid(setpoint=target_temp, process_fn=lambda _: read_temp())
    oled.fill(0)
    oled.text("Update PID?", 0, 0)
    oled.text("Kp={:.1f}".format(new_kp), 0, 16)
    oled.text("Ki={:.1f}".format(new_ki), 0, 32)
    oled.text("Kd={:.1f}".format(new_kd), 0, 48)
    oled.show()
    time.sleep(1)
    while ENC_BTN.value() == 1:
        time.sleep(0.1)
    while ENC_BTN.value() == 0:
        time.sleep(0.1)
    config["Kp"] = new_kp
    config["Ki"] = new_ki
    config["Kd"] = new_kd
    save_config(config)
    pid.Kp, pid.Ki, pid.Kd = new_kp, new_ki, new_kd

# ====== MAIN LOOP ======
temp_samples = [(time.time(), read_temp())]
temp_stable = False
last_temp_time = time.time()

def beep():
    if config.get("use_buzzer", True):
        BUZZER.on()
        time.sleep(0.1)
        BUZZER.off()

# Safety: disable if temp rises too fast (>10°C/min) during stable phase
# Temp samples are collected in the loop to evaluate stability and rate of change

def handle_quick_buttons():
    global button1_pressed_time, button2_pressed_time, target_temp
    now = time.ticks_ms()

    if BUTTON1.value() == 0:
        if button1_pressed_time == 0:
            button1_pressed_time = now
        elif time.ticks_diff(now, button1_pressed_time) > 2000:
            config["button1_target"] = target_temp
            save_config(config)
            button1_pressed_time = 0
    else:
        if 0 < button1_pressed_time < 2000:
            target_temp = config.get("button1_target", 40)
            beep()
        button1_pressed_time = 0

    if BUTTON2.value() == 0:
        if button2_pressed_time == 0:
            button2_pressed_time = now
        elif time.ticks_diff(now, button2_pressed_time) > 2000:
            config["button2_target"] = target_temp
            save_config(config)
            button2_pressed_time = 0
    else:
        if 0 < button2_pressed_time < 2000:
            target_temp = config.get("button2_target", 80)
            beep()
        button2_pressed_time = 0

while True:
    global last_temp, last_temp_time
    handle_quick_buttons()
    handle_encoder()
    temp = read_temp()
    now = time.time()
    temp_samples.append((now, temp))
    temp_samples = [t for t in temp_samples if now - t[0] <= 60]

    if len(temp_samples) >= 2:
        t1, v1 = temp_samples[0]
        t2, v2 = temp_samples[-1]
        rate = abs(v2 - v1) / (t2 - t1 + 0.001)
        temp_stable = rate < (5 / 60.0)  # stable if <5°C/min

    if heater_enabled and temp_stable is False and len(temp_samples) >= 2:
        # Check if temperature rising too fast while system is supposed to be stable
        t1, v1 = temp_samples[-2]
        t2, v2 = temp_samples[-1]
        short_rate = abs(v2 - v1) / (t2 - t1 + 0.001)
        if short_rate > (10 / 60.0):  # 10°C/min max rate
            disable_heater()

    if heater_enabled and temp < config["min_temp"]:
        disable_heater()

    if heater_enabled:
        pid.setpoint = target_temp
        pid.update(temp)
        check_timeout()

    if in_menu:
        if editing:
            value = ["Yes" if config.get("use_buzzer", True) else "No", "Yes" if config.get("button_labels", True) else "No",
                config["min_temp"], config["max_temp"], config["Kp"], config["Ki"], config["Kd"], config["timeout"],
                "Yes" if config.get("use_relay", True) else "No",
                "Yes" if config.get("use_second_probe", False) else "No",
                config.get("max_temp_diff", 5),
                "Yes" if config.get("use_slow_pwm", True) else "No"
            ][menu_index]
            draw_edit(value)
        else:
            draw_menu()
    else:
        draw_main(temp)

    time.sleep(0.1)
