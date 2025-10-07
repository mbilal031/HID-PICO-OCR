
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>

#include "pico/stdlib.h"
#include "hardware/uart.h"
#include "hardware/gpio.h"

#include "bsp/board_api.h"
#include "tusb.h"
#include "usb_descriptors.h"

// ------------------------- Blink patterns -------------------------
enum
{
  BLINK_NOT_MOUNTED = 250,
  BLINK_MOUNTED = 1000,
  BLINK_SUSPENDED = 2500,
};
static uint32_t blink_interval_ms = BLINK_NOT_MOUNTED;

static void led_blinking_task(void);

// ------------------------- UART setup -----------------------------
#define UART_ID uart0
#define UART_BAUD 115200
#define UART_TX_PIN 0 // GP0  (Pico UART0 TX) -> CP2102 RX
#define UART_RX_PIN 1 // GP1  (Pico UART0 RX) -> CP2102 TX

// Packet format: 0xAA, TYPE, LEN, PAYLOAD[LEN], CHKSUM8(TYPE+LEN+payload)
#define PKT_MAGIC 0xAA

enum
{
  TYPE_MOUSE = 0x01,
  TYPE_KBD   = 0x02
};

static inline uint8_t csum8(uint8_t type, uint8_t len, const uint8_t *p)
{
  uint16_t s = type + len;
  for (uint8_t i = 0; i < len; i++) s += p[i];
  return (uint8_t)(s & 0xFF);
}

typedef enum
{
  S_MAGIC,
  S_TYPE,
  S_LEN,
  S_PAYLOAD,
  S_CHK
} rx_state_t;

static rx_state_t rx_state = S_MAGIC;
static uint8_t rx_type, rx_len, rx_buf[64], rx_pos;

static void handle_mouse(const uint8_t *p, uint8_t len)
{
  if (len < 5 || !tud_hid_ready()) return;
  uint16_t x = (uint16_t)p[0] | ((uint16_t)p[1] << 8);
  uint16_t y = (uint16_t)p[2] | ((uint16_t)p[3] << 8);
  uint8_t  buttons = p[4];

  for (int i=0; i<3; i++) {
    tud_hid_abs_mouse_report(REPORT_ID_MOUSE, buttons, (int16_t)x, (int16_t)y, 0, 0);
    sleep_ms(10);
  }
}



static void handle_keyboard(const uint8_t *p, uint8_t len)
{
  if (len < 7 || !tud_hid_ready()) return;

  uint8_t mods = p[0];
  uint8_t keys[6];
  memcpy(keys, &p[1], 6);
  tud_hid_keyboard_report(REPORT_ID_KEYBOARD, mods, keys);
}

static void handle_packet(uint8_t type, uint8_t len, uint8_t *p)
{
  // Remote wakeup if suspended
  if (tud_suspended()) tud_remote_wakeup();

  switch (type)
  {
    case TYPE_MOUSE: handle_mouse(p, len); break;
    case TYPE_KBD  : handle_keyboard(p, len); break;
    default: break;
  }
}

// ------------------------- TinyUSB callbacks ----------------------
void tud_mount_cb(void)   { blink_interval_ms = BLINK_MOUNTED;   }
void tud_umount_cb(void)  { blink_interval_ms = BLINK_NOT_MOUNTED; }
void tud_suspend_cb(bool remote_wakeup_en)
{
  (void)remote_wakeup_en;
  blink_interval_ms = BLINK_SUSPENDED;
}
void tud_resume_cb(void)
{
  blink_interval_ms = tud_mounted() ? BLINK_MOUNTED : BLINK_NOT_MOUNTED;
}

uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id,
                               hid_report_type_t report_type, uint8_t *buffer, uint16_t reqlen)
{
  (void)instance; (void)report_id; (void)report_type; (void)buffer; (void)reqlen;
  return 0; // Not used
}

void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id,
                           hid_report_type_t report_type, uint8_t const *buffer, uint16_t bufsize)
{
  (void)instance; (void)report_type;

  // Keyboard LED feedback (CapsLock)
  if (report_id == REPORT_ID_KEYBOARD && bufsize >= 1)
  {
    uint8_t leds = buffer[0];
    if (leds & KEYBOARD_LED_CAPSLOCK)
    {
      blink_interval_ms = 0;
      board_led_write(true);
    }
    else
    {
      board_led_write(false);
      blink_interval_ms = BLINK_MOUNTED;
    }
  }
}

// ------------------------- LED blinking task ----------------------
static void led_blinking_task(void)
{
  static uint32_t start_ms = 0;
  static bool led_state = false;

  if (!blink_interval_ms) return;
  if (board_millis() - start_ms < blink_interval_ms) return;
  start_ms += blink_interval_ms;

  board_led_write(led_state);
  led_state = !led_state;
}

// ------------------------- MAIN ----------------------------------
int main(void)
{
  board_init();
  tusb_init();

  // UART init
  uart_init(UART_ID, UART_BAUD);
  gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
  gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

  absolute_time_t pkt_deadline = delayed_by_ms(get_absolute_time(), 100);

  while (1)
  {
    tud_task();          // USB
    led_blinking_task(); // status LED

    // UART RX state machine (non-blocking)
    while (uart_is_readable(UART_ID))
    {
      uint8_t b = uart_getc(UART_ID);

      // simple LED toggle on any received byte (non-blocking)
      gpio_xor_mask(1u << PICO_DEFAULT_LED_PIN);

      switch (rx_state)
      {
        case S_MAGIC:
          if (b == PKT_MAGIC)
          {
            rx_state = S_TYPE;
            pkt_deadline = delayed_by_ms(get_absolute_time(), 100);
          }
          break;

        case S_TYPE:
          rx_type = b;
          rx_state = S_LEN;
          pkt_deadline = delayed_by_ms(get_absolute_time(), 100);
          break;

        case S_LEN:
          rx_len = b;
          if (rx_len > sizeof(rx_buf))
          {
            rx_state = S_MAGIC;
            break;
          }
          rx_pos = 0;
          rx_state = S_PAYLOAD;
          pkt_deadline = delayed_by_ms(get_absolute_time(), 100);
          break;

        case S_PAYLOAD:
          rx_buf[rx_pos++] = b;
          if (rx_pos >= rx_len) rx_state = S_CHK;
          break;

        case S_CHK:
        {
          uint8_t want = csum8(rx_type, rx_len, rx_buf);
          if (want == b) handle_packet(rx_type, rx_len, rx_buf);
          rx_state = S_MAGIC;
        }
        break;
      }
    }

    // parser timeout recovery
    if (rx_state != S_MAGIC && absolute_time_diff_us(get_absolute_time(), pkt_deadline) < 0)
    {
      rx_state = S_MAGIC;
    }
  }
}

