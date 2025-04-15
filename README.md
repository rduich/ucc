<p align="center"><strong><span style="color:red; font-size:20px;">⚠️ DISCLAIMER: This project is a concept and not yet fully tested. Use at your own risk!</span></strong></p>

# ☕ UCC – Universal Coffee Controller

**The UCC (Universal Coffee Controller)** is a customizable, feature-packed temperature control system based on the Raspberry Pi Pico. It’s designed for use in coffee machines, DIY espresso setups, steaming, or any application requiring smart and safe temperature control.

## 🎯 Features

- 🔁 **Advanced PID control** with on-device auto-tuning
- 🔥 **Slow or fast PWM** output (configurable)
- 🧠 **Persistent settings** stored in flash (`config.json`)
- 📟 **OLED interface** with menu system
- 🎚️ **Rotary encoder UI** for intuitive control
- 🧲 **Two configurable preset buttons** (e.g., Coffee / Steam)
- 🌡️ **One or two temperature probes**, with average temp and safety diff
- 🛎️ **Buzzer** for notifications (new target or stable temp reached)
- ⏱️ **Optional timeout** to auto-disable heater
- 🛡️ **Relay support** with safety cutoff below min temp
- 🔧 Full in-menu configuration: PID, limits, labels, relay, probes, buzzer...

## 🔌 Hardware Requirements

| Component             | Notes                            |
|----------------------|----------------------------------|
| Raspberry Pi Pico     | Main microcontroller             |
| SSD1306 OLED (I2C)    | 128x64 display                   |
| Rotary encoder         | With integrated push-button     |
| 2x Momentary buttons  | Preset selectors                 |
| Thermistor (e.g. NTC) | On ADC pin 26                   |
| Optional 2nd sensor    | On another ADC pin              |
| Heater output          | MOSFET/Relay/SSR on GPIO        |
| Relay safety output    | GPIO controlled                 |
| Buzzer                 | GPIO 19                          |

## 📁 Files

- `main.py` — main logic with UI and control loop
- `smart_pid_pwm.py` — PID control module with auto-tuning
- `config.json` — created on first run, stores settings

## 🧰 Setup

1. Flash your Pico with MicroPython
2. Copy `main.py` and `smart_pid_pwm.py` to the board
3. Wire components according to `main.py`
4. On first boot, defaults will be created and stored
5. Adjust settings from the menu using the rotary encoder

## 🔊 Preset Buttons

- Short press: instantly set configured temp (`Coffee`, `Steam`)
- Long press: save current target as that preset
- Labels and targets are configurable and stored

## 🛠️ Configurable via Menu

- Target temperature  
- Kp / Ki / Kd (PID tuning)  
- Min / Max temperature  
- Timeout (auto-off in minutes)  
- Enable/Disable:
  - Relay safety output
  - Buzzer alerts
  - Second temperature probe
  - PWM mode (slow or fast)
  - Preset labels  
- Run **auto-tune** with confirmation to apply results

## 🧪 Safety Features

- Heater **never starts enabled**
- Auto disable if temperature falls below minimum
- Auto disable on timeout
- Max temperature difference when using dual probes
- Persistent configuration with validation

## 🔐 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for full details.
