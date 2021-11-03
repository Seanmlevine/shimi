import numpy as np
import matplotlib.pyplot as plt
from shimi import *
from motion.move import *
from config.definitions import *
from motion.recorder import *
from motion.playback import *
from motion.generative_phrase import *
from motion.jam import *
from utils.utils import *

import time
import datetime

from copy import deepcopy

import os

import threading

# Load Shimi
shimi = Shimi(silent=False)

local_gestures = {}

### Proper Recording and playback of motor movements

#r = Recorder(shimi, shimi.all_motors, 10.0)
#r.record()
#r.plot(plt.axes())
#r.play(vel_ax=plt.axes())

### Jam

j = Jam(shimi, 1.0, 10.0)
j.run() 

