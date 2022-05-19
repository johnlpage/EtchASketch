#!/usr/bin/python
import cv2
from pprint import pprint

import numpy as np
import logging
import RPi.GPIO as GPIO
import time
from enum import Enum
from math import sin,cos
import sys

class Motors(object):

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
            time.sleep(0.002)
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
            
            #Check first and last points in contour
def distance_to_contour(contour,x,y):
   first = True
 
   firstpoint = contour[0][0]
   px = firstpoint[0]
   py = firstpoint[1]
   d = ((px-x)**2 + (py-y)**2)**0.5
   lastpoint = contour[0][-1]
   px = lastpoint[0]
   py = lastpoint[1]
   d2 = ((px-x)**2 + (py-y)**2)**0.5
   if d2<d :
         return d2,False

   return d,True

#Finds the nearest contour to the location
#Returns it and the list without it


def get_nearest_contour(contours,x,y):
    if len(contours) == 0:
         return (None,[])

    unused = []
    found = None
    founddist = 99999999999

    for contour in contours:
        (dist,first) = distance_to_contour(contour,x,y)
        
        if dist < founddist:
            if founddist != 99999999999:
                unused.append(found)
            founddist = dist
            if first:
                found = contour
            else:
                found = reverse(contour)
        else:
            unused.append(contour)
    
    return (found,unused)


if __name__ == "__main__":
    try:
        print("Testing class Motors standalone")
        motors = Motors();
        motors.setup_motors();


        image = cv2.imread('joe.jpg')  

        ox = image.shape[0]
        oy = image.shape[1]
        scaley = 900 / image.shape[1]
        scalex = 1200 / image.shape[0]

        #Scale to screen
        scale = min(scalex,scaley)
        image=cv2.resize(image,(int(scale*ox),int(scale*oy)),interpolation = cv2.INTER_AREA);
        #Grayscale
        img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        #Contrast/Brightness
        #contrast=1.5
        #brightness=2
        #img_gray = cv2.addWeighted( img_gray, contrast, img_gray, 0, brightness)
    
        img_gray = cv2.fastNlMeansDenoising(   img_gray,None,h=10)
        
        cv2.imshow('base', img_gray )

        allcontours=[]
        levels = 4
        for c in range(1,levels):
            ret,thimg = cv2.threshold( img_gray,c*(256/levels),255,cv2.THRESH_BINARY_INV)
            #cv2.imshow('out'+str(c),thimg)
            (levelcontours, hierarchy)  = cv2.findContours(thimg, cv2.RETR_LIST ,cv2.CHAIN_APPROX_SIMPLE)
            #pprint(levelcontours)
            #print(levelcontours)
            allcontours.append(levelcontours)
            print(len(levelcontours))
           

        contours = np.concatenate(allcontours)
        #pprint(contours)
        #Have to sort so we dont move too far each time
        #First, remove any small ones
        #contours = list(filter(lambda x: len(x)>5,contours))




        plan = np.zeros(image.shape, np.uint8)
        cv2.drawContours(plan, contours,  -1, (0,255,0), 1)
        plan = cv2.cvtColor(plan, cv2.COLOR_BGR2GRAY)
        plan = np.invert(plan)

        cv2.imshow('lines',plan)
        cv2.waitKey(0)
        ncontours = len(contours)

        (contour,remaining) =  get_nearest_contour(contours,0,0)
        scaling = 15
        while  isinstance(contour, type(None)) == False:
            ncontours -= 1
            print(F"{ncontours} {len(contour)} segments")
            for segment in contour:
                for point in segment:
                    (absx,absy) = motors.absLine(point[0]*scaling,point[1]*scaling)
            absx /= scaling
            absy /= scaling
            (contour,remaining) =  get_nearest_contour(remaining,absx,absy)

    except KeyboardInterrupt:
         pass
    finally:
        cv2.destroyAllWindows() 
        GPIO.cleanup()
