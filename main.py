# -*- coding: utf-8 -*-

import gc
import os
import time
import utime
import machine
import network
import nabla
import dht

def color_str(c): return tuple([int(n) for n in c.split(",")])

def alert(msg="(!)", color=(255,255,255), bg=(255,0,0)):
    msg=msg[0:5]
    bar.br()
    line = bar.line(bg)
    for y in range(bar.h):
        bar.scroll(line)
        bar.write()
    time.sleep(1)
    bar.msg(msg, color=color, bg=bg, x=3*(5-len(msg)))
    time.sleep(1)
    for y in range(bar.h):
        bar.scroll(line)
        bar.write()
    bar.br()

class Myself(nabla.Thing):

    cycle = 0
    adc = machine.ADC(0)
    value = {'light':0, 'temp':0, 'humi':0 }
    config= {"dt":None, "fg":"255,255,0", "bg":"0,0,0" }

    def init(self):
        self.load_config()
        c = self.config
        if c['dt']: self.set_clock(c['dt'])
        if c['fg']: bar.fgcolor = color_str(c['fg'])
        if c['bg']: bar.bgcolor = color_str(c['bg'])
        bar.time()

    def tt_connect(self):
        if self.broker is None: return False
        from umqtt.simple import MQTTClient
        self.tt = MQTTClient(self.name, self.broker ) #user=, password=
        self.tt.set_callback(self.onMessage)
        self.tt.connect()

    def value_set(self, k, v):
        c = self.value[k]
        if c!=v:
            self.value[k]=v
            self.tt.publish(b"info/%s/%s" % (self.name, k), b"%s" % v )
            
    def check_sensors(self):
        try:
            d = dht.DHT11(machine.Pin(12))
            d.measure()
        except:
            return
        self.value_set("temp", d.temperature())
        self.value_set("humi", d.humidity())
        del d
        gc.collect()

    def loop(self):
        self.cycle+=1;
        if self.cycle>=120:
            nabla.settime()
            self.set_clock(self.config['dt'])
            self.cycle=0
        if self.cycle>=0:
            t = machine.RTC().datetime()
            h = "0%s" % t[4]
            m = "0%s" % t[5]
            bar.msg("%s%s%s" % (h[-2:],":" if self.cycle%2==0 else " ",m[-2:]))
        if self.cycle%10==0:
            s = self.value["light"]
            v = self.adc.read()
            if (v-s)**2>100:
                self.value_set("light", v)
                bar.power=v/102.4 if v<124 else 1.0
            self.check_sensors()
            
     
        self.tt.check_msg()
        time.sleep_ms(500)

    def onMessage(self, topic, msg):
        me = b"thing/%s" % (self.name)
        super().onMessage(topic, msg)
        msg = msg.decode("utf-8").upper()
        if self.command(topic, msg): return
        if topic==b"%s/write" % (me):
            bar.message("     \n-> ", color=(255,255,255), wait=0)
            bar.message(msg)
            bar.message(" \n     ", color=(255,255,255))
            
        elif topic==b"%s/alert" % (me):
            alert(msg[0:5])
        gc.collect()
    
    def topic_value(self, color):
        for k,v in self.value.items():
            self.tt.publish(b"info/%s/%s" % (self.name, k), b"%s" % v )
        
    def topic_color(self, color):
        bar.color(*[int(z) for z in color.split(",")])
    
    def topic_foreground(self, color):
        bar.fgcolor = color_str(color)
        self.config['fg']=color
        self.save_config()

    def topic_background(self, color):
        c = [int(z) for z in color.split(",")]
        bar.bgcolor = tuple(c)
        bar.color(*c)
        self.config['bg']=color
        self.save_config()

    def topic_fx(self, n):
        bar.fx(*[int(z) for z in n.split(",")])
        bar.br()
        v = self.value
        bar.message("Temperatura %s%sC, humedad %s%%, luz %s%%" % (v["temp"],u'\xba',v["humi"],int(v["light"]/10.24)))


bar.wait=25

try:
    
    connect()
    me = Myself("gps.gglas.com", i2c=None)
    me.run()
except Exception as e:
    alert("ERROR")
    bar.message(" "+e.__class__.__name__+": "+str(e)+"     ", color=(255,128,0))
    alert("ERROR")
    if "ECONNABORTED" in str(e):
        bar.message("ABORT", color=(255,0,0))
        #machine.reset()
    if "ETIMEDOUT" in str(e):
        bar.message("TIMED", color=(255,0,0))
        #machine.reset()
