# dev By Muhammad Bila (bilalrajput031@gmail.com)
#!/usr/bin/env python3
# main.py — Steam login automation with HID + OCR + Guard code module

import time, argparse, os, shutil
import sender_final as hid
import ocr_helper
import guard_code
import clear_caps
import defines
from ocr_helper import ocr_text, detect_popup, detect_phrase


# --------- HID Key helpers ----------
def press(ser, mod, kc):
    hid.press_and_release(ser, mod, kc)

def hit_enter(ser):
    try:
        hid.type_text(ser, "\n")
    except Exception:
        press(ser, 0, defines.KC_ENTER)

def alt_tab(ser, times=1, delay=0.15):
    for _ in range(times):
        press(ser, defines.MOD_LALT, defines.KC_TAB)
        time.sleep(delay)

def esc(ser):
    press(ser, 0, defines.KC_ESC)
    time.sleep(0.08)

def _type_path_safe(ser, text):
    for ch in text:
        if ch == ' ':
            press(ser, 0, 0x2C)
        elif ch == '\\':
            press(ser, 0, 0x31)
        elif ch == ':':
            press(ser, defines.MOD_LSHIFT, 0x33)
        elif ch == '.':
            press(ser, 0, 0x37)
        elif ch == '"':
            press(ser, defines.MOD_LSHIFT, 0x34)
        elif ch == '-':
            press(ser, 0, 0x2D)
        elif ch == '_':
            press(ser, defines.MOD_LSHIFT, 0x2D)
        elif ch == '(':
            press(ser, defines.MOD_LSHIFT, 0x26)
        elif ch == ')':
            press(ser, defines.MOD_LSHIFT, 0x27)
        elif 'a' <= ch <= 'z':
            kc = 0x04 + (ord(ch) - ord('a'))
            press(ser, 0, kc)
        elif 'A' <= ch <= 'Z':
            kc = 0x04 + (ord(ch.lower()) - ord('a'))
            press(ser, defines.MOD_LSHIFT, kc)
        elif '0' <= ch <= '9':
            kc = 0x27 if ch == '0' else 0x1E + (ord(ch) - ord('1'))
            press(ser, 0, kc)
        time.sleep(0.002)


# --------- CS2 launcher ----------
def launch_cs2(ser):
    steam_path = r"C:\Program Files (x86)\Steam\steam.exe"
    params = '-silent -nofriendsui -no-dwrite -worldwide -language english -applaunch 730'
    command = f'"{steam_path}" {params}'

    alt_tab(ser, times=2)
    esc(ser)
    press(ser, defines.MOD_LGUI, 0x15)   # Win+R
    time.sleep(0.5)
    _type_path_safe(ser, command)
    hit_enter(ser)
    print("[i] Launched Steam/CS2 with parameters.")
    time.sleep(2.0)


# --------- Steam path helper ----------
def get_steam_base():
    candidates = [
        r"C:\Program Files (x86)\Steam",
        r"C:\Program Files\Steam",
        r"D:\Steam",
        r"D:\Program Files (x86)\Steam",
        r"D:\Program Files\Steam",
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return r"C:\Program Files (x86)\Steam"


# --------- Central popup handler ----------
def handle_popup(ser, popup):
    if popup == "invalid_login":
        print("[!] Wrong username/password detected.")
        return "stop"

    if popup == "invalid_guard":
        print("[!] Invalid Steam Guard code detected.")
        for _ in range(6):
            press(ser, 0, 0x2A)
            time.sleep(0.04)
        return "stop"

    if popup == "cloud_sync":
        print("[i] Cloud Sync popup detected. Running fixed path...")

        W, H = 1920, 1080
        ABS_MAX = 32767

        def px_to_abs(n_px, max_px, abs_max=ABS_MAX):
            if n_px < 0: n_px = 0
            if n_px > max_px: n_px = max_px
            return int(round(n_px * abs_max / max_px))

        def send_abs(x_px, y_px, click=False):
            x_abs, y_abs = px_to_abs(x_px, W-1), px_to_abs(y_px, H-1)
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

        # Step 1: top-left
        x, y = 5, 5
        send_abs(x, y)
        time.sleep(0.3)

        # Step 2: down 475
        y += 475
        send_abs(x, y)
        time.sleep(0.3)

        # Step 3: right 750
        x += 750
        send_abs(x, y)
        time.sleep(0.3)

        # Step 4: single click
        send_abs(x, y, click=True)
        print(f"[✓] Clicked Play Anyway at approx {x},{y}")
        time.sleep(2.0)

        # ✅ Clear caps after successful Play Anyway click
        clear_caps.clear_caps()
        print("[i] CapsLock cleared after Play Anyway click.")
        return "handled"

    if popup == "update_required" or "updating" in popup.lower():
        print("[i] Update in progress — waiting until it finishes...")
        start = time.time()
        while time.time() - start < 1200:
            try:
                frame, path = ocr_helper.grab_full_frame()
                text, _ = ocr_text(frame)
            except RuntimeError:
                time.sleep(2)
                continue

            try: os.remove(path)
            except: pass

            if "updating" not in text.lower() and detect_popup(frame) != "update_required":
                print("[i] Update finished.")
                return "handled"

            time.sleep(5)

        print("[!] Timeout waiting for update to finish.")
        return "stop"

# --------- Logout handler ----------
def logout_steam(ser):
    steam_path = r'C:\Program Files (x86)\Steam\steam.exe'
    command = f'"{steam_path}" -shutdown'

    # Send shutdown
    alt_tab(ser, times=2)
    esc(ser)
    press(ser, defines.MOD_LGUI, 0x15)  # Win+R
    time.sleep(0.5)
    _type_path_safe(ser, command)
    hit_enter(ser)
    print("[i] Sent Steam -shutdown (logout).")
    time.sleep(2.0)

     # Run steam_cleaner.py via python
    cleaner_cmd = r'"C:\Users\Saad_\Desktop\steam_cleaner.exe"'
    press(ser, defines.MOD_LGUI, 0x15)  # Win+R
    time.sleep(0.5)
    _type_path_safe(ser, cleaner_cmd)
    hit_enter(ser)
    print("[i] Executed SteamCleaner (Python).")
    time.sleep(5.0)

# --------- Main Flow ----------
def main():
    ap = argparse.ArgumentParser(description="Steam login/logout with OCR")
    ap.add_argument('--port', default='/dev/ttyUSB0')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--logout-only', action='store_true')
    args = ap.parse_args()

    print("[i] Config:")
    print(f"    Port : {args.port}@{args.baud}")

    if args.logout_only:
        ser = hid.open_serial(port=args.port, baud=args.baud)
        logout_steam(ser)
        try: ser.close()
        except: pass
        return

    ser = hid.open_serial(port=args.port, baud=args.baud)
    try:
        print("[i] Waiting for Steam login screen (loop)...")
        while True:
            try: frame, path = ocr_helper.grab_frame()
            except RuntimeError:
                time.sleep(defines.POLL_INTERVAL)
                continue

            text, _ = ocr_text(frame)
            low = text.lower()

            if "library" in low or "store" in low:
                print("[i] Steam already logged in — skipping login flow.")
                try: os.remove(path)
                except: pass
                break

            if "sign in" in low and "password" in low:
                print("[i] Steam login screen detected.")
                alt_tab(ser, times=2)
                esc(ser)
                print("[i] Typing username…")
                hid.type_text(ser, defines.USERNAME)
                press(ser, 0, defines.KC_TAB)
                time.sleep(defines.AFTER_USERNAME_PAUSE)
                print("[i] Typing password…")
                hid.type_text(ser, defines.PASSWORD)
                time.sleep(defines.AFTER_PASSWORD_PAUSE)
                hit_enter(ser)
                try: os.remove(path)
                except: pass
                break

            popup = detect_popup(frame)
            if popup:
                action = handle_popup(ser, popup)
                try: os.remove(path)
                except: pass
                if action == "stop":
                    return

            try: os.remove(path)
            except: pass
            time.sleep(defines.POLL_INTERVAL)

        print("[i] Watching for guard/errors/popups...")
        guard_done = False

        while True:
            try: frame, path = ocr_helper.grab_frame()
            except RuntimeError:
                time.sleep(defines.POLL_INTERVAL)
                continue

            text, _ = ocr_text(frame)
            low = text.lower()

            if any(p in low for p in defines.PHRASES_INVALID_GUARD):
                print("[!] Invalid guard detected.")
                for _ in range(6):
                    press(ser, 0, 0x2A)
                    time.sleep(0.04)
                try: os.remove(path)
                except: pass
                continue

            if any(p in low for p in defines.PHRASES_GUARD):
                print("[i] Steam Guard prompt detected.")
                code = guard_code.get_guard_code()
                hid.type_text(ser, code)
                hit_enter(ser)
                guard_done = True
                try: os.remove(path)
                except: pass
                continue

            if guard_done:
                print("[✓] Guard accepted — launching CS2.")
                launch_cs2(ser)
                time.sleep(0.5)
                print("[i] Watching for Cloud Sync / Play Anyway / Update popups...")
                while True:
                    try: frame, path = ocr_helper.grab_full_frame()
                    except RuntimeError:
                        time.sleep(0.5)
                        continue
                    popup = detect_popup(frame)
                    if popup:
                        action = handle_popup(ser, popup)
                        try: os.remove(path)
                        except: pass
                        if action == "stop": return
                    time.sleep(1.0)

            try: os.remove(path)
            except: pass
            time.sleep(defines.POLL_INTERVAL)

    finally:
        try: clear_caps.clear_caps()
        except: pass
        print("[i] Serial kept alive (not closed).")


# --------- ENTRY POINT ----------
if __name__ == "__main__":
    main()
