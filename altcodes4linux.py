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
    'a': evdev.ecodes.KEY_A,
    'b': evdev.ecodes.KEY_B,
    'c': evdev.ecodes.KEY_C,
    'd': evdev.ecodes.KEY_D,
    'e': evdev.ecodes.KEY_E,
    'f': evdev.ecodes.KEY_F,
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
        epilog='(c) Georg Sieber 2024'
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
            if not currentAltCode: # might be an empty string
                currentAltCode = None
                continue
            altCodeDec = int(currentAltCode)
            altCodeChar = chr(altCodeDec)
            altCodeHex = hex(altCodeDec)[2:]
            currentAltCode = None
            print('ALTCODE:', currentAltCode, altCodeDec, altCodeChar, altCodeHex)

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