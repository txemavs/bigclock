# bigclock
Micropython MQTT Neopixel Clock

This was used to make a big five letter led matrix color clock, to display any messages sent from a web page.

Materials:
* One ESP8266 microcontroller with micropython and umqtt installed
* A LDR light sensor
* A DHT11 temp sensor
* 150 neopixel LEDs
* a 5V 10A power source

Letters are 5x5 dots, 6 dots width with the spacing, so we need a 30x5 dot matrix 
A 5m 150 LED strip makes a 110x17 cm display.
