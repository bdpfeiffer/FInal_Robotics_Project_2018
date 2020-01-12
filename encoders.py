import time
import Adafruit_PCA9685
import signal
import math
import pprint
import servos
import json


class Encoders(object):

    def __init__(self):
        self.velArrayRight = []
        self.velArrayLeft = []
        self.rightTicks = 0
        self.leftTicks = 0
        self.startTime = time.time()
        self.speedRecord = 2 #number of values to record in record of speed. Min val is 2. Bigger values are less instantaneous but more reliable.
        self.notMovingTimeout = 1 # time in s before declared as not moving if no encoders ticked. The smaller the value, the less accurate but the higher the response time.
        #for calibration
        self.calibrating = False
        self.wheelTicksLeft = 0
        self.wheelTicksRight = 0
        self.calibrationArrayRight = [] #these two arrays hold values for speed that will be averages for each speed increment and put into the json
        self.calibrationArrayLeft = []
        self.accuracy = 10 #will record speed this number of time and average result

    # This function is called when the left encoder detects a rising edge signal.
    def onLeftEncode(self, pin):
        #print("Left encoder ticked!")
        self.leftTicks += 1
        self.velArrayLeft.append((time.time(), self.leftTicks))
        if (len(self.velArrayLeft) > self.speedRecord):
            self.velArrayLeft = self.velArrayLeft[1:(self.speedRecord + 1)]
        if (self.calibrating):
            self.wheelTicksLeft += 1
            self.calibrationArrayLeft.append(self.getSpeeds()[0]) #append current left speed to array

    # This function is called when the right encoder detects a rising edge signal.
    def onRightEncode(self, pin):
        #print("Right encoder ticked!")
        self.rightTicks += 1
        self.velArrayRight.append((time.time(), self.rightTicks))
        if (len(self.velArrayRight) > self.speedRecord):
            self.velArrayRight = self.velArrayRight[1:(self.speedRecord + 1)]
        if (self.calibrating):
            self.wheelTicksRight += 1
            self.calibrationArrayRight.append(self.getSpeeds()[1]) #append current right speed to array

    def resetCounts(self):
        self.rightTicks = 0
        self.leftTicks = 0

    def getCounts(self):
        return (self.leftTicks, self.rightTicks)

    def getSpeeds(self):
        totalTime = self.getElapsedTime()
        moving = self.isSpeedZero()
        #pprint(self.velArrayLeft)
        #pprint(self.velArrayRight)
        leftLength = len(self.velArrayLeft)
        rightLength = len(self.velArrayRight)
        # return(
        # (velArrayLeft[1][leftLength - 1] - velArrayLeft[1][leftLength - 2]) / (velArrayLeft[0][leftLength - 1] - velArrayLeft[0][leftLength - 2]),
        # (velArrayRight[1][rightLength - 1] - velArrayRight[1][rightLength - 2]) / (velArrayRight[0][rightLength - 1] - velArrayRight[0][rightLength - 2]))
        if rightLength > 0 and leftLength > 0 and totalTime > 0:
            # I think all of this was wrong
            # self.totalTimeLeft = 0
            # self.totalTicksLeft = 0
            # for (time, ticks) in self.velArrayLeft:
            #     self.totalTimeLeft += time
            #     self.totalTicksLeft += ticks 
            #     #print(val)
            # self.totalTimeRight = 0
            # self.totalTicksRight = 0
            # for (time, ticks) in self.velArrayRight:
            #     self.totalTimeRight += time
            #     self.totalTicksRight += ticks
            #     #print(val)
            if ((self.velArrayLeft[leftLength - 1][0] - self.velArrayLeft[0][0]) > 0 and (self.velArrayRight[rightLength - 1][0] - self.velArrayRight[0][0]) > 0):
                speedLeft = (self.velArrayLeft[leftLength - 1][1] - self.velArrayLeft[0][1]) / (self.velArrayLeft[leftLength - 1][0] - self.velArrayLeft[0][0])
                speedRight = (self.velArrayRight[rightLength - 1][1] - self.velArrayRight[0][1]) / (self.velArrayRight[rightLength - 1][0] - self.velArrayRight[0][0])
            else:
                print('is failing if')
                return (0, 0)
            # return (self.totalTicksLeft / totalTime / 32 * moving[0], self.totalTicksRight / totalTime / 32 * moving[1])
            return (speedLeft / 32 * moving[0], speedRight / 32 * moving[1])
        else:
            return (0, 0)

    def getElapsedTime(self):
        return time.time() - self.startTime
    def isSpeedZero(self): #returns 0 for stopped, 1 for moving as a tuple (left, right)
        rightMoving = 1
        leftMoving = 1
        if (len(self.velArrayLeft) > 0):
            timeSinceLeft = time.time() - self.velArrayLeft[len(self.velArrayLeft) - 1][0]
        else:
            timeSinceLeft = 0
        if (len(self.velArrayRight) > 0):
            timeSinceRight = time.time() - self.velArrayRight[len(self.velArrayRight) - 1][0]
        else:
            timeSinceRight = 0
        #print((timeSinceLeft, timeSinceRight))
            
        if timeSinceRight > self.notMovingTimeout:
            rightMoving = 0
        if timeSinceLeft > self.notMovingTimeout:
            leftMoving = 0
        return (leftMoving, rightMoving)


    def calibrateSpeeds(self):
        calServ = servos.Servos()
        self.calibrating = True
        print('Starting calibration...')
        calibrationData = {} #dictionary containing calibration data
        calibrationData['left'] = {}
        calibrationData['right'] = {}
        rightStage = 1.2 #PWM freq for right
        leftStage = 1.8 #PWM freq for left
        print('CCW stage beginning...')
        while (rightStage < 1.5 and leftStage > 1.5):
            print('Collecting data for (' + str(leftStage) + ', ' + str(rightStage) + ')...')
            calServ.setSpeeds(leftStage, rightStage)
            print('Waiting for ticks...')
            while(self.wheelTicksLeft < self.accuracy + 1 and self.wheelTicksRight < self.accuracy + 1): #while loop is just to wait for more ticks
                #speed = self.getSpeeds()
                #if speed[0] == 0 or speed[1] == 0 and rightStage > 1.4 and leftStage < 1.6:
                    #rightStage = 1.5
                    #leftStage = 1.5
                    #break
                pass
            print('Got the ticks!')
            averageSpeedLeft = sum(self.calibrationArrayLeft[-self.accuracy:]) / self.accuracy #averages last x elements of left array, left out first because it may not be accurate
            averageSpeedRight = sum(self.calibrationArrayRight[-self.accuracy:]) / self.accuracy #averages last x elements of right array
            calibrationData['left'][averageSpeedLeft] = leftStage
            calibrationData['right'][-averageSpeedRight] = rightStage
            print('Average speed left: ' + str(averageSpeedLeft))
            print('Average speed right: ' + str(averageSpeedRight))
            #empty everything and reset for next stage
            self.calibrationArrayLeft = []
            self.calibrationArrayRight = []
            self.wheelTicksLeft = 0
            self.wheelTicksRight = 0
            # if (leftStage > 1.6 and rightStage < 1.4):
            #     rightStage += 0.01
            #     leftStage -= 0.01
            if(leftStage > 1.52 and rightStage < 1.48): #would be miserable going slower than this
                rightStage += 0.005
                leftStage -= 0.005
            else:
                rightStage = 1.5
                leftStage = 1.5
        #reset for another run in the opposite direction
        print('CW stage beginning...')
        rightStage = 1.8 #PWM freq for right
        leftStage = 1.2 #PWM freq for left
        while (rightStage > 1.5 and leftStage < 1.5):
            print('Collecting data for (' + str(leftStage) + ', ' + str(rightStage) + ')(1.5, 1.5)...')
            calServ.setSpeeds(leftStage, rightStage)
            print('Waiting for ticks...')
            while(self.wheelTicksLeft < self.accuracy + 1 and self.wheelTicksRight < self.accuracy + 1): #while loop is just to wait for more ticks
                #speed = self.getSpeeds()
                #if speed[0] == 0 or speed[1] == 0 and rightStage > 1.4 and leftStage < 1.6:
                    #rightStage = 1.5
                    #leftStage = 1.5
                    #break
                pass
            print('Got the ticks!')
            averageSpeedLeft = sum(self.calibrationArrayLeft[-self.accuracy:]) / self.accuracy #averages last x elements of left array, left out first because it may not be accurate
            averageSpeedRight = sum(self.calibrationArrayRight[-self.accuracy:]) / self.accuracy #averages last x elements of right array
            calibrationData['left'][-averageSpeedLeft] = leftStage
            calibrationData['right'][averageSpeedRight] = rightStage
            print('Average speed left: ' + str(averageSpeedLeft))
            print('Average speed right: ' + str(averageSpeedRight))
            #empty everything and reset for next stage
            self.calibrationArrayLeft = []
            self.calibrationArrayRight = []
            self.wheelTicksLeft = 0
            self.wheelTicksRight = 0
            # if (leftStage < 1.4 and rightStage > 1.6):
            #     rightStage -= 0.01
            #     leftStage += 0.01
            if(leftStage < 1.48 and rightStage > 1.52): #would be miserable going slower than this
                rightStage -= 0.005
                leftStage += 0.005
            else:
                rightStage = 1.5
                leftStage = 1.5
        print('Turning off servos.')
        calServ.stopServos()
        #write to file
        with open('calibration.json', 'w') as writeFile:
            json.dump(calibrationData, writeFile, indent=4, separators=(',',': '), sort_keys=True)
        self.calibrating = False

