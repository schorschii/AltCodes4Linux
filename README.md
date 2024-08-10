# AltCodes4Linux

This script makes it possible to enter "alt codes" with a keyboard device on the Linux desktop as known from Windows.

On Windows, when you hold the left ALT key and enter the **decimal** number of a char (ASCII/cp850/cp1252) on the numpad, the corresponding char is inserted at the current position when releasing the ALT key. The behavior is different if you want to insert a special char on the Linux desktop: here, you need to press CTRL+SHIFT+u, followed by the **hexadecimal** Unicode code point and ENTER.

This script captures the events of an input device and when recognizing alt codes, it converts them into appropriate keystrokes for the Linux desktop.

This is necessary for compatibility with keyboard-like devices which cannot be configured otherwise, e.g. some barcode scanners or RFID card readers.

## Usage
1. Install packages: `apt install python3-evdev evtest`.
2. Find your input device with `evtest`.
3. Start the script: `./altcodes4linux.py /dev/input/event19`.  
   Since the event device number can change depending on the order the devices are recognized, you should rather use the device path by id, e.g. `/dev/input/by-id/usb-<YOUR-RFID-READER-NAME>`.  
   Put the script call in your autostart.
4. Enter an alt code on the selected device and have fun!
