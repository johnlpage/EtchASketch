#!/usr/bin/python

from etchasketch import EtchASketch

import cv2
from pprint import pprint
import numpy as np
import time
from math import sin,cos
import sys
import logging
import pymongo


#CV2 image Processing

def image_to_contours(filename,toPrint):
    logging.info("Loading Image")
    image = cv2.imread(filename) 
    logging.info("Scaling Image")  
    #Scale to Required Size to fit screen ratio
    oy = image.shape[0]
    ox = image.shape[1]
    logging.info(F"Image Size {ox} x {oy}")
    scaley = 900 / oy
    scalex = 1200 / ox
    scale = min(scalex,scaley)
   
    image=cv2.resize(image,(int(scale*ox),int(scale*oy)),interpolation = cv2.INTER_AREA);
    
    oy = image.shape[0]
    ox = image.shape[1]
    logging.info(F"New Image Size {ox} x {oy}")

    logging.info("Smoothing Contours")
    #Greyscale and denoise
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.fastNlMeansDenoising(   img_gray,None,h=10) 

    #Find contours at N different Grey levels
    allcontours=[]

    #levels = 4
    
    #for c in range(1,levels):
        #print(F"Threshold {c}")
        #ret,thimg = cv2.threshold( img_gray,c*(256/levels),255,cv2.THRESH_BINARY_INV)
        
    thimg  = cv2.adaptiveThreshold( img_gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
    
    levelcontours, hierarchy  = cv2.findContours(thimg, cv2.RETR_LIST ,cv2.CHAIN_APPROX_SIMPLE)

    for contour in levelcontours:
        #The Numpy contour format is not playing nice so we are going to convert to a list here
        newcontour = []
        for p in contour:
            coord = [p[0][0],p[0][1]]
            newcontour.append(coord)
        allcontours.append(newcontour)
            
    
    writePlanBack(levelcontours,image,toPrint)
    #Discard the longest as it's the outer border
    #allcontours.sort(key=len)
    #for c in range(1,levels):
    #    allcontours.pop()
    
    return allcontours


            

#Finds the nearest contour to existing
#Returns it and the list without it as well as closest points

def distance_to_contour(source,target):
    dmax = 99999999
    si=0
    ti=0
    for sourceindex,sourceitem in enumerate(source):
        sx=sourceitem[0]
        sy=sourceitem[1]
        for targetindex,targetitem in enumerate(target):
            tx=targetitem[0]
            ty=targetitem[1]
            d = ((tx-sx)**2 + (ty-sy)**2)
            if d < dmax:
                dmax = d
                si=sourceindex
                ti=targetindex
    return (dmax,si,ti)


def writePlanBack(wbcontours,image,toPrint):
   
    plan = np.zeros(image.shape, np.uint8)
    cv2.drawContours(plan, wbcontours,  -1, (255,255,255), 1)
    #plan = cv2.cvtColor(plan, cv2.COLOR_BGR2GRAY)
    plan = np.invert(plan)
    cv2.imwrite('/tmp/plan.jpg', plan)
    is_success, im_buf_arr = cv2.imencode(".jpg", plan)
    #Shoudl write this back to the mobile app
    _id = toPrint['_id']
    mongoclient.etch.images.update_one({"_id":_id},{"$set":{"plan":im_buf_arr.tobytes()}})


#Need to look at all points on the contour we just drew
#and all points elsewhere and find the shortest jump 
#Then backtrack to the jump off point and hop over.


def get_nearest_contour(remaining,source):
    if len(remaining) == 0:
         return (None,0,0,[])

    unused = []
    found = None
    founddist = 99999999999
    #Check all remaining for miniumum distance
    for cidx,contour in enumerate(remaining):
        #logging.info(F"{cidx} of {len(contours)}")
        (dist,si,ti) = distance_to_contour(source,contour)
        if dist < founddist:
            if founddist != 99999999999:
                unused.append(found[0])
            founddist = dist
            found = (contour,si,ti,cidx)
        else:
            unused.append(contour) 
    
    return (found[0],found[1],found[2],unused)


def drawimage(filename,toPrint):
    logging.info(F"Processing Image {filename}")
    contours = image_to_contours(filename,toPrint)

    contour=[[0,0]]
    remaining = contours

    scaling = 15

    while  isinstance(contour, type(None)) == False:
        print(F"Rendering contour length {len(contour)}")
        for point in contour:  
            #pprint(point)     
            etchasketch.absLine(point[0]*scaling,point[1]*scaling)


        source = contour
        logging.info("Looking for nearest contour")
        (contour,si,ti,remaining) =  get_nearest_contour(remaining,source)
        if contour != None:
            print(F"Found Nearest={len(contour)} si={si} ti={ti} remaining={len(remaining)}")
    

            sourcetobridge = source[si:]
            sourcetobridge.reverse() 

            #TODO Work out shortest route to an end
            clen = len(contour)
            #print(F"Contourlen {clen} Start{ti}")
            if ti > clen/2:
                targettostart = contour[ti:]
                contour.reverse()
            else:
                targettostart = contour[:ti]
                targettostart.reverse()
            
            
            #print(F"Retracing to Bridge {len(sourcetobridge)} points")
            for point in sourcetobridge:
                etchasketch.absLine(point[0]*scaling,point[1]*scaling)
            
            #print(F"Bridge to Start {len(targettostart)} points")
            for point in targettostart:
                etchasketch.absLine(point[0]*scaling,point[1]*scaling)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        etchasketch = EtchASketch();
        logging.info("Enabling Motors")
        etchasketch.setup_motors();


        logging.info("Connecting to MongoDB")
       
        with open("/home/pi/.mongo_uri.txt") as f:
            uri = f.readline().strip()
            mongoclient = pymongo.MongoClient(uri)
            pprint(mongoclient.etch.command({"ping":1}))
        while True:
            toPrint = mongoclient.etch.images.find_one_and_update({"status":"new"},{"$set":{"processed":"done"}})
            
            #pprint(toPrint)
            if toPrint == None:
                print("Sleeping")
                time.sleep(5)  
            else:
                f = open('/tmp/image.jpg', 'wb')
                f.write(toPrint['image'])
                f.close()
                drawimage("/tmp/image.jpg",toPrint)
                exit(1); #Need to clear the screen




    except KeyboardInterrupt:
         pass
    finally:
        cv2.destroyAllWindows() 
        etchasketch.cleanup()


