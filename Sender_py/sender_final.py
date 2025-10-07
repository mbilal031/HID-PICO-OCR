#!/usr/bin/env python3
# sender_final.py — serial HID bridge helpers (keyboard + mouse)

import time, serial
from serial.tools import list_ports

PKT_MAGIC  = 0xAA
TYPE_MOUSE = 0x01
TYPE_KBD   = 0x02

BAUD = 115200
PKT_PAUSE = 0.002

# Keyboard modifiers
MOD_LSHIFT = 0x02

def autodetect_port():
    for p in list_ports.comports():
        if (p.vid, p.pid) in [(0x0403,0x6001),(0x10C4,0xEA60)]:  # FTDI/CP210x
            return p.device
    ports = [p.device for p in list_ports.comports()]
    return ports[0] if ports else None

def open_serial(port=None, baud=BAUD):
    dev = port or autodetect_port()
    if not dev:
        raise RuntimeError("No serial port found")
    print(f"[i] Using {dev} @ {baud}")
    return serial.Serial(dev, baud, timeout=1)

def send_packet(ser, ptype, payload):
    payload = bytes(payload)
    cs = (ptype + len(payload) + sum(payload)) & 0xFF
    ser.write(bytes([PKT_MAGIC, ptype, len(payload)]) + payload + bytes([cs]))
    ser.flush()
    time.sleep(PKT_PAUSE)

# ---------------- Keyboard ----------------
def send_keyboard_report(ser, modifiers=0, keys=None):
    keys = (keys or [])[:6] + [0]*max(0, 6-len(keys or []))
    send_packet(ser, TYPE_KBD, [modifiers] + keys)

def press_and_release(ser, mod, kc, hold_ms=15):
    send_keyboard_report(ser, mod, [kc])
    time.sleep(max(0.001, hold_ms/1000.0))
    send_keyboard_report(ser, 0, [])

def type_text(ser, text):
    for ch in text:
        if ch == '\r': ch = '\n'
        if 'A' <= ch <= 'Z':
            mod, kc = MOD_LSHIFT, 0x04 + (ord(ch.lower())-ord('a'))
        elif 'a' <= ch <= 'z':
            mod, kc = 0, 0x04 + (ord(ch)-ord('a'))
        elif '0' <= ch <= '9':
            mod, kc = 0, 0x27 if ch == '0' else 0x1e + (ord(ch)-ord('1'))
        elif ch == '\n':
            mod, kc = 0, 0x28
        else:
            continue
        press_and_release(ser, mod, kc)

# ---------------- Mouse ----------------
# Set these once to match the TARGET PC screen resolution
SCREEN_W = 1920
SCREEN_H = 1080

def mouse_move_click(ser, x_px, y_px):
    """
    Move to (x_px,y_px) in screen pixels and click.
    If coords look like they came from the 800x600 center ROI, de-crop first.
    Scales to TinyUSB absolute range 0..32767 for the Pico firmware.
    """
    # --- de-crop if OCR used 800x600 center area ---
    if x_px < 1000 and y_px < 700:  # typical ROI numbers
        roi_w, roi_h = 800, 600
        off_x = (SCREEN_W - roi_w) // 2
        off_y = (SCREEN_H - roi_h) // 2
        x_px = off_x + x_px
        y_px = off_y + y_px

    # --- scale pixels -> absolute HID (0..32767) ---
    XMAX = 32767
    YMAX = 32767
    x_abs = max(0, min(XMAX, int(round(x_px * XMAX / (SCREEN_W - 1)))))
    y_abs = max(0, min(YMAX, int(round(y_px * YMAX / (SCREEN_H - 1)))))

    # payload for Pico: [x_lo, x_hi, y_lo, y_hi, buttons]
    def _send(xa, ya, btn):
        payload = [xa & 0xFF, (xa >> 8) & 0xFF, ya & 0xFF, (ya >> 8) & 0xFF, btn]
        send_packet(ser, TYPE_MOUSE, payload)

    try:
        # move (no button), send twice to be sticky
        _send(x_abs, y_abs, 0); time.sleep(0.01)
        _send(x_abs, y_abs, 0); time.sleep(0.01)
        # click down
        _send(x_abs, y_abs, 1); time.sleep(0.03)
        # release
        _send(x_abs, y_abs, 0); time.sleep(0.03)
        # reinforce position once more (helps on some systems)
        _send(x_abs, y_abs, 0); time.sleep(0.01)
    except Exception as e:
        print(f"[!] Mouse click failed: {e}")
