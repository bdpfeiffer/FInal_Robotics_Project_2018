# This program demonstrates usage of the digital encoders.
# After executing the program, manually spin the wheels and observe the output.
# See https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/ for more details.
import encoders
import servos
import time
import RPi.GPIO as GPIO
import signal
# import pandas as pd

#objects for servos, encoders, sensors, and camera
enc = encoders.Encoders()
serv = servos.Servos()
# Pins that the encoders are connected to
LENCODER = 17
RENCODER = 18

def ctrlC(signum, frame):
    print("Exiting")
    serv.stopServos()
    GPIO.cleanup()
    exit()

def calibrateSpeeds(interval):
    freq = 1.3
    y = 1.3
    while freq <= 1.7 and y <= 1.7:
        serv.setSpeeds(freq, freq)
        time.sleep(1)
        speedTuple2 = enc.getSpeeds()
        print(str((speedTuple2[0] + speedTuple2[1]) / 2) + " RPS")
        freq += interval


# Attach the Ctrl+C signal interrupt
signal.signal(signal.SIGINT, ctrlC)
    
# Set the pin numbering scheme to the numbering shown on the robot itself.
GPIO.setmode(GPIO.BCM)

# Set encoder pins as input
# Also enable pull-up resistors on the encoder pins
# This ensures a clean 0V and 3.3V is always outputted from the encoders.
GPIO.setup(LENCODER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RENCODER, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Attach a rising edge interrupt to the encoder pins
GPIO.add_event_detect(LENCODER, GPIO.RISING, enc.onLeftEncode)
GPIO.add_event_detect(RENCODER, GPIO.RISING, enc.onRightEncode)

serv.setSpeedsIPS(100, 100)
while True:
    time.sleep(1)
    print(enc.getSpeeds())
