import time
from machine import Pin, PWM
import umqttsimple
from servo_lib import Servo
import machine

# Initialization of servomotor using the servo_lib library
sm = Servo(27)
sm.move(85)

# Decodes the message received from the "SERVO" channel to move the servomotor
def sub_cb(topic, msg):
    msg = msg.decode()
    print('Received Message %s from topic %s' % (msg, topic))
    if msg == 'open':
        sm.move(179)
        time.sleep(5)
        sm.move(85)
    else:
        pass
    
# Function that listens to the 'SERVO' channel
def connect_and_subscribe():
    global client_id, mqtt_server, topic_sub
    # client = MQTTClient(client_id, mqtt_server, user='#####', password='####3') # Add if user and password were passed to the broker
    client = MQTTClient(client_id, mqtt_server)
    client.set_callback(sub_cb)
    client.connect()
    client.subscribe(topic_sub)
    print('Connected to %s MQTT broker, subscribed to %s topic' % (mqtt_server, topic_sub))
    return client

def restart_and_reconnect():
    print('Failed to connect to MQTT broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

try:
    client = connect_and_subscribe()
except OSError as e:
    restart_and_reconnect()

while True:
    try:
        new_msg = client.check_msg()
        time.sleep(0.1)
    except OSError as e:
        restart_and_reconnect


