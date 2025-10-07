#!/usr/bin/env python3
# hid_pico.py — unified UART→HID sender for Pico bridge
import time, argparse, serial
from serial.tools import list_ports

# ---------- Protocol ----------
PKT_MAGIC  = 0xAA
TYPE_MOUSE = 0x01
TYPE_KBD   = 0x02

BAUD = 115200
PKT_PAUSE   = 0.002  # gap between packets
KEY_DOWN_MS = 15      # key hold

MOD_LSHIFT = 0x02

# ---------- ASCII → HID map ----------
ASCII_MAP = {
    **{c:(0,0x04+i) for i,c in enumerate("abcdefghijklmnopqrstuvwxyz")},
    **{c:(0,0x1e+i) for i,c in enumerate("1234567890")},
    '\n':(0,0x28), '\r':(0,0x28), '\t':(0,0x2b), ' ':(0,0x2c),
    '-':(0,0x2d),'=':(0,0x2e),'[':(0,0x2f),']':(0,0x30),'\\':(0,0x31),
    ';':(0,0x33),"'":(0,0x34),'`':(0,0x35),',':(0,0x36),'.':(0,0x37),'/':(0,0x38),
    '!':(MOD_LSHIFT,0x1e),'@':(MOD_LSHIFT,0x1f),'#':(MOD_LSHIFT,0x20),
    '$':(MOD_LSHIFT,0x21),'%':(MOD_LSHIFT,0x22),'^':(MOD_LSHIFT,0x23),
    '&':(MOD_LSHIFT,0x24),'*':(MOD_LSHIFT,0x25),'(':(MOD_LSHIFT,0x26),
    ')':(MOD_LSHIFT,0x27),'_':(MOD_LSHIFT,0x2d),'+':(MOD_LSHIFT,0x2e),
    '{':(MOD_LSHIFT,0x2f),'}':(MOD_LSHIFT,0x30),'|':(MOD_LSHIFT,0x31),
    ':':(MOD_LSHIFT,0x33),'"':(MOD_LSHIFT,0x34),'~':(MOD_LSHIFT,0x35),
    '<':(MOD_LSHIFT,0x36),'>':(MOD_LSHIFT,0x37),'?':(MOD_LSHIFT,0x38),
}

# ---------- serial helpers ----------
def autodetect_port():
    for p in list_ports.comports():
        if (p.vid, p.pid) in [(0x0403,0x6001),(0x10C4,0xEA60)]:  # FTDI/CP210x
            return p.device
    ports = [p.device for p in list_ports.comports()]
    return ports[0] if ports else None

def open_serial(port, baud=BAUD):
    dev = port or autodetect_port()
    if not dev: raise RuntimeError("No serial port found")
    print(f"[i] Using {dev} @ {baud}")
    return serial.Serial(dev, baud, timeout=1)

def send_packet(ser, ptype, payload):
    payload = bytes(payload)
    cs = (ptype + len(payload) + sum(payload)) & 0xFF
    ser.write(bytes([PKT_MAGIC, ptype, len(payload)]) + payload + bytes([cs]))
    ser.flush()
    time.sleep(PKT_PAUSE)

# ---------- keyboard ----------
def send_keyboard_report(ser, modifiers=0, keys=None):
    keys = (keys or [])[:6] + [0]*max(0, 6-len(keys or []))
    send_packet(ser, TYPE_KBD, [modifiers] + keys)

def press_and_release(ser, mod, kc, hold_ms=KEY_DOWN_MS):
    send_keyboard_report(ser, mod, [kc])
    time.sleep(max(0.001, hold_ms/1000.0))
    send_keyboard_report(ser, 0, [])

def type_text(ser, text):
    for ch in text:
        if ch == '\r': ch = '\n'
        if 'A' <= ch <= 'Z':
            mod, kc = MOD_LSHIFT, 0x04 + (ord(ch.lower())-ord('a'))
        elif ch in ASCII_MAP:
            mod, kc = ASCII_MAP[ch]
        else:
            print(f"[w] skip unmapped char: {repr(ch)}"); continue
        press_and_release(ser, mod, kc)

# ---------- mouse ----------
def send_mouse(ser, buttons=0, dx=0, dy=0, wheel=0, hscroll=0):
    payload = [
        buttons & 0x1F,
        (dx + 256) % 256,
        (dy + 256) % 256,
        (wheel + 256) % 256,
        (hscroll + 256) % 256,
    ]
    send_packet(ser, TYPE_MOUSE, payload)

def move_steps(ser, dx, dy):
    sx = 1 if dx >= 0 else -1
    sy = 1 if dy >= 0 else -1
    for _ in range(abs(dx)): send_mouse(ser, dx=sx)
    for _ in range(abs(dy)): send_mouse(ser, dy=sy)

def click(ser, which="left"):
    m = {"left":1, "right":2, "middle":4}[which]
    send_mouse(ser, buttons=m)
    send_mouse(ser, buttons=0)

def drag(ser, dx, dy, which="left"):
    m = {"left":1, "right":2, "middle":4}[which]
    send_mouse(ser, buttons=m)
    move_steps(ser, dx, dy)
    send_mouse(ser, buttons=0)

def scroll(ser, vertical=0, horizontal=0):
    send_mouse(ser, wheel=vertical, hscroll=horizontal)

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="UART→HID commands for Pico")
    ap.add_argument("--port", help="serial port (/dev/ttyUSB0, COM7, etc.)")
    ap.add_argument("--baud", type=int, default=BAUD)

    sub = ap.add_subparsers(dest="cmd")

    kbd = sub.add_parser("text");   kbd.add_argument("s", help="text to type")
    kbd.add_argument("--enter", action="store_true")

    mv = sub.add_parser("move");    mv.add_argument("dx", type=int); mv.add_argument("dy", type=int)
    ck = sub.add_parser("click");   ck.add_argument("--btn", choices=["left","right","middle"], default="left")
    dr = sub.add_parser("drag");    dr.add_argument("dx", type=int); dr.add_argument("dy", type=int)
    dr.add_argument("--btn", choices=["left","right","middle"], default="left")
    sc = sub.add_parser("scroll");  sc.add_argument("--v", type=int, default=0); sc.add_argument("--h", type=int, default=0)

    args = ap.parse_args()
    with open_serial(args.port, args.baud) as ser:
        time.sleep(0.3)
        if args.cmd == "text":
            type_text(ser, args.s)
            if args.enter: press_and_release(ser, 0, 0x28)
        elif args.cmd == "move":
            move_steps(ser, args.dx, args.dy)
        elif args.cmd == "click":
            click(ser, args.btn)
        elif args.cmd == "drag":
            drag(ser, args.dx, args.dy, args.btn)
        elif args.cmd == "scroll":
            scroll(ser, args.v, args.h)
        else:
            print("No command given. Try 'text', 'move', 'click', 'drag', or 'scroll'.")

if __name__ == "__main__":
    main()
