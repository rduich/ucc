import time
from machine import Pin, PWM

class SimplePIDPWM:
    def __init__(self, pin, freq=1000, slow_pwm=False, pwm_period=2.0):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(freq)
        self.slow_pwm = slow_pwm
        self.pwm_period = pwm_period  # Seconds
        self.last_toggle = time.ticks_ms()

        self.setpoint = 0
        self.Kp = 1.0
        self.Ki = 0.0
        self.Kd = 0.0
        self._last_error = 0
        self._integral = 0
        self._last_time = time.ticks_ms()

    def update(self, measured_value):
        now = time.ticks_ms()
        dt = time.ticks_diff(now, self._last_time) / 1000.0
        if dt <= 0:
            return
        self._last_time = now

        error = self.setpoint - measured_value
        self._integral += error * dt
        derivative = (error - self._last_error) / dt
        self._last_error = error

        output = (
            self.Kp * error +
            self.Ki * self._integral +
            self.Kd * derivative
        )

        output = max(0, min(100, output))  # Clamp 0–100%
        self._apply_pwm(output)

    def _apply_pwm(self, duty_percent):
        if self.slow_pwm:
            now = time.ticks_ms()
            elapsed = time.ticks_diff(now, self.last_toggle) / 1000.0
            if elapsed >= self.pwm_period:
                self.last_toggle = now
                self._slow_pwm_cycle(duty_percent)
        else:
            self._set_duty_cycle(duty_percent)

    def _slow_pwm_cycle(self, duty_percent):
        on_time = self.pwm_period * (duty_percent / 100.0)
        off_time = self.pwm_period - on_time

        if on_time > 0:
            self._set_duty_cycle(100)
            time.sleep(on_time)
        if off_time > 0:
            self._set_duty_cycle(0)
            time.sleep(off_time)

    def _set_duty_cycle(self, percent):
        # 16-bit resolution
        duty = int(percent / 100.0 * 65535)
        self.pwm.duty_u16(duty)

    def auto_tune(self, process_fn, duration=10, relay_amp=20):
        print("Auto-tuning...")
        high = relay_amp
        low = 0
        values = []
        toggles = []
        start = time.time()
        output = high
        toggle_time = time.time()

        while time.time() - start < duration:
            value = process_fn(output)
            values.append(value)

            if time.time() - toggle_time > 1:
                output = high if output == low else low
                self._set_duty_cycle(output)
                toggles.append(time.time())
                toggle_time = time.time()

            time.sleep(0.1)

        if len(toggles) < 2:
            print("Not enough oscillation.")
            return

        period = (toggles[-1] - toggles[0]) / (len(toggles) - 1)
        amplitude = (max(values) - min(values)) / 2.0
        Ku = (4 * relay_amp) / (3.1415 * amplitude)
        Pu = period

        # Ziegler-Nichols Tuning
        self.Kp = 0.6 * Ku
        self.Ki = 1.2 * Ku / Pu
        self.Kd = 0.075 * Ku * Pu

        print("Tuned: Kp=%.2f Ki=%.2f Kd=%.2f" % (self.Kp, self.Ki, self.Kd))
        
        
        
        
'''   
#example usage:  
from simple_pid_pwm import SimplePIDPWM
import random
import time

# Fake temperature-like input
def read_temp_simulated(output_percent):
    base = 20 + output_percent * 0.05 + random.uniform(-0.2, 0.2)
    return base

pid = SimplePIDPWM(pin=15, slow_pwm=True, pwm_period=2.0)
pid.setpoint = 25

# Optional: auto-tune
pid.auto_tune(read_temp_simulated)

# Main control loop
while True:
    current_value = read_temp_simulated(0)  # Replace with actual sensor
    pid.update(current_value)
    print("Value:", current_value)
    time.sleep(1)
'''
