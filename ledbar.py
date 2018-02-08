# -*- coding: utf-8 -*-
# Led Strip ZigZag bar driver for MicroPython on ESP8266
# MIT license; Copyright (c) 2017 Txema Vicente

from esp import neopixel_write
import time
import machine
import urandom
import math

DIGIT = {
    '0': bytes((14,17,17,17,14)), ' ': bytes(( 0, 0, 0, 0, 0)),
    '1': bytes(( 4,12, 4, 4,14)), '#': bytes((10,31,10,31,10)),
    '2': bytes((14, 1,14,16,14)), '_': bytes(( 0, 0, 0, 0,31)), 
    '3': bytes((30, 1,14, 1,30)), '-': bytes(( 0, 0,14, 0, 0)), 
    '4': bytes((18,18,31, 2, 2)), '*': bytes(( 0,10, 4,10, 0)), 
    '5': bytes((31,16,14, 1,30)), '/': bytes(( 1, 2, 4, 8,16)), 
    '6': bytes((14,16,30,17,14)), '=': bytes(( 0,14, 0,14, 0)), 
    '7': bytes((31, 1, 2, 4, 4)), '+': bytes(( 0, 4,14, 4, 0)),
    '8': bytes((14,17,14,17,14)), '.': bytes(( 0, 0, 0, 0, 4)),
    '9': bytes((14,17,15, 1,14)), ',': bytes(( 0, 0, 0, 4, 8)),
    'A': bytes((14,17,31,17,17)), ':': bytes(( 0, 4, 0, 4, 0)),  
    'B': bytes((30,17,30,17,30)), ';': bytes(( 0, 4, 0, 4, 8)),
    'C': bytes((14,16,16,16,14)), "'": bytes(( 4, 0, 0, 0, 0)),
    'D': bytes((28,18,17,18,28)), '"': bytes((10, 0, 0, 0, 0)),
    'E': bytes((31,16,30,16,31)), '(': bytes(( 2, 4, 4, 4, 2)),
    'F': bytes((31,16,30,16,16)), ')': bytes(( 4, 2, 2, 2, 4)),
    'G': bytes((14,16,19,17,14)), '[': bytes(( 6, 4, 4, 4, 6)),
    'H': bytes((17,17,31,17,17)), ']': bytes(( 6, 2, 2, 2, 6)),
    'I': bytes((14, 4, 4, 4,14)), '{': bytes(( 2, 4, 4, 4, 2)),
    'K': bytes((17,18,28,18,17)), '}': bytes(( 4, 2, 3, 2, 4)),
    'J': bytes(( 1, 1, 1,17,14)), '<': bytes(( 0, 4, 8, 4, 0)),
    'L': bytes((16,16,16,16,31)), '>': bytes(( 0, 8, 4, 8, 0)),
    'M': bytes((17,27,21,17,17)), '!': bytes(( 4, 4, 4, 0, 4)), 
    'N': bytes((17,25,21,19,17)), '?': bytes((14, 1, 6, 0, 4)),
    'O': bytes((14,17,17,17,14)), 'º': bytes((14,10,14, 0, 0)),
    'P': bytes((30,17,30,16,16)), '%': bytes((17,18, 4, 9,17)),
    'Q': bytes((14,17,17,21,14)), '$': bytes((14,20,14, 5,14)),
    'R': bytes((30,17,30,18,17)), '€': bytes((14,16,28,16,14)),
    'S': bytes((14,16,14, 1,14)), '|': bytes(( 4, 4, 4, 4, 4)),
    'T': bytes((31, 4, 4, 4, 4)), '@': bytes((14, 1,29,17,14)),
    'U': bytes((17,17,17,17,14)), 
    'V': bytes((17,17,10,10, 4)),
    'W': bytes((17,17,21,21,10)),
    'X': bytes((17,10, 4,10,17)),
    'Y': bytes((17,17,10, 4, 4)), 'Ñ': bytes((31,0,25,21,19)),
    'Z': bytes((31, 2, 4, 8,31)),'\n': bytes((31,31,31,31,31))
}

def clean_txt(txt):
    if type(txt)!=type(u''):
        txt = txt.decode('utf-8')
    return txt.upper()


class LedBar(object):

    def __init__(self, w=30, h=5, pin=None):
        
        if pin is None: pin = machine.Pin(14)
        self.pin = pin
        self.pin.init(pin.OUT)
        self.n = n = w * h
        self.h = h
        self.w = w
        self.width = w // 6
        self.__fgcolor = (255, 255, 255)
        self.__bgcolor = (0, 0, 0)
        self.power = 1.0
        self.wait = 10
        self.buf = bytearray(n*3)
        self.lines = []
        for y in range(h):
            if y%2==0:
                o = 3*y*w
                e = 3*((y+1)*w-1)
            else:
                o = 3*((y+1)*w-1)
                e = 3*(y*w)
            self.lines.append((y,o,e))


    def write(self):
        neopixel_write(self.pin, self.buf, True)
        

    def speed(self):
        for i in range(self.n):
            self.buf = bytearray(3*self.n)
            o=(i%self.n)*3
            self.buf[o:o+3] = bytearray([255, 255, 255])
            self.write()


    def color(self, r, g, b):
        color = bytearray([g,r,b])
        for n in range(0,3*self.n,3): self.buf[n:n+3] = color
        self.write()


    @property
    def fgcolor(self):
        c = self.__fgcolor
        return (int(c[0]*self.power), int(c[1]*self.power), int(c[2]*self.power))


    @fgcolor.setter
    def fgcolor(self, val): self.__fgcolor = val


    @property
    def bgcolor(self):
        c = self.__bgcolor
        return (int(c[0]*self.power), int(c[1]*self.power), int(c[2]*self.power))


    @bgcolor.setter
    def bgcolor(self, val): self.__bgcolor = val
    

    def random(self, times=1):
        for t in range(0,times):
            self.buf = bytearray([ urandom.getrandbits(8) for x in range(self.n*3)])
            self.write()


    def led(self, x, y, color):
        if x<0 or x>=self.w: return
        if y<0 or y>=self.h: return
        if y%2==0: n = 3*(y*self.w+x)
        else: n=3*((1+y)*self.w-x-1)
        self.buf[n:n+3]=bytearray([color[1], color[0], color[2]])


    def char(self, char, x=0, y=0, color=None):
        if color is None: color = self.fgcolor
        char = char.upper()
        if not char in DIGIT.keys(): char = "?"
        for oy in range(self.h):
            for ox in range(5):
                if 2**(4-ox) & DIGIT[char][oy]:
                    self.led(x+ox, y+oy, color)

                
    def msg(self, txt, color=None, x = 0, bg=None):
        if color is None: color = self.fgcolor
        if bg is None: bg = self.bgcolor
        
        if len(txt)>self.width:
            return self.message(txt, color=color, x=x, bg=bg)
        if bg is not None:
            gbr=bytearray([bg[1],bg[0],bg[2]])
            for n in range(0,self.n*3,3): self.buf[n:n+3] = gbr
        for char in txt:
            self.char(char, x, color=color)
            x+=6
        self.write()
        

    def message(self, txt, color=None, bg=None, wait=None, x=0):
        if wait is None: wait = self.wait
        for char in clean_txt(txt):
            self.push_char(char, color=color, bg=bg, wait=wait)

    def time(self, color=None):
        t = machine.RTC().datetime()
        hh = "0%s" % t[4]
        mm = "0%s" % t[5]
        self.msg(hh[-2:]+":"+mm[-2:] , color=color)


    def push_char(self, char, color=None, bg=None, wait=None):
        if not char in DIGIT.keys(): char = "*"
        line = DIGIT[char]
        if color is None: color = self.fgcolor
        if bg is None: bg = self.bgcolor
        if wait is None: wait = self.wait
        color = bytearray([color[1],color[0],color[2]])
        bg = bytearray([bg[1],bg[0],bg[2]])
        for x in range(6):
            for y,o,e in self.lines:
                self.buf[o:o+3]=bytearray([])
                self.buf[e:e]=color if x<5 and (2**(4-x) & line[y]) else bg
            self.write()
            time.sleep_ms(wait)


    def mirror(self, line):
        odd=bytearray()
        for x in range(len(line), 0, -3):
            odd+=bytearray(line[x-3:x])
        return odd


    def zigzag(self):
        m = memoryview(self.buf)
        for y,L,R in self.lines:
            if L>R:
                a=R
                b=L+3
            else:
                a=L
                b=R+3
            m[a:b] = self.mirror(m[a:b])

        
    def scroll(self, line):
        self.buf[0:self.w*3] = bytes([])
        self.zigzag()
        self.buf+=line


    def line(self, color):
        line = bytearray([])
        c = bytearray([color[1], color[0], color[2]])
        for x in range(self.w): line.extend(c)
        return line


    def br(self, color=(0,0,0), bg=(0,0,0)):
        line = self.line(bg)
        for y in range(self.h):
            self.scroll(line)
            self.write()
        self.scroll(self.line(color))
        self.write()
        for y in range(self.h):
            self.scroll(line)
            self.write()
        

    def cycle_left(self):
        for y,L,R in self.lines:
            t = self.buf[L:L+3]
            self.buf[L:L+3] = bytearray([])
            self.buf[R:R] = t
        self.write()


    def hue(self,offset=20):
        hue = bytearray()
        w = self.w
        for x in range(w):
            ox = offset+x
            if ox>=w: ox-=w
            h=(ox/float(w))*6
            t = (h%2)
            if h<1: r=1;g=1*t;b=0
            elif h<2: r=2-t;g=1;b=0
            elif h<3: r=0;g=1;b=t; 
            elif h<4: r=0;g=2-t;b=1
            elif h<5: r=t;g=0;b=1
            else: r=1;g=0;b=2-t
            m = 255.0/math.sqrt(r*r+g*g+b*b)
            hue.append(int(m*g))
            hue.append(int(m*r))
            hue.append(int(m*b))
        return hue


    def spectrum(self, offset=0):
        even=self.hue(offset)
        odd=self.mirror(even)
        for y in range(self.h):    
            ox = 3*y*self.w
            self.buf[ox:ox+self.w*3] = even if y%2==0 else odd
        self.write()
        del even
        del odd

  
    def fx(self, offset=0, delay=0):
        hue = self.hue(offset)
        for i in range(0,len(hue),3):
            c = hue[i:i+3]
            time.sleep_ms(delay)
            line = bytearray([])
            for i in range(self.w): line+=c
            self.scroll(line)
            self.write()

