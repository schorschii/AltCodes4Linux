#!/usr/bin/env python3

import argparse
import evdev
import time


hexKeyMap = {
    '0': evdev.ecodes.KEY_0,
    '1': evdev.ecodes.KEY_1,
    '2': evdev.ecodes.KEY_2,
    '3': evdev.ecodes.KEY_3,
    '4': evdev.ecodes.KEY_4,
    '5': evdev.ecodes.KEY_5,
    '6': evdev.ecodes.KEY_6,
    '7': evdev.ecodes.KEY_7,
    '8': evdev.ecodes.KEY_8,
    '9': evdev.ecodes.KEY_9,
    'A': evdev.ecodes.KEY_A,
    'B': evdev.ecodes.KEY_B,
    'C': evdev.ecodes.KEY_C,
    'D': evdev.ecodes.KEY_D,
    'E': evdev.ecodes.KEY_E,
    'F': evdev.ecodes.KEY_F,
}
numpadKeyMap = {
    evdev.ecodes.KEY_KP0: '0',
    evdev.ecodes.KEY_KP1: '1',
    evdev.ecodes.KEY_KP2: '2',
    evdev.ecodes.KEY_KP3: '3',
    evdev.ecodes.KEY_KP4: '4',
    evdev.ecodes.KEY_KP5: '5',
    evdev.ecodes.KEY_KP6: '6',
    evdev.ecodes.KEY_KP7: '7',
    evdev.ecodes.KEY_KP8: '8',
    evdev.ecodes.KEY_KP9: '9',
}

def main():
    parser = argparse.ArgumentParser(
        description='Translate alt codes from input devices into hex code keystrokes which Linux desktops understand',
        epilog='(c) Georg Sieber 2024 - https://github.com/schorschii/AltCodes4Linux'
    )
    parser.add_argument('device', help='The input device file, e.g. /dev/input/event1 or /dev/input/by-id/usb-WHATEVER')
    args = parser.parse_args()

    # open input device
    dev = evdev.InputDevice(args.device)
    dev.grab() # become the sole recipient of all incoming input events
    print('Listening for alt codes on', dev)

    # create virtual input device
    vinput = evdev.UInput()

    # listen for altcode key events
    currentAltCode = None
    for event in dev.read_loop():
        if event.type != evdev.ecodes.EV_KEY: continue
        keyEvent = evdev.events.KeyEvent(event)
        #print(keyEvent.keycode, keyEvent.keystate)

        # ALT key pressed - reset our buffer for next altcode
        if keyEvent.scancode == evdev.ecodes.KEY_LEFTALT and keyEvent.keystate == 1:
            currentAltCode = ''

        # ALT key released - convert and emulate input
        elif keyEvent.scancode == evdev.ecodes.KEY_LEFTALT and keyEvent.keystate == 0:
            # currentAltCode might be empty
            if not currentAltCode:
                # forward ALT key press
                vinput.write(evdev.ecodes.EV_KEY, keyEvent.scancode, 1)
                vinput.syn()
                vinput.write(evdev.ecodes.EV_KEY, keyEvent.scancode, 0)
                vinput.syn()

                currentAltCode = None
                continue

            # convert alt code to equivalent Unicode code point
            codepage = 'cp1252' if currentAltCode[0]=='0' else 'cp850'
            altCodeDec = int(currentAltCode)
            altCodeChar = ord(altCodeDec.to_bytes(1, 'big').decode(codepage))
            altCodeHex = ('%0.2X' % altCodeChar).upper()
            print('ALTCODE: ', currentAltCode, '('+str(altCodeDec)+')', ' ='+chr(altCodeChar)+'= ', ' --> ', '0x'+altCodeHex)
            currentAltCode = None

            # send Linux equivalent keystrokes CTRL+SHIFT+u+<hex>+ENTER
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 1)
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTSHIFT, 1)
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_U, 1)
            vinput.syn()
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 0)
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTSHIFT, 0)
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_U, 0)
            vinput.syn()
            for char in altCodeHex:
                if char in hexKeyMap.keys():
                    vinput.write(evdev.ecodes.EV_KEY, hexKeyMap[char], 1)
                    vinput.syn()
                    vinput.write(evdev.ecodes.EV_KEY, hexKeyMap[char], 0)
                    vinput.syn()
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 1)
            vinput.syn()
            vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 0)
            vinput.syn()

        # write pressed numpad key into our currentAltCode buffer
        elif keyEvent.scancode in numpadKeyMap and keyEvent.keystate == 1 and currentAltCode != None:
            currentAltCode += numpadKeyMap[keyEvent.scancode]
        elif keyEvent.scancode in numpadKeyMap and keyEvent.keystate == 0 and currentAltCode != None:
            pass # discard numpad key up event when ALT is pressed

        # forward other key strokes
        else:
            vinput.write(evdev.ecodes.EV_KEY, keyEvent.scancode, keyEvent.keystate)
            vinput.syn()

    vinput.close()

if __name__ == '__main__':
    while True:
        try:
            main()
        except (FileNotFoundError, OSError) as e:
            # if device disconnected or not yet connected, try again in 1 sec
            print(type(e), e)
            time.sleep(1)
