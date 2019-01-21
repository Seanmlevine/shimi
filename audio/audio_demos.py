import pygame.mixer as mixer
from motion.recorder import *
from motion.move import *
import threading
import time


def play_outkast(shimi, **kwargs):
    # Move to initial positions
    shimi.initial_position()

    # Initialize audio mixer
    mixer.init()

    # Load song
    mixer.music.load('audio/outkast.wav')

    # Rest for a little
    time.sleep(0.5)

    beat = 0.68

    neck_lr = Move(shimi, shimi.neck_lr, 0.2, 0.5, vel_algo='linear_ad', normalized_positions=True)
    neck_lr.add_move(0.5, 0.5, delay=0.2)
    neck_lr.add_move(0.7, beat, delay=0.3)
    for i in range(5):
        neck_lr.add_move(0.3, beat)
        neck_lr.add_move(0.7, beat)
    neck_lr.add_move(0.2, 4 * beat)
    neck_lr.add_move(0.8, (4 * beat) - beat / 2, delay=4 * beat)
    neck_lr.add_move(0.5, beat / 2)

    neck_ud = Move(shimi, shimi.neck_ud, 0.2, 0.5, vel_algo='linear_ad', normalized_positions=True)
    neck_ud.add_move(0.9, beat, delay=0.5)
    for i in range(2):
        neck_ud.add_move(0.2, 2 * beat)
        neck_ud.add_move(0.9, 2 * beat)

    neck_ud.add_move(0.1, beat, delay=15 * beat)
    for i in range(5):
        neck_ud.add_move(0.9, beat)
        neck_ud.add_move(0.1, beat)
    neck_ud.add_move(0.9, beat)

    neck_ud_lin = Move(shimi, shimi.neck_ud, 0.2, beat / 4, initial_delay=1.0 + (12.5 * beat),
                       normalized_positions=True)
    for i in range(10):
        neck_ud_lin.add_move(0.8, beat / 4)
        neck_ud_lin.add_move(0.2, beat / 4)
    neck_ud_lin.add_move(0.9, beat / 2, delay=1.5 * beat)
    neck_ud_lin.add_move(0.2, beat / 4, delay=0.5 * beat)
    for i in range(6):
        neck_ud_lin.add_move(0.8, beat / 4)
        neck_ud_lin.add_move(0.2, beat / 4)
    neck_ud_lin.add_move(0.8, beat / 2)

    foot = Move(shimi, shimi.foot, 1.0, 0.5, vel_algo='linear_ad', normalized_positions=True)

    foot_lin = Move(shimi, shimi.foot, 0.0, beat / 4, initial_delay=1.0, normalized_positions=True)
    for i in range(2):
        foot_lin.add_move(1.0, beat / 4, delay=2 * beat)
        foot_lin.add_move(0.0, beat / 4, delay=2 * beat)
    foot_lin.add_move(1.0, beat, delay=2 * beat)

    for i in range(10):
        foot_lin.add_move(0.2, beat)
        foot_lin.add_move(1.0, beat)
    foot_lin.add_move(0.0, 2 * beat)

    torso = Move(shimi, shimi.torso, 0.7, 0.7, initial_delay=1.0, vel_algo='linear_ad', vel_algo_kwarg={'min_vel': 40},
                 normalized_positions=True)
    for i in range(5):
        torso.add_move(0.95, beat)
        if i % 2 == 0:
            torso.add_move(0.7, beat)
        else:
            torso.add_move(0.63, beat)
    torso.add_move(0.95, beat)
    torso.add_move(0.5, beat * 2, delay=12 * beat)
    for i in range(2):
        torso.add_move(0.95, beat * 2)
        torso.add_move(0.5, beat * 2)
    torso.add_move(0.95, beat)

    # Start moves
    neck_lr.start()
    neck_ud.start()
    neck_ud_lin.start()
    foot.start()
    foot_lin.start()
    torso.start()

    # Start song
    mixer.music.play()


def play_opera(shimi, **kwargs):
    # Move to initial positions
    shimi.initial_position()

    # Initialize audio mixer
    mixer.init()

    # Load song
    mixer.music.load('audio/opera_long.wav')

    # Load the movement
    r = load_recorder(shimi, "opera")

    # Start moving
    move = threading.Thread(target=r.play)
    move.start()

    # Allow for move to catch up
    time.sleep(2.7)

    # Start playback
    mixer.music.play()

    # Wait for move to end
    move.join()

    # Move back to initial position
    shimi.initial_position()
