import logging
import RPi.GPIO as GPIO
import time

class EtchASketch(object):

    __right_motor_pins = [17,18,27,22]
    __left_motor_pins = [10,9,25,11]

    __motor_pins = [__left_motor_pins,__right_motor_pins]
    __minstep_us = 1500 #How long to energize for
    __absx = 0
    __absy = 0
    __first = True

    __motor_steps = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
    ]

    def cleanup(self):
        GPIO.cleanup()

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        logging.basicConfig(level=logging.INFO)
        self.step = [0,0]


    def setup_motors(self):
        for pin in self.__right_motor_pins + self.__left_motor_pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, 0)

    def step_motor(self,side,direction):
        direction=-int(direction)
        self.step[side] = (self.step[side]  + direction + 8) % 8
        for pin in range(4):
            GPIO.output(self.__motor_pins[side][pin], self.__motor_steps[self.step[side]][pin])
    

    def absLine(self,x,y):
        
        if self.__first == True:
            self.__first = False
            self.__absx = 0
            self.__absy = 0
        #print(F"{self.__absx},{self.__absy} to {x},{y} is {x - self.__absx},{y-self.__absy}")
        (dx,dy) = self.relativeLine(x - self.__absx,y-self.__absy)
        #print(F"-> {dx},{dy}")
        self.__absx += dx
        self.__absy += dy
        return (self.__absx,self.__absy)

    def relativeLine(self,x,y):
        bigcount=0
        smallcount=0

        if x==0:
            x=0.0000001
        if y==0:
            y=0.0000001

        if(x>0):
             x=x*1.005
        if(y<0):
            y=y*1.1

        if abs(x) > abs(y):
            motororder = [0,1]
            ratio = abs(y/x)
            big=int(abs(x))
            bigsign = int(x/abs(x));
            smallsign = int(y/abs(y));
        else:
            motororder = [1,0]
            ratio = abs(x/y)
            big = int(abs(y))
            bigsign = int(y/abs(y));
            smallsign = int(x/abs(x));

        smallsteps=0
        for c in range(big ):
            time.sleep(0.001)
            self.step_motor(motororder[0],bigsign)
            bigcount += bigsign
            #Steping this one
            
            if smallsteps < float(c) * ratio:
                smallsteps +=1
                self.step_motor(motororder[1],smallsign)
                smallcount += smallsign
        
        if abs(x) > abs(y):        
            return (bigcount,smallcount)
        else:
            return (smallcount,bigcount)