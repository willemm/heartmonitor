#!/usr/bin/env python

import time, sys, os, random, smbus, socket
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import pyaudio, wave
from neopixel import *
import MAX30102
import NFCReader
import Paddles

leds = Adafruit_NeoPixel(2, 13, channel=1)
mx = MAX30102.MAX30102()

beepwav = wave.open("audio/beep.wav","rb")

pa = pyaudio.PyAudio()
stream = pa.open(format = pa.get_format_from_width(beepwav.getsampwidth()),
                 channels = beepwav.getnchannels(),
                 rate = beepwav.getframerate(),
                 output = True)

beep = beepwav.readframes(4096)

i2c = smbus.SMBus(1)
mcp = 0x20
mcp_iodir = 0x00
mcp_gppu = 0x0c
mcp_gpio = 0x12

i2c.write_word_data(mcp, mcp_iodir, 0xFFFF)
i2c.write_word_data(mcp, mcp_gppu, 0xFFFF)
i2c.write_word_data(mcp, mcp_gpio, 0x0000)

leds.begin()

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.disable_hardware_pulsing = True
options.pixel_mapper_config = "Rotate:180"

#nfcRdr = NFCReader.NFCReader()
#nfcRdr.run()

paddles = Paddles.Paddles()

matrix = RGBMatrix(options = options)
acmefont = graphics.Font()
acmefont.LoadFont('/home/pi/src/rpi-rgb-led-matrix/fonts/6x13.bdf')
ipfont = graphics.Font()
ipfont.LoadFont('/home/pi/src/rpi-rgb-led-matrix/fonts/5x8.bdf')

def show_ipaddress(matrix, font):
    ipaddress = ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0])
    ypos = 64 - 5*len(ipaddress)
    graphics.DrawText(matrix, font, ypos, 30, graphics.Color(255, 0, 255), ipaddress)

pixs = [255,255,255,255,255,0]
leds.setPixelColor(0, Color(pixs[2], pixs[1], pixs[0]))
leds.setPixelColor(1, Color(pixs[5], pixs[4], pixs[3]))
leds.show()
try:
    matrix.Fill(0, 0, 0)
    print "Starting process"
    graphics.DrawText(matrix, acmefont, 2, 20, graphics.Color(255, 255, 0), 'ACME')
    graphics.DrawText(matrix, acmefont, 32, 20, graphics.Color(0, 255, 255), 'Cura')
    heartbeatdelay = 0
    heartmode = 0
    cur = 0.4
    tgt = 0.4
    spd = 0.1
    zapcnt = 0
    zaptry = 0
    beat = False
    plotpos = 0
    while True:
        """
        uid = nfcRdr.poll()
        if uid:
            print "Got NFC card "+uid
            if uid == 'e4c3b6c3' and heartbeatdelay != 120:
                print "Stop beat"
                heartbeatdelay = 120
                spd = 0.1
                tgt = 0.4
            if uid == '9349a524' and heartbeatdelay == 120:
                print "Start beat"
                heartbeatdelay = -100
                spd = 0.1
                tgt = 0.4
        """
        if heartmode != 0:
            for y in range(0, matrix.height):
                #matrix.SetPixel(plotpos, y, 0, 0, 0)
                #matrix.SetPixel(plotpos+1, y, 0, 0, 0)
                #matrix.SetPixel(plotpos+2, y, 0, 0, 0)
                matrix.SetPixel((plotpos+3)%matrix.width, y, 0, 0, 0)
                matrix.SetPixel((plotpos+4)%matrix.width, y, 0, 0, 0)
        if heartmode == 2:
            mx.update()
            tgt = 0.5 - (mx.ir / 1200.0)
            spd = 1.0
            if tgt > 1.0:
                tgt = 1.0
            if tgt < 0.0:
                tgt = 0.0
            if tgt > 0.8 and not beat:
                beat = True
                stream.write(beep)
            if tgt < 0.4 and beat:
                beat = False
        elif heartmode == 1:
            if heartbeatdelay == 10:
                tgt = random.randint(15,25)/100.0
                spd = 0.1
            elif heartbeatdelay == 15:
                tgt = random.randint(90,90)/100.0
                spd = 0.3
                stream.write(beep)
            elif heartbeatdelay == 18:
                tgt = random.randint(5,15)/100.0
                spd = 0.2
            elif heartbeatdelay == 22:
                tgt = random.randint(50,60)/100.0
                spd = 0.1
            elif heartbeatdelay >= 27 and heartbeatdelay < 35:
                tgt = random.randint(35,45)/100.0
                spd = 0.1
            elif heartbeatdelay ==35:
                tgt = 0.4
                spd = 0.1
            elif heartbeatdelay == 40:
                heartbeatdelay = random.randint(-5,5)
            ypos1 = int(matrix.height/2 * (1.0-cur))
            if cur < tgt:
                cur = cur + spd
                if cur > tgt:
                    cur = tgt
                    spd = 0.0
                ypos2 = int(matrix.height/2 * (1.0-cur))
                for y in range(ypos2, ypos1):
                    matrix.SetPixel(plotpos, y, 0, 255, 0)
            elif cur > tgt:
                cur = cur - spd
                if cur < tgt:
                    cur = tgt
                    spd = 0.0
                ypos2 = int(matrix.height/2 * (1.0-cur))
                for y in range(ypos1, ypos2):
                    matrix.SetPixel(plotpos, y, 0, 255, 0)
            matrix.SetPixel(plotpos, ypos1, 0, 200, 0)
            if heartbeatdelay > -100 and heartbeatdelay <= 100:
                heartbeatdelay += 1

        try:
            buttons = i2c.read_word_data(mcp, mcp_gpio)
            """
            for x in range(0,16):
                if ((buttons >> x) & 1) == 0:
                    if x >= 0 and x <= 4:
                        pixs[x] = 0
                    matrix.SetPixel(x*4+2, 30, 0, 0, 255)
                    matrix.SetPixel(x*4+3, 30, 0, 64, 64)
                    matrix.SetPixel(x*4+1, 30, 0, 64, 64)
                    matrix.SetPixel(x*4+2, 31, 0, 64, 64)
                    matrix.SetPixel(x*4+2, 29, 0, 64, 64)
                else:
                    if x >= 0 and x <= 4:
                        pixs[x] += 2
                        if pixs[x] >= 255:
                            pixs[x] = 255
                    matrix.SetPixel(x*4+2, 30, 0, 0, 0)
                    matrix.SetPixel(x*4+3, 30, 0, 0, 0)
                    matrix.SetPixel(x*4+1, 30, 0, 0, 0)
                    matrix.SetPixel(x*4+2, 31, 0, 0, 0)
                    matrix.SetPixel(x*4+2, 29, 0, 0, 0)
            """
            if   (not buttons & 0b0000000000001000) and heartmode == 0:
                print "Starting heart monitor"
                heartmode = 1
            elif (not buttons & 0b0000000000010000) and heartmode == 1:
                print "Stopping heart monitor"
                heartmode = 0
            if   (not buttons & 0b0000000010000000) and heartbeatdelay != 120:
                print "Stop beat"
                heartbeatdelay = 120
                spd = 0.1
                tgt = 0.4
                zaptry = 0
            elif (not buttons & 0b0000000000100000) and heartbeatdelay == 120:
                print "Start beat"
                heartbeatdelay = -10
                spd = 0.1
                tgt = 0.4
            if   (not buttons & 0b0000000000000010):
                show_ipaddress(matrix, ipfont)
        except:
            pass
        paddles.read()
        buttons = paddles.buttons.values()
        if len(buttons) == 2 and buttons[0] and buttons[1]:
            if zapcnt == 0:
                paddles.command("color 100,0,0")
                paddles.command("sound")
            zapcnt += 1
            if zapcnt > 100:
                paddles.command("color 0,100,0")
        elif zapcnt > 100:
            paddles.command("color 0,0,100")
            paddles.command("flash")
            paddles.command("color 0,0,0")
            if heartmode != 0 and heartbeatdelay == 120:
                zaptry += 1
                if zapcnt < (80 + (zaptry * 30)):
                    print "It worked! Start beat!"
                    heartbeatdelay = -99
                    spd = 0.1
                    tgt = 0.4
            zapcnt = 0
        elif zapcnt > 0:
            zapcnt = 0
            paddles.command("color 0,0,0")
            paddles.command("soundoff")
        time.sleep(0.02)
        if heartmode != 0:
            plotpos = (plotpos + 1) % matrix.width
        else:
            plotpos = 0
except KeyboardInterrupt:
    print "Stopping"
    pass
finally:
    leds.setPixelColor(0, Color(0, 0, 0))
    leds.setPixelColor(1, Color(0, 0, 0))
    leds.show()
    paddles.command("color 0,0,0")
    paddles.command("soundoff")
    #mx.close()
    sys.exit(0)
