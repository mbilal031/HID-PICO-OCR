/*
 * The MIT License (MIT)
 */
#include "bsp/board_api.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include <string.h>

/* A combination of interfaces must have a unique product id ... */
#define _PID_MAP(itf, n)  ( (CFG_TUD_##itf) << (n) )
#define USB_PID           (0x4000 | _PID_MAP(CDC, 0) | _PID_MAP(MSC, 1) | _PID_MAP(HID, 2) | \
                           _PID_MAP(MIDI, 3) | _PID_MAP(VENDOR, 4) )

#define USB_VID   0xCafe
#define USB_BCD   0x0200

//--------------------------------------------------------------------+
// Device Descriptors
//--------------------------------------------------------------------+
tusb_desc_device_t const desc_device =
{
    .bLength            = sizeof(tusb_desc_device_t),
    .bDescriptorType    = TUSB_DESC_DEVICE,
    .bcdUSB             = USB_BCD,
    .bDeviceClass       = 0x00,
    .bDeviceSubClass    = 0x00,
    .bDeviceProtocol    = 0x00,
    .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,

    .idVendor           = USB_VID,
    .idProduct          = USB_PID,
    .bcdDevice          = 0x0100,

    .iManufacturer      = 0x01,
    .iProduct           = 0x02,
    .iSerialNumber      = 0x03,

    .bNumConfigurations = 0x01
};

uint8_t const * tud_descriptor_device_cb(void)
{
  return (uint8_t const *) &desc_device;
}

// HID Report Descriptor (kbd + abs mouse + consumer + gamepad)
// Absolute Mouse report descriptor: X/Y 16-bit absolute coords (0–32767)
#define TUD_HID_REPORT_DESC_ABS_MOUSE(...) \
  HID_USAGE_PAGE ( HID_USAGE_PAGE_DESKTOP     ) ,\
  HID_USAGE      ( HID_USAGE_DESKTOP_MOUSE   ) ,\
  HID_COLLECTION ( HID_COLLECTION_APPLICATION),\
    __VA_ARGS__                                  /* <- DO NOT add comma here */ \
    HID_USAGE      ( HID_USAGE_DESKTOP_POINTER ),\
    HID_COLLECTION ( HID_COLLECTION_PHYSICAL   ),\
      /* Buttons (3) */ \
      HID_USAGE_PAGE   ( HID_USAGE_PAGE_BUTTON ),\
        HID_USAGE_MIN    ( 1                    ),\
        HID_USAGE_MAX    ( 3                    ),\
        HID_LOGICAL_MIN  ( 0                    ),\
        HID_LOGICAL_MAX  ( 1                    ),\
        HID_REPORT_COUNT ( 3                    ),\
        HID_REPORT_SIZE  ( 1                    ),\
        HID_INPUT        ( HID_DATA | HID_VARIABLE | HID_ABSOLUTE ),\
        HID_REPORT_COUNT ( 1                    ),\
        HID_REPORT_SIZE  ( 5                    ),\
        HID_INPUT        ( HID_CONSTANT | HID_VARIABLE | HID_ABSOLUTE ),\
      /* Absolute X/Y (16-bit each) */ \
      HID_USAGE_PAGE   ( HID_USAGE_PAGE_DESKTOP ),\
        HID_USAGE        ( HID_USAGE_DESKTOP_X   ),\
        HID_USAGE        ( HID_USAGE_DESKTOP_Y   ),\
        HID_LOGICAL_MIN  ( 0                     ),\
        HID_LOGICAL_MAX_N( 32767, 2              ),\
        HID_REPORT_SIZE  ( 16                    ),\
        HID_REPORT_COUNT ( 2                     ),\
        HID_INPUT        ( HID_DATA | HID_VARIABLE | HID_ABSOLUTE ),\
    HID_COLLECTION_END ,\
  HID_COLLECTION_END

uint8_t const desc_hid_report[] =
{
  TUD_HID_REPORT_DESC_KEYBOARD( HID_REPORT_ID(REPORT_ID_KEYBOARD) ),
  TUD_HID_REPORT_DESC_ABS_MOUSE( HID_REPORT_ID(REPORT_ID_MOUSE) ),
  TUD_HID_REPORT_DESC_CONSUMER( HID_REPORT_ID(REPORT_ID_CONSUMER_CONTROL) ),
  TUD_HID_REPORT_DESC_GAMEPAD ( HID_REPORT_ID(REPORT_ID_GAMEPAD) )
};


uint8_t const * tud_hid_descriptor_report_cb(uint8_t instance)
{
  (void) instance;
  return desc_hid_report;
}

//--------------------------------------------------------------------+
// Configuration Descriptor
//--------------------------------------------------------------------+
enum { ITF_NUM_HID, ITF_NUM_TOTAL };
#define  CONFIG_TOTAL_LEN  (TUD_CONFIG_DESC_LEN + TUD_HID_DESC_LEN)
#define EPNUM_HID   0x81

uint8_t const desc_configuration[] =
{
  TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, CONFIG_TOTAL_LEN, TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 100),
  TUD_HID_DESCRIPTOR(ITF_NUM_HID, 0, HID_ITF_PROTOCOL_NONE, sizeof(desc_hid_report),
                     EPNUM_HID, CFG_TUD_HID_EP_BUFSIZE, 5)
};

#if TUD_OPT_HIGH_SPEED
uint8_t desc_other_speed_config[CONFIG_TOTAL_LEN];
tusb_desc_device_qualifier_t const desc_device_qualifier =
{
  .bLength            = sizeof(tusb_desc_device_qualifier_t),
  .bDescriptorType    = TUSB_DESC_DEVICE_QUALIFIER,
  .bcdUSB             = USB_BCD,
  .bDeviceClass       = 0x00,
  .bDeviceSubClass    = 0x00,
  .bDeviceProtocol    = 0x00,
  .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,
  .bNumConfigurations = 0x01,
  .bReserved          = 0x00
};

uint8_t const* tud_descriptor_device_qualifier_cb(void)
{
  return (uint8_t const*) &desc_device_qualifier;
}

uint8_t const* tud_descriptor_other_speed_configuration_cb(uint8_t index)
{
  (void) index;
  memcpy(desc_other_speed_config, desc_configuration, CONFIG_TOTAL_LEN);
  desc_other_speed_config[1] = TUSB_DESC_OTHER_SPEED_CONFIG;
  return desc_other_speed_config;
}
#endif

uint8_t const * tud_descriptor_configuration_cb(uint8_t index)
{
  (void) index;
  return desc_configuration;
}

//--------------------------------------------------------------------+
// String Descriptors
//--------------------------------------------------------------------+
enum { STRID_LANGID = 0, STRID_MANUFACTURER, STRID_PRODUCT, STRID_SERIAL };

char const *string_desc_arr[] =
{
  (const char[]) { 0x09, 0x04 }, // English (0x0409)
  "TinyUSB",                     // Manufacturer
  "TinyUSB Device",              // Product
  NULL,                          // Serial uses unique ID if possible
};

static uint16_t _desc_str[32 + 1];

uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t langid) {
  (void) langid;
  size_t chr_count;

  switch ( index ) {
    case STRID_LANGID:
      memcpy(&_desc_str[1], string_desc_arr[0], 2);
      chr_count = 1;
      break;

    case STRID_SERIAL:
      chr_count = board_usb_get_serial(_desc_str + 1, 32);
      break;

    default:
      if ( !(index < sizeof(string_desc_arr) / sizeof(string_desc_arr[0])) ) return NULL;
      {
        const char *str = string_desc_arr[index];
        chr_count = strlen(str);
        size_t const max_count = sizeof(_desc_str) / sizeof(_desc_str[0]) - 1;
        if ( chr_count > max_count ) chr_count = max_count;
        for ( size_t i = 0; i < chr_count; i++ ) _desc_str[1 + i] = str[i];
      }
      break;
  }
  _desc_str[0] = (uint16_t) ((TUSB_DESC_STRING << 8) | (2 * chr_count + 2));
  return _desc_str;
}
