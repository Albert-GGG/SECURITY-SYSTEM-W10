# ESP-32 Microcontroller Files in Micropython to Activate the Entrance Mechanism

## Description:

"Main.py" contains the main code that connects to the MQTT broker as a client and actively listens to the signals that activate the entrance mechanism by controlling the *servomotor* or actuator connected to it.

### Files

- boot.py: Initialization of mictocontroller
- main.py: Code that connects to the broker and activates the mechanism when a signal is received.
- servo_lib.py: Library used to control the stepper mottor.
- umqttsimple.py: Library that allows the connection to the MQTT broker.

The code to use the MQTT communication protocol was obtained from <https://randomnerdtutorials.com/micropython-mqtt-esp32-esp8266/> and it was modified to work with the entrance mechanism system.