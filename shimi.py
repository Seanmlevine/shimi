from config.definitions import *
from motion.move import *
import utils.utils as utils
import numpy as np
import pypot.dynamixel
import time
from pprint import pprint

class Shimi:
    # Constructor
    def __init__(self):
        # Attempt to load robot model
        # self.robot = pypot.robot.from_json(model_path)

        # Setup serial connection to motors and get the controller
        self.controller = self.setup()

        # Stores active movements
        self.active_moves = {
            TORSO: None,
            NECK_LR: None,
            NECK_UD: None,
            PHONE: None,
            FOOT: None
        }

        # Set motors to initial positions
        self.initial_position()

    # Establishes serial connection to motors
    def setup(self):
        # Find USB to serial converter
        ports = pypot.dynamixel.get_available_ports()

        # Connect to first port for now
        print('Connecting on', ports[0])
        controller = pypot.dynamixel.DxlIO(ports[0])

        # Search for motors
        ids = controller.scan(range(10))
        print('Found motors with the following IDs:', ids)

        # Current settings for found motors
        pprint(controller.get_control_table(ids))

        return controller

    @property
    def torso(self):
        return TORSO

    @property
    def neck_ud(self):
        return NECK_UD

    @property
    def neck_lr(self):
        return NECK_LR

    @property
    def phone(self):
        return PHONE

    @property
    def foot(self):
        return FOOT

    @property
    def all_motors(self):
        return [TORSO, NECK_UD, NECK_LR, PHONE, FOOT]

    # Moves the motors to the initial position set in config/definitions
    def initial_position(self, move_style='linear'):
        # Make sure torque is enabled
        self.enable_torque()

        print("Setting motors to starting positions:")
        pprint(STARTING_POSITIONS)
        # self.robot.goto_position({m.name: STARTING_POSITIONS[m.id] for m in self.robot.motors}, 1.0, wait=True)
        moves = []
        for m in self.all_motors:
            if move_style == 'linear_accel':
                move = LinearAccelMove(self, m, STARTING_POSITIONS[m], 1.0)
            else:
                move = LinearMove(self, m, STARTING_POSITIONS[m], 1.0)
            moves.append(move)

        # Start all the moves
        for move in moves:
            move.start()

        # Wait for all the moves to finish
        for move in moves:
            move.join()

    # Turns off torque so they can be moved by hand
    def disable_torque(self):
        # Disable torque for all motors
        self.controller.disable_torque(self.all_motors)

    # Turns on torque, making the motors rigid
    def enable_torque(self):
        # Enable torque for all motors
        self.controller.enable_torque(self.all_motors)

    # # Returns a recorder with the specified motors
    # def get_recorder(self, motors):
    #     return MoveRecorder(self.robot, 50, motors)
    #
    # # Starts and ends a recording
    # def make_recording(self, recorder, wait_time=3, recording_time=10):
    #     # Make the motors compliant if they're not already
    #     self.make_compliant()
    #
    #     # For counting down
    #     timer = wait_time
    #
    #     # Count down
    #     while timer > 0:
    #         print(str(timer) + "...")
    #         time.sleep(1)
    #         timer -= 1
    #
    #     # Start recording
    #     print("Starting to record!")
    #     recorder.start()
    #
    #     # Sleep for record time
    #     time.sleep(recording_time)
    #
    #     # Stop recording
    #     print("Recording stopped.")
    #     recorder.stop()
    #
    #     # Print number of frames
    #     print("{0} frames recorded.".format(len(recorder.move.positions())))
    #
    #     return recorder
    #
    # # Plays back recordings
    # def play_recordings(self, recorders, blocking=True):
    #     players = []
    #
    #     # Creates MovePlayers
    #     for recorder in recorders:
    #         players.append(MovePlayer(self.robot, recorder))
    #
    #     # Start playback
    #     for player in players:
    #         player.start()
    #
    #     # Wait for the longest to stop
    #     if(blocking):
    #         longest = players[0]
    #
    #         # Find the longest-lasting recording
    #         for i in range(1, len(players)):
    #             if players[i].duration() > longest.duration():
    #                 longest = players[i]
    #
    #         longest.wait_to_stop()

