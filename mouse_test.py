#!/usr/bin/env python3
# fixed_mouse_path.py
# Always moves: top-left -> down 475 -> right 750 -> single click
# (double-click test included, just comment out if not needed)

import argparse, time
import sender_final as hid

ABS_MAX = 32767

def px_to_abs(n_px, max_px, abs_max=ABS_MAX):
    if n_px < 0: n_px = 0
    if n_px > max_px: n_px = max_px
    return int(round(n_px * abs_max / max_px))

def send_abs(ser, x_abs, y_abs, click=False):
    payload = [
        x_abs & 0xFF, (x_abs >> 8) & 0xFF,
        y_abs & 0xFF, (y_abs >> 8) & 0xFF,
        1 if click else 0
    ]
    hid.send_packet(ser, hid.TYPE_MOUSE, payload)
    if click:
        time.sleep(0.03)
        payload[-1] = 0
        hid.send_packet(ser, hid.TYPE_MOUSE, payload)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--screen", required=True, help="e.g. 1920x1080")
    args = ap.parse_args()

    W, H = [int(x) for x in args.screen.lower().split("x")]
    ser = hid.open_serial(args.port, args.baud)

    # Step 1: top-left
    x_px, y_px = 5, 5
    x_abs, y_abs = px_to_abs(x_px, W-1), px_to_abs(y_px, H-1)
    send_abs(ser, x_abs, y_abs)
    print(f"Step 1: moved to {x_px},{y_px}")
    time.sleep(0.3)

    # Step 2: down 475
    y_px += 475
    x_abs, y_abs = px_to_abs(x_px, W-1), px_to_abs(y_px, H-1)
    send_abs(ser, x_abs, y_abs)
    print(f"Step 2: moved to {x_px},{y_px}")
    time.sleep(0.3)

    # Step 3: right 750
    x_px += 750
    x_abs, y_abs = px_to_abs(x_px, W-1), px_to_abs(y_px, H-1)
    send_abs(ser, x_abs, y_abs)
    print(f"Step 3: moved to {x_px},{y_px}")
    time.sleep(0.3)

    # Step 4a: single click
    send_abs(ser, x_abs, y_abs, click=True)
    print(f"Step 4a: single click at {x_px},{y_px}")
    time.sleep(0.3)

    # Step 4b: double-click test (comment this out if not needed)
    for i in range(2):
        send_abs(ser, x_abs, y_abs, click=True)
        print(f"Step 4b.{i+1}: double-click test at {x_px},{y_px}")
        time.sleep(0.15)

if __name__ == "__main__":
    main()
