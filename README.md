# AltCodes4Linux

This script makes it possible to enter "alt codes" with a keyboard device on the Linux desktop as known from Windows.

On Windows, when you hold the left ALT key and enter the **decimal** number of a char (ASCII/cp850/cp1252) on the numpad, the corresponding char is inserted at the current position when releasing the ALT key. The behavior is different if you want to insert a special char on the Linux desktop: here, you need to press CTRL+SHIFT+u, followed by the **hexadecimal** Unicode code point and ENTER.

This script captures the events of an input device and when recognizing alt codes, it converts them into appropriate keystrokes for the Linux desktop.

This is necessary for compatibility with keyboard-like devices which cannot be configured otherwise, e.g. some barcode scanners or RFID card readers.

## Usage
### Listen on all keyboards (automatic, package installation)
1. Install the .deb package provided in the [releases](https://github.com/schorschii/AltCodes4Linux/releases).
2. Enter an alt code on your keyboard and have fun!

Note: if you plug in your device **after** the service started, you need to restart the service with `systemctl restart altcodes4linux`!

### Specific device only (manual installation)
1. Install packages: `apt install python3-evdev evtest`.
2. Find your input device with `evtest`.
3. Test the script, e.g. with: `./altcodes4linux.py /dev/input/event19`.  
   Since the event device number can change depending on the order the devices are recognized, you should rather use the device path by id, e.g. `/dev/input/by-id/usb-<YOUR-RFID-READER-NAME>`.  
4. Put the systemd service file into `/etc/systemd/system/altcodes4linux.service` (adjust your device path) and enable it via `systemctl enable altcodes4linux`. Start it via `systemctl start altcodes4linux`.
5. Enter an alt code on the selected device and have fun!

## Troubleshooting
Before opening a issue, please execute the script manually (by typing `altcodes4linux.py` in a terminal and pressing enter). Have a look at the output and include it in your issue.
