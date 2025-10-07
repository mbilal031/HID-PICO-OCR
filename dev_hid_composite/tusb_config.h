#pragma once
#include "tusb_option.h"

#ifndef CFG_TUSB_MCU
#define CFG_TUSB_MCU OPT_MCU_RP2040
#endif

#ifndef CFG_TUSB_OS
#define CFG_TUSB_OS OPT_OS_NONE
#endif

#define CFG_TUSB_RHPORT0_MODE   (OPT_MODE_DEVICE)
#define CFG_TUD_ENDPOINT0_SIZE  64

// Device classes
#define CFG_TUD_HID             1
#define CFG_TUD_HID_EP_BUFSIZE  16

// Optional (not used, but keep product-id map macros happy if enabled later)
#define CFG_TUD_CDC             0
#define CFG_TUD_MSC             0
#define CFG_TUD_MIDI            0
#define CFG_TUD_VENDOR          0
