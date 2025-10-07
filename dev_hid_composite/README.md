# 🧠 Raspberry Pi Pico HID Firmware (Keyboard + Mouse + CP210x Serial Bridge)

This document explains how to **build, wire, flash, and test** the custom TinyUSB-based firmware used in the **Steam Login & CS2 Automation Project**.

---

## 🧩 Overview

The firmware allows the Raspberry Pi Pico to function simultaneously as:

- ✅ USB **Keyboard**
- ✅ USB **Mouse**
- ✅ Serial communication interface via **CP210x USB-UART bridge**

It is built on **TinyUSB HID Composite** firmware with absolute mouse control support.

---

## 🔌 Hardware Wiring (CP210x ↔ Pico)

| Pico Pin | CP210x Pin | Description |
|-----------|-------------|--------------|
| **GP0 (TX)** | **RX** | UART transmit from Pico |
| **GP1 (RX)** | **TX** | UART receive to Pico |
| **GND** | **GND** | Common ground |

- UART settings: **115200 baud, 8-N-1**
- **Important:** TX ↔ RX must be **crossed** — Pico TX → CP210x RX, Pico RX ← CP210x TX

### Connection Flow

```
Target PC ↔ CP210x ↔ Pico ↔ TinyUSB ↔ Target PC
```

---

## ⚙️ Firmware Setup

### 1️⃣ Clone Pico SDK and Examples
```bash
git clone -b master https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init
export PICO_SDK_PATH=$PWD
cd ..
git clone https://github.com/raspberrypi/pico-examples.git
```

### 2️⃣ Place the project folder
Put your project (e.g., `pico_hid_composite/`) inside `pico-examples`.

Example:
```bash
cp -r ~/pico_hid/dev_hid_composite ~/pico-examples/pico_hid_composite
```

### 3️⃣ Build
```bash
cd pico-examples/pico_hid_composite
mkdir build && cd build
cmake ..
make -j4
```

This generates:
```
dev_hid_composite.uf2
```

### 4️⃣ Flash the Pico
1. Hold **BOOTSEL**, connect the Pico to your PC via USB.
2. A new drive appears (RPI-RP2).
3. Drag-and-drop the `dev_hid_composite.uf2` file.

Pico reboots as a **USB HID keyboard + mouse + serial port**.

---

## 🧰 Testing Firmware

### 🖱️ Test Mouse Functionality
Run from your host machine:
```bash
python3 mouse_test.py --screen 1920x1080 --start 1 1 down 475 right 750 click
```
The Pico will move the mouse in the defined path (top-left → down → right → click).

### ⌨️ Test Keyboard Functionality
Use this command to simulate typing:
```bash
python3 - <<'EOF'
import sender_final as hid
ser = hid.open_serial('/dev/ttyUSB0', 115200)
hid.type_text(ser, "Pico Keyboard Test")
hid.press_and_release(ser, 0, 0x28)  # Press Enter
EOF
```

This should type `Pico Keyboard Test` on the target PC followed by Enter.

---

## 🧱 Firmware Features

- Composite HID device (keyboard + mouse)
- Absolute-position mouse mode (TinyUSB)
- Compatible with **Linux / Windows / macOS**
- Communication bridge via **CP210x serial** at 115200 baud

---

## 🧩 Integration Notes

- Works seamlessly with the host automation Python scripts (`sender_final.py`, `main.py`).
- Designed for real-time interaction with **Steam login automation** and **OCR-based UI detection**.

---

## 🧾 Troubleshooting

| Issue | Solution |
|--------|-----------|
| Pico not detected | Ensure it's flashed with the correct UF2. Check `dmesg | grep tty` |
| Mouse not moving | Verify the serial connection (`/dev/ttyUSB0`) and rebuild firmware |
| Wrong serial bridge | Install CP210x drivers on Windows |
| UART not communicating | Cross-check TX/RX wiring |

---

## ✅ Summary

1. Wire Pico ↔ CP210x (TX↔RX, GND↔GND).  
2. Build and flash `dev_hid_composite.uf2`.  
3. Test mouse + keyboard via Python scripts.  
4. Integrate with Steam automation scripts.  

---

**Author:** Muhammad Bilal (bilalrajput031@gmail.com)  
**Project:** Steam Login & CS2 Automation  
**Firmware Base:** TinyUSB HID Composite (Raspberry Pi Pico)