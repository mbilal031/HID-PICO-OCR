
import cv2, pytesseract, datetime, os
from pytesseract import Output
from defines import (
    DEVICE, SKIP_FRAMES, WIDTH, HEIGHT, CAP_DIR,
    CROP_X1_PCT, CROP_Y1_PCT, CROP_X2_PCT, CROP_Y2_PCT,
    PHRASES_INVALID_LOGIN, PHRASES_INVALID_GUARD, PHRASES_CLOUD_SYNC
)

os.makedirs(CAP_DIR, exist_ok=True)

def grab_frame(dev=DEVICE, skip=SKIP_FRAMES, width=WIDTH, height=HEIGHT):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if width:  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    for _ in range(max(0, skip)):
        cap.read()

    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError("Failed to capture a frame.")

    h, w = frame.shape[:2]
    x1 = int(w * CROP_X1_PCT); y1 = int(h * CROP_Y1_PCT)
    x2 = int(w * CROP_X2_PCT); y2 = int(h * CROP_Y2_PCT)
    cropped = frame[y1:y2, x1:x2].copy()

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(CAP_DIR, f"ocr_{ts}.png")
    cv2.imwrite(path, cropped)
    return cropped, path

# 🔥 New: full frame grab for Play Anyway popup
def grab_full_frame(dev=DEVICE, skip=SKIP_FRAMES, width=WIDTH, height=HEIGHT):
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if width:  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    for _ in range(max(0, skip)):
        cap.read()

    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError("Failed to capture a full frame.")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(CAP_DIR, f"ocr_full_{ts}.png")
    cv2.imwrite(path, frame)
    return frame, path

def grab_center_popup(dev=DEVICE, skip=SKIP_FRAMES, width=WIDTH, height=HEIGHT):
    """
    Capture full screen but crop only the center area
    where Steam popups (e.g., Cloud Out of Date, Play Anyway) usually appear.
    """
    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
    if width:  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    if height: cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    for _ in range(max(0, skip)):
        cap.read()

    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError("Failed to capture a frame.")

    h, w = frame.shape[:2]

    # crop center area (30%–70% width, 30%–70% height)
    x1, y1 = int(w * 0.3), int(h * 0.3)
    x2, y2 = int(w * 0.7), int(h * 0.7)

    cropped = frame[y1:y2, x1:x2].copy()

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(CAP_DIR, f"ocr_center_{ts}.png")
    cv2.imwrite(path, cropped)

    return cropped, path

def ocr_text(frame, delete_after=False, img_path=None):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    data = pytesseract.image_to_data(th, output_type=Output.DICT, config="--psm 6")
    words = [w for w in data.get("text", []) if w and w.strip()]

    if delete_after and img_path and os.path.exists(img_path):
        try: os.remove(img_path)
        except: pass

    return " ".join(words), data

def detect_phrase(frame, phrase="Play Anyway"):
    text, data = ocr_text(frame)
    if not data or "text" not in data: return None
    target = phrase.lower().split()
    words = [w.lower() for w in data["text"]]
    i = 0
    while i < len(words):
        if words[i] == target[0]:
            run = [i]; j = 1
            while j < len(target) and i + j < len(words) and words[i + j] == target[j]:
                run.append(i + j); j += 1
            if j == len(target):
                xs, ys, xe, ye = [], [], [], []
                for k in run:
                    conf = data["conf"][k]
                    try: ok_conf = (int(conf) >= 0)
                    except: ok_conf = True
                    if ok_conf and data["text"][k].strip():
                        xs.append(data["left"][k]); ys.append(data["top"][k])
                        xe.append(data["left"][k] + data["width"][k])
                        ye.append(data["top"][k] + data["height"][k])
                if xs:
                    x1, y1, x2, y2 = min(xs), min(ys), max(xe), max(ye)
                    return (x1, y1, x2, y2, (x1+x2)//2, (y1+y2)//2)
        i += 1
    return None

def detect_play_anyway(frame):
    """
    Detect 'Play anyway' button with extra preprocessing and fallback.
    """
    # invert colors to help with white-on-blue text
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    inv = cv2.bitwise_not(gray)
    _, th = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    data = pytesseract.image_to_data(th, output_type=Output.DICT, config="--psm 6")
    words = [w.lower() for w in data.get("text", []) if w.strip()]

    joined = "".join(words)
    if "playanyway" in joined or "play" in words or "anyway" in words:
        for i, word in enumerate(data["text"]):
            if word.strip().lower().startswith("play"):
                x1, y1 = data["left"][i], data["top"][i]
                x2 = x1 + data["width"][i]
                y2 = y1 + data["height"][i]
                return (x1, y1, x2, y2, (x1+x2)//2, (y1+y2)//2)

    return None


def detect_popup(frame, delete_after=False, img_path=None):
    text, _ = ocr_text(frame, delete_after=delete_after, img_path=img_path)
    t = text.lower()

    if any(p in t for p in PHRASES_INVALID_LOGIN):
        return "invalid_login"

    if any(p in t for p in PHRASES_INVALID_GUARD):
        return "invalid_guard"

    # ---- FIX: cloud sync / play anyway (tolerant) ----
    if any(p in t for p in PHRASES_CLOUD_SYNC) \
       or "play anyway" in t \
       or "play anyvvay" in t \
       or "play anvvay" in t \
       or "anyway" in t:
        return "cloud_sync"
    
    if "update" in t:
        return "update_required"

    return None

def detect_login_or_popup(frame, delete_after=False, img_path=None):
    text, _ = ocr_text(frame, delete_after=delete_after, img_path=img_path)
    t = text.lower()
    if "sign in" in t and "password" in t:
        return "login_screen"
    return detect_popup(frame, delete_after=delete_after, img_path=img_path)
