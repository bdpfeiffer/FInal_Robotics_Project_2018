import time
import Adafruit_PCA9685
import signal
import math
import encoders
import json
import bisect
from collections import OrderedDict

class Servos(object):

    def __init__(self):
        # Initialize the servo hat library.
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pwm.set_pwm_freq(50)
        self.LSERVO = 0
        self.RSERVO = 1
        self.calibrationDataLeftRPS = []
        self.calibrationDataRightRPS = []
        self.calibrationDataLeftMS = []
        self.calibrationDataRightMS = []
        self.loadJSON()
        #  = json.load(open('calibration.json', 'r'), object_pairs_hook=OrderedDict) #opens json as ordered dict
        # self.calibrationData['right'] = {float(k):v for k, v in self.calibrationData['right'].items()} #converts keys from strings to floats for right side
        # self.calibrationData['left'] = {float(k):v for k, v in self.calibrationData['left'].items()} #converts keys from strings to floats for left side

    def loadJSON(self):
        left = False
        right = False
        with open('calibration.json', 'r') as json:
            for line in json:
                if "left" in line:
                    left = True
                    right = False
                    continue
                elif "right" in line:
                    right = True
                    left = False
                    continue
                elif "{" in line or "}" in line:
                    continue
                else:
                    numberString = line.replace(",", "").replace("\"", "").replace(" ", "").replace("\n", "")
                    numberArray = numberString.split(":")
                    numberArray[0] = float(numberArray[0])
                    numberArray[1] = float(numberArray[1])
                    if (left):
                        self.calibrationDataLeftRPS.append(numberArray[0])
                        self.calibrationDataLeftMS.append(numberArray[1])
                    if (right):
                        self.calibrationDataRightRPS.append(numberArray[0])
                        self.calibrationDataRightMS.append(numberArray[1])                                                                                                                

    def stopServos(self):
        self.pwm.set_pwm(self.LSERVO, 0, 0)
        self.pwm.set_pwm(self.RSERVO, 0, 0)

    def setSpeeds(self, left, right):
        # print("left: " + str(left))
        # print("right: " + str(right))
        self.pwm.set_pwm(self.LSERVO, 0, math.floor(left / 20 * 4096))
        self.pwm.set_pwm(self.RSERVO, 0, math.floor((3 - right) / 20 * 4096))

    #all of this is for calibration    

    def setSpeedsRPS(self, rpsLeft, rpsRight):        
        self.setSpeeds(self.retrieveJSONSpeed("left", rpsLeft), self.retrieveJSONSpeed("right", rpsRight))
        

    def setSpeedsIPS(self, ipsLeft, ipsRight):
        self.setSpeedsRPS(ipsLeft / (2.61 * math.pi), ipsRight / (2.61 * math.pi))

# def setSpeedsvw(v, w):
        #self.pwm.set_pwm(self.LSERVO, 0, math.floor(left / 20 * 4096))
        #self.pwm.set_pwm(self.RSERVO, 0, math.floor((3 - right) / 20 * 4096))

    def printCalibrationData(self):
        print(self.calibrationDataLeft)
        print(self.calibrationDataRight)
        
    def retrieveJSONSpeed(self, side, rps): #side is string
        if side == "left":
            index = bisect.bisect_left(self.calibrationDataLeftRPS, rps) #finds first index that has key larger than rps
            if index == len(self.calibrationDataLeftRPS):
                index -= 1
            if abs(rps - self.calibrationDataLeftRPS[index]) >= abs(rps - self.calibrationDataLeftRPS[index - 1]):
                return self.calibrationDataLeftMS[index - 1]
            else:
                return self.calibrationDataLeftMS[index]
        if side == "right":
            index = bisect.bisect_left(self.calibrationDataRightRPS, rps) #finds first index that has key larger than rps
            if index == len(self.calibrationDataRightRPS):
                index -= 1
            if abs(rps - self.calibrationDataRightRPS[index]) >= abs(rps - self.calibrationDataRightRPS[index - 1]):
                return self.calibrationDataRightMS[index - 1]
            else:
                return self.calibrationDataRightMS[index]


        # return min(abs(rps - list(self.calibrationData[side].values())[index]), abs(rps - list(self.calibrationData[side].values())[index - 1]))
        
 #finds first index that has key larger than rps
