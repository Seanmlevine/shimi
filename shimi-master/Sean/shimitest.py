import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import numpy as np
import matplotlib.pyplot as plt
from shimi import *
from motion.move import *
from config.definitions import *
from motion.recorder import *
from motion.playback import *
from motion.generative_phrase import GenerativePhrase
from audio.audio_demos import play_opera


import time
import datetime

import threading

# Load Shimi
shimi = Shimi(silent=False)

local_gestures = {}

#r = Recorder(shimi, shimi.all_motors, 5.0)
#r.record()
#r.plot(plt.axes())

playsound('outkast.wav')
