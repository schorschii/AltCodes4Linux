#!/usr/bin/env python3

import threading
import argparse
import signal
import evdev
import time
import sys


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
altTimer = None
altCodeTimer = None
pressAlt = True
pressedAlt = False
pressEnter = False
altCodeBuffer = []

def sendAlt(vinput):
    global pressAlt, pressedAlt
    if(pressAlt):
        print('DELAYED ALT')
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTALT, 1)
        vinput.syn()
        pressAlt = False
        pressedAlt = True

def sendAltCode(vinput):
    global altCodeBuffer, pressEnter
    # send Linux equivalent keystrokes CTRL+SHIFT+u+<hex>+ENTER
    for altCodeHex in altCodeBuffer:
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 1)
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTSHIFT, 1)
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_U, 1)
        vinput.syn()
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTCTRL, 0)
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_LEFTSHIFT, 0)
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_U, 0)
        vinput.syn(); time.sleep(0.01)
        for char in altCodeHex:
            if char in hexKeyMap.keys():
                vinput.write(evdev.ecodes.EV_KEY, hexKeyMap[char], 1)
                vinput.syn()
                vinput.write(evdev.ecodes.EV_KEY, hexKeyMap[char], 0)
                vinput.syn(); time.sleep(0.01)
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 1)
        vinput.syn()
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 0)
        vinput.syn(); time.sleep(0.01)
    # exec delayed enter keystroke
    if(pressEnter):
        print('DELAYED ENTER')
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 1)
        vinput.syn()
        vinput.write(evdev.ecodes.EV_KEY, evdev.ecodes.KEY_ENTER, 0)
        vinput.syn()
        pressEnter = False
    # reset buffer
    altCodeBuffer.clear()

def main(device):
    global altTimer, altCodeTimer, pressAlt, pressedAlt, pressEnter

    # open input device
    dev = evdev.InputDevice(device)
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

            # delay ALT key down event - send only if no numpad key is pressed within 0.5s
            # this is for handling fast input of multiple alt codes, e.g. barcode scanners or RFID readers,
            # to not open menus in Firefox and VScode
            if(altTimer): altTimer.cancel()
            altTimer = threading.Timer(0.5, sendAlt, (vinput,))
            altTimer.start()
            pressAlt = True
            pressedAlt = False

        # ALT key released - convert and emulate unicode input
        elif keyEvent.scancode == evdev.ecodes.KEY_LEFTALT and keyEvent.keystate == 0:
            pressEnter = False

            # when ALT key is released before altTimer fired, send ALT key down event immediately
            if(altTimer):
                altTimer.cancel()
                sendAlt(vinput)

            # ALT key is still pressed - forward key up event
            vinput.write(evdev.ecodes.EV_KEY, keyEvent.scancode, keyEvent.keystate)
            vinput.syn()

            # do nothing if no number was entered on numpad
            if not currentAltCode:
                currentAltCode = None
                continue

            # do nothing if delayed ALT key down event was already sent via altTimer
            if pressedAlt:
                continue

            # convert alt code to equivalent Unicode code point
            codepage = 'cp1252' if currentAltCode[0]=='0' else 'cp850'
            try:
                altCodeDec = int(currentAltCode)
                altCodeChar = ord(altCodeDec.to_bytes(1, 'big').decode(codepage))
                altCodeHex = ('%0.2X' % altCodeChar).upper()
                altCodeBuffer.append(altCodeHex)
                print('ALTCODE: ', currentAltCode, '('+str(altCodeDec)+')', ' --> ', '0x'+altCodeHex, ' [ '+chr(altCodeChar)+' ]')
                currentAltCode = None

            except Exception as e:
                print('ALTCODE: ', currentAltCode, ' not recognized --> ignored (',e,')')
                currentAltCode = None
                continue

            # delay sending captured alt codes - too fast unicode input may be garbled
            if(altCodeTimer): altCodeTimer.cancel()
            altCodeTimer = threading.Timer(0.2, sendAltCode, (vinput,))
            altCodeTimer.start()

        # delay enter press while writing unicode
        elif keyEvent.scancode == evdev.ecodes.KEY_ENTER and altCodeBuffer:
            pressEnter = True

        # write pressed numpad key into our currentAltCode buffer
        elif keyEvent.scancode in numpadKeyMap and currentAltCode != None:
            if keyEvent.keystate == 1:
                currentAltCode += numpadKeyMap[keyEvent.scancode]
                pressAlt = False
            elif keyEvent.keystate == 0:
                pass # discard numpad key event when typing an alt code

        # forward other key strokes
        else:
            # if any other key than a numpad number is pressed within the altTimer,
            # we assume that it's not intended to enter an alt code but a shortcut with ALT
            # e.g. ALT+tab or ALT+F4
            if(pressAlt and keyEvent.scancode != evdev.ecodes.KEY_LEFTALT):
                if(altTimer): altTimer.cancel()
                sendAlt(vinput)

            vinput.write(evdev.ecodes.EV_KEY, keyEvent.scancode, keyEvent.keystate)
            vinput.syn()

    vinput.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Translate alt codes from input devices into hex code keystrokes which Linux desktops understand',
        epilog='(c) Georg Sieber 2024-2026 - https://github.com/schorschii/AltCodes4Linux'
    )
    parser.add_argument('device', nargs='?', help='The input device file, e.g. /dev/input/event1 or /dev/input/by-id/usb-WHATEVER. Omit it to listen on all keyboard devices (experimental).')
    parser.add_argument('-d', '--daemon', action='store_true', help='Daemon mode, keep running if device is not yet connected or disconnected.')
    args = parser.parse_args()

    if(args.device):
        # try to grab given device
        while True:
            try:
                time.sleep(0.2)
                main(args.device)
            except (FileNotFoundError, OSError) as e:
                print(type(e), e)
                if(args.daemon):
                    # if device disconnected or not yet connected, try again in 1 sec
                    time.sleep(1)
                else:
                    sys.exit(1)
    else:
        # grab all devices
        time.sleep(0.2)
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            caps = device.capabilities()
            if(evdev.ecodes.KEY_ENTER in caps.get(evdev.ecodes.EV_KEY, [])
            and evdev.ecodes.BTN_LEFT not in caps.get(evdev.ecodes.EV_KEY, [])):
                thread = threading.Thread(target=main, args=[device.path], daemon=True)
                thread.start()
            else:
                print('Skip (not a keyboard):', device)
        signal.pause()
