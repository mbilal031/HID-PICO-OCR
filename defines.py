import os

# ------------------- CONFIG -------------------
USERNAME = os.getenv("STEAM_USER", "mabelmaginnis8582") #mabelmaginnis8582
PASSWORD = os.getenv("STEAM_PASS", "qz5ngZk0wQC5L") #qz5ngZk0wQC5

STEAM_LAUNCH_WAIT      = 8.0
AFTER_USERNAME_PAUSE   = 0.2
AFTER_PASSWORD_PAUSE   = 0.2
POLL_INTERVAL          = 0.2
POPUP_TIMEOUT          = 12.0

# ------------------- OCR / CAPTURE CONFIG -------------------
DEVICE   = os.getenv("CAP_DEVICE", "/dev/video2")
SKIP_FRAMES = 30
WIDTH, HEIGHT = 1920, 1080
CAP_DIR = "cap"

# Crop region for Steam login
CROP_X1_PCT = 0.25
CROP_Y1_PCT = 0.18
CROP_X2_PCT = 0.75
CROP_Y2_PCT = 0.72

# ------------------- POPUP PHRASES -------------------
PHRASES_INVALID_LOGIN = [
    "please check your password",
    "account name and try again",
    "invalid login",
    "incorrect password",
    "wrong username"
]

PHRASES_GUARD = [
    "steam guard",
    "enter steam guard",
    "enter the code from your steam mobile app",
    "use backup code"
]

PHRASES_INVALID_GUARD = [
    "incorrect code",
    "incorrect code please try again",
    "incorrect code, please try again",
    "invalid code",
    "please try again",
    "try again code"
]

PHRASES_CLOUD_SYNC = [
   "cloud out of date",
    "play anyway",
    "play anyvvay",
    "play anvvay",
    "cloud sync"
]

# ------------------- HID KEYCODES -------------------
KC_ENTER = 0x28
KC_TAB   = 0x2B
KC_ESC   = 0x29

# Modifiers
MOD_LALT   = 0x04
MOD_LGUI   = 0x08
MOD_LSHIFT = 0x02
