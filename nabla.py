# -*- coding: utf-8 -*-
# Nabla Thing ESP8266
# MIT license; Copyright (c) 2017 Txema Vicente

import os
import gc
import esp
import network
import ubinascii
import uasyncio as asyncio
from machine import I2C, Pin, freq, RTC, unique_id
from time import sleep, sleep_ms, ticks_ms
from ntptime import settime
import utime

def connect(ssid, passwd):
    lan = network.WLAN(network.STA_IF)
    if not lan.isconnected():
        print('Connecting to %s ...' % ssid)
        lan.active(True)
        lan.connect(ssid, passwd )
        while not lan.isconnected():
            pass
    print('network config:', lan.ifconfig())


def pad(s, l, x="0"):
    if x=="": return s
    s = s.decode('utf-8') if type(s)==type(b'') else str(s)        
    while len(s)<l:s=x+s
    return s[0:l]


        

I2C_ADDR_MCP23017=32#x20
I2C_ADDR_SSD1306 =60#x3C
I2C_ADDR_LCD1602 =63#x3F


class Thing(object):
    '''Intelligent Machine, Host
    '''
    broker = "mqtt.nabla.net"
    io=None   # MCP ports
    i2c=None  
    spi=None
    lan=None
    scr=None
    lcd=None
    clockset = False
    config={'dt':0, 'user':None, 'pass':None}
    

    def init(self): pass


    def __init__(self, broker=None, name=None, i2c=True, spi=None):
        if broker is not None: self.broker = broker
        self.uid = ubinascii.hexlify(unique_id())
        self.name = self.uid if name is None else name 
        self.size = esp.flash_size() #esp.flash_id()
        self.ip = self.get_ip()
        settime()
        if i2c is not None: self.__i2c(i2c)
        self.init()
        gc.collect()


    def get_ip(self):
        sta_if = network.WLAN(network.STA_IF)
        if sta_if.isconnected():
            ifconfig = sta_if.ifconfig()
            return ifconfig[0]
        else:
            return None


    def load_config(self, filename="config.ini"):
        if not filename in os.listdir(): return
        for line in open(filename):
            part = line.strip().split("=")
            if len(part)>1: self.config[part[0]]=part[1]


    def save_config(self, filename="config.ini"):
        with open(filename, "w") as f:
            for key in self.config.keys():
                f.write("%s=%s\n" % (key, self.config[key]))

    
    def set_clock(self, dt):
        oc=utime.time()+int(dt)
        (ye, mo, md, ho, mi, se, wd, yd)=utime.localtime(oc)
        RTC().datetime((ye, mo, md, 0, ho, mi, se, 0))
        self.clockset = True


    def now(self):
        n = RTC().datetime()
        return "%s%s%s %s:%s Z" % (n[0],pad(n[1],2),pad(n[2],2),pad(n[4],2),pad(n[5],2))


    def command(self, topic, msg):        
        me = b"thing/"+self.name+"/"
        if not (me in topic): return False
        cmd = b"topic_"+topic[len(me):]
        cmd = cmd.decode("utf-8") 
        if hasattr(self, cmd):
            getattr(self, cmd)(msg)
            return True
        return False


    def onMessage(self, topic, msg):
        if topic==b"thing/%s/service" % (self.name):
            if msg==b"!STOP":
                self.stop()
                self.print(self.ip, "|OUT OF SERVICE|") 
                return
            if msg==b"!NOW":
                self.print(self.ip, self.now()) 
                return
        
        elif topic==b"thing/%s/clock/dt" % (self.name):
            if not self.clockset:
                self.config['dt']=msg
                self.save_config()
                self.set_clock(msg)

        self.print(topic[-16:], msg)
        gc.collect()

        
    def tt_connect(self):
        if self.broker is None: return False
        self.status(self.broker,"warning")
        from umqtt.simple import MQTTClient
        self.tt = MQTTClient(self.name, self.broker, user=self.config['user'], password=self.config['pass'])
        self.tt.set_callback(self.onMessage)
        self.tt.connect()
        self.status("Connected","run")
        self.print(self.broker)

    
    def connect(self):
        self.tt_connect()
        self.tt.subscribe(b"thing/info")
        self.tt.subscribe(b"thing/%s/#" % self.name)
      

    def disconnect(self):
        self.tt.disconnect()
        self.status("Disconnected","warning")


    def value_set(self, k, v):
        c = self.value[k]
        if c!=v:
            self.value[k]=v
            self.tt.publish(b"info/%s/%s" % (self.name, k), b"%s" % v )
  

    def tick(self): pass


    def loop(self):
        self.status(self.now(),"run")
        self.tt.check_msg()
        self.tick()
        sleep_ms(500)


    def run(self):
        self.connect()
        self.running = True
        while self.running:
            self.loop()
        self.disconnect()
        gc.collect()

    def stop(self):
        self.running = False



    def print(self, *args):
        r=[]
        for line in args:
            if type(line)==type(b''):
                r.append(line.decode('utf-8'))
            else:
                r.append(line)
        print('\n'.join(r))

        if self.scr is not None:
            self.scr.write('\n'.join(r))

            
        if self.lcd is not None:
            self.lcd.move_to(0,0)
            t = ''
            for x in r:
                l=x+" "*16
                t+=l[0:16]
            self.lcd.clear()
            self.lcd.putstr(t)
            print(t)
    


    def __i2c(self, i2c):
        now = self.now()
        if i2c is True:
            self.i2c = I2C( scl=Pin(5), sda=Pin(4), freq=400000)
        else:
            self.i2c = i2c

        i2c_devices = self.i2c.scan()
            
        if I2C_ADDR_SSD1306 in i2c_devices:
            from ssd1306 import SSD1306_I2C
            print("OLED 128x64")
            oled = SSD1306_I2C(128, 64, self.i2c)
            self.scr = Screen(oled)
            self.scr.header("Disconnected")
            self.scr.write("Nabla Net Things")
            self.scr.write("%s" % self.name)
            self.scr.write(now)


        if I2C_ADDR_LCD1602 in i2c_devices:
            from lcd1602 import I2cLcd
            print("LCD 1604 detected")
            self.lcd = I2cLcd(self.i2c, I2C_ADDR_LCD1602, 2, 16)

        self.print(self.name,  "disconnected!" if self.ip is None else self.ip)
             
        if I2C_ADDR_MCP23017 in i2c_devices:
            from mcp import MCP23017, OUT, HIGH, LOW
            print("16 port IO Expander")
            self.io = MCP23017()
            #for x in range(0,8):
            #    self.io.setup(x, OUT)
            #    self.io.output(x, HIGH)



    def status(self, *args):
        if self.scr is None: return
        self.scr.header(*args)
        self.scr.show_header()

