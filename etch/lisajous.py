#!/usr/bin/python


import logging
import RPi.GPIO as GPIO
import time
from enum import Enum
from math import sin,cos
from etchasketch import EtchASketch


if __name__ == "__main__":
    a = 0
    b = 2
    c=3000

    try:
        etchasketch = EtchASketch();
        logging.info("Enabling Motors")
        etchasketch.setup_motors();

        for p in range(1,200):
            x = (p*a+c)*sin(p*b)
            y = (p*a+c)*cos(p*b)
            print(F"{x},{y}")
            etchasketch.absLine(x,y)
    except KeyboardInterrupt:
         pass
    except Exception as e:
         logging.error(e)
    finally:
         GPIO.cleanup()
