
import time
from umqttsimple import  MQTTClient
import ubinascii
import machine
import micropython
import network
import esp
esp.osdebug(None)
import gc

gc.collect()

# Channel to listen for signals
topic_sub = 'SERVO'

# Connection to router
ssid = 'ssid'
password = 'password'
mqtt_server = '192.168.1.3' # IP of broker or Raspberry

# Connect to broker
client_id = ubinascii.hexlify(machine.unique_id())

station = network.WLAN(network.STA_IF)
station.active(True)
station.connect(ssid, password)

while station.isconnected() == False:
    pass

print('Connection successful')
print(station.ifconfig())
