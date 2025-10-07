#!/usr/bin/env python3
# clear_caps.py — utility to remove saved OCR screenshots

import os

CAP_DIR = "cap"

def clear_caps():
    if not os.path.exists(CAP_DIR):
        return
    for f in os.listdir(CAP_DIR):
        if f.lower().endswith(".png"):
            try:
                os.remove(os.path.join(CAP_DIR, f))
            except Exception as e:
                print(f"[!] Failed to delete {f}: {e}")
