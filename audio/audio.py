import simpleaudio as sa
from shimi import *
from motion.move import *
import threading
import time

def play_outkast(shimi):
    # Move to initial positions
    shimi.initial_position()

    # Rest for a little
    time.sleep(0.5)

    # Load the song
    outkast = sa.WaveObject.from_wave_file('audio/Hey_Ya-OutKast.wav')

    # Start playback
    play_obj = outkast.play()

    beat = 0.68

    neck_lr = LinearAccelMove(shimi, shimi.neck_lr, 0.2, 0.5, normalized_positions=True)
    neck_lr.add_move(0.5, 0.5, delay=0.2)
    neck_lr.add_move(0.7, beat, delay=0.3)
    for i in range(6):
        neck_lr.add_move(0.3, beat)
        neck_lr.add_move(0.7, beat)

    neck_ud = LinearAccelMove(shimi, shimi.neck_ud, 0.2, 0.5, normalized_positions=True)
    neck_ud.add_move(0.9, beat, delay=0.5)
    for i in range(3):
        neck_ud.add_move(0.2, 2 * beat)
        neck_ud.add_move(0.9, 2 * beat)

    foot = LinearAccelMove(shimi, shimi.foot, 1.0, 0.5, normalized_positions=True)

    foot_lin = LinearMove(shimi, shimi.foot, 0.0, beat / 4, initial_delay=1.0, normalized_positions=True)
    for i in range(3):
        foot_lin.add_move(1.0, beat / 4, delay=2 * beat)
        foot_lin.add_move(0.0, beat / 4, delay=2 * beat)

    torso = LinearAccelMove(shimi, shimi.torso, 0.7, 0.7, initial_delay=1.0, normalized_positions=True, min_vel=40)
    for i in range(6):
        torso.add_move(0.95, beat)
        if i % 2 == 0:
            torso.add_move(0.7, beat)
        else:
            torso.add_move(0.63, beat)
    torso.add_move(0.95, beat)

    neck_lr.start()
    neck_ud.start()
    foot.start()
    foot_lin.start()
    torso.start()

    time.sleep(12 * beat + 1.0)
    play_obj.stop()