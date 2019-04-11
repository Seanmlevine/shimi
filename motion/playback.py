import numpy as np
from scipy.interpolate import UnivariateSpline
from motion.move import Move
import time

# Constants
TIME_INDEX = 0
POS_INDEX = 1
ERROR = 0.00001
INTERP_FREQ = 0.01

def playback(shimi, motors, duration, timestamps, pos_matrix, vel_matrix, pos_ax=None, vel_ax=None,
             use_pos_spl=True, use_vel_spl=False, callback=None):
    """Actuates motors based on input positions and velocities.
    
    Args:
        shimi (Shimi): An instance of the Shimi motor controller class.
        motors (List[int]): Motors IDs to play back the recorded.
        duration (float): Length of the playback in seconds.
        timestamps (List[float]): The timestamps of the position and velocity data.
        pos_matrix (List[List[float]]): The position data for each motor.
        vel_matrix (List[List[float]]): The velocity data for each motor.
        pos_ax (matplotlib.pyplot.axis, optional): Defaults to None. An axis to plot position data on through pyplot.
        vel_ax (matplotlib.pyplot.axis, optional): Defaults to None. An axis to plot velocity data on through pyplot.
        use_pos_spl (bool, optional): Defaults to True. Determines whether to us univariate spline smoothing on position data.
        use_vel_spl (bool, optional): Defaults to False. Determines whether to us univariate spline smoothing on velocity data.
        callback (function, optional): Defaults to None. A function called when movement starts.
    """

    # Ensure all inputs are np arrays
    if not isinstance(timestamps, np.ndarray):
        timestamps = np.array(timestamps)
    if not isinstance(pos_matrix, np.ndarray):
        pos_matrix = np.array(pos_matrix)
    if vel_matrix and not isinstance(vel_matrix, np.ndarray):
        vel_matrix = np.array(vel_matrix)

    # Helper for making the legend
    flatten = lambda l: [item for sublist in l for item in sublist]

    # Create spline to smooth path
    pos_spline = None
    vel_spline = None
    pos_splines = []
    vel_splines = []
    for i, m in enumerate(motors):
        pos_spline_obj = UnivariateSpline(timestamps, pos_matrix[:,i])
        pos_spline = pos_spline_obj(timestamps)
        pos_spline = pos_spline.reshape(pos_spline.shape[0], 1)
        pos_splines.append(pos_spline)

        # If no measured velocities
        if len(vel_matrix) == 0 or not vel_matrix.any():
            # Ensure the spline of velocity is being used
            use_vel_spl = True

            # Use the position spline to generate velocity curve
            vel_spline_obj = pos_spline_obj.derivative()
            vel_spline = vel_spline_obj(timestamps)
            vel_spline = vel_spline.reshape(vel_spline.shape[0], 1)

            # Make all velocities positive
            np.place(vel_spline, vel_spline < 0.0, abs(vel_spline))

            vel_splines.append(vel_spline)
        else:
            vel_spline_obj = UnivariateSpline(timestamps, vel_matrix[:,i])
            vel_spline = vel_spline_obj(timestamps)
            vel_spline = vel_spline.reshape(vel_spline.shape[0], 1)
            vel_splines.append(vel_spline)

        # Plot if axes are provided
        if pos_ax:
            pos_ax.plot(timestamps, pos_matrix[:,i])
            pos_ax.plot(timestamps, pos_spline)

        if vel_ax:
            # Only plot this if there are velocities provided
            if not (len(vel_matrix) == 0 or not vel_matrix.any()):
                vel_ax.plot(timestamps, vel_matrix[:,i])
            vel_ax.plot(timestamps, vel_spline)

    # Make plots if needed
    if pos_ax:
        pos_ax.legend(flatten([["OG_" + str(m), "SPL_" + str(m)] for m in motors]))
        pos_ax.set_xlabel('Time (in s)')
        pos_ax.set_ylabel('Position (in degrees)')

    if vel_ax:
        vel_ax.legend(flatten([["OG_" + str(m), "SPL_" + str(m)] for m in motors]))
        vel_ax.set_xlabel('Time (in s)')
        vel_ax.set_ylabel('Velocity (in degrees/sec)')

    # Use splines if set
    if use_pos_spl:
        pos_matrix = np.concatenate(tuple(pos_splines), axis=1)
    if use_vel_spl:
        vel_matrix = np.concatenate(tuple(vel_splines), axis=1)

    # Start the gesture at the initial position it read
    moves = []
    for i, m in enumerate(motors):
        move = Move(shimi, m, pos_matrix[0, i], 1.0, normalized_positions=False)
        moves.append(move)

    # Start all the moves
    for move in moves:
        move.start()

    # Wait for all the moves to finish
    for move in moves:
        move.join()

    # Make sure no speeds are 0.0 (which means move-as-fast-as-possible)
    # Set to 1.0 degree per second, which is very slow, but won't cause jerkiness
    #   due to changing the goal position when velocity is 0.0
    np.place(vel_matrix, vel_matrix < 1.0, 1.0)

    # Find the positions at which direction change happens, interpolated to INTERP_FREQ [s] increments
    times_positions = [[[], []] for _ in motors]
    for i, _ in enumerate(motors):
        zero_pos = np.interp(0, timestamps, pos_matrix[:, i])
        first_pos = np.interp(INTERP_FREQ, timestamps, pos_matrix[:, i])
        if first_pos - zero_pos < 0:
            increasing = False
        else:
            increasing = True

        t = 2 * INTERP_FREQ
        last_pos = first_pos
        while t < duration:
            pos = np.interp(t, timestamps, pos_matrix[:, i])
            if increasing and last_pos - pos < 0.009:
                times_positions[i][TIME_INDEX].append(t)
                times_positions[i][POS_INDEX].append(last_pos)
                increasing = not increasing
            if not increasing and last_pos - pos > 0.009:
                times_positions[i][TIME_INDEX].append(t)
                times_positions[i][POS_INDEX].append(last_pos)
                increasing = not increasing
            last_pos = pos

            t += INTERP_FREQ

    # Add initial time (which should correspond to the first position change)
    # Add final position (which should correspond to the last position change time)
    for i, _ in enumerate(motors):
        times_positions[i][TIME_INDEX].insert(0, 0.0)
        times_positions[i][POS_INDEX].append(pos_matrix[-1, i])

    # Use callback to alert start of playback
    if callback is not None:
        print("Starting motion, calling back...")
        callback()

    # Using the times and positions, and the captured speeds, set goal position on change and update speed
    t = 0
    while t <= duration:
        # Measure the time it takes for updating in order to make the sleep time such that update occurs
        #   as close to INTERP_FREQ as possible
        compute_time = time.time()

        # Queues for setting multiple values at the same time
        motor_pos_to_set = []
        pos_to_set = []
        motor_vel_to_set = []
        vel_to_set = []

        for i, m in enumerate(motors):
            # Set a new goal pos if needed
            if len(times_positions[i][TIME_INDEX]) > 0 and abs(times_positions[i][TIME_INDEX][0] - t) <= ERROR:
                # Note which motor needs to be moved
                motor_pos_to_set.append(m)

                # Add position to set queue
                pos_to_set.append(times_positions[i][POS_INDEX].pop(0))

                # Remove this position change time
                times_positions[i][TIME_INDEX].pop(0)

            # Calculate velocity at this point
            motor_vel_to_set.append(m)
            vel_to_set.append(np.interp(t, timestamps, vel_matrix[:, i]))

        # Set speeds for all motors
        shimi.controller.set_moving_speed(dict(zip(motor_vel_to_set, vel_to_set)))

        # Set new goal positions for those that need it
        if len(motor_pos_to_set) > 0:
            # print("Setting positions {}".format(dict(zip(motor_pos_to_set, pos_to_set))))
            shimi.controller.set_goal_position(dict(zip(motor_pos_to_set, pos_to_set)))

        # Sleep for INTERP_FREQ [s] minus compute time
        if INTERP_FREQ - (time.time() - compute_time) > 0:
            time.sleep(INTERP_FREQ - (time.time() - compute_time))
        else:
            print("Didn't sleep.")
        t += INTERP_FREQ
