from __future__ import division
import platform
import logging
import subprocess

import pypot.primitive

logger = logging.getLogger(__name__)

class LimitTorque(pypot.primitive.LoopPrimitive):
    def __init__(self, robot, freq=20, max_error=10., torque_min=20., torque_max=95.):
        pypot.primitive.LoopPrimitive.__init__(self, robot, freq)

        self._max_error = max_error
        self.torque_min = torque_min
        self.torque_max = torque_max

    def setup(self):
        self.initial_torque_limit = []

        # Using a dictionnary may be a better solution so we can easily retrieve the initial torque value.
        for m in self.robot.motors:
            self.initial_torque_limit.append(m.torque_limit)

        self.active_motors = self.robot.motors

    def update(self):
        for m in self.active_motors:
            self.adjust_torque(m)

    def adjust_torque(self, motor):
        target = motor.goal_position
        pos = motor.present_position
        dist = abs(target - pos)

        if dist > self._max_error:
            motor.torque_limit = self.torque_max
        else:
            motor.torque_limit = self.torque_min + dist / self._max_error * (self.torque_max - self.torque_min)

    def teardown(self):
        for i, m in enumerate(self.robot.motors):
            m.torque_limit = self.initial_torque_limit[i]

    @property
    def change_watched_motors(self):
        return self.active_motors

    @change_watched_motors.setter
    def change_watched_motors(self, watched_motors):
        self.active_motors = map(self.get_mockup_motor, watched_motors)

    @property
    def max_error(self):
        return self._max_error

    @max_error.setter
    def max_error(self, new_error):
        if new_error <= 0:
            raise ValueError('The max_error parameter must be strictly positive!')
        self._max_error = float(new_error)


class TemperatureMonitor(pypot.primitive.LoopPrimitive):
    '''
        This primitive raises an alert when the temperature
        of one motor reaches the "temp_limit".
        '''
    def __init__(self, robot, freq=0.5, temp_limit=55):
        pypot.primitive.LoopPrimitive.__init__(self, robot, freq)

        self.temp_limit = temp_limit
        self.watched_motors = self.robot.motors

    def setup(self):
        pass

    def update(self):
        self.check_temperature()

    def teardown(self):
        pass

    def check_temperature(self):
        motor_list = []

        for m in self.watched_motors:
            if m.present_temperature > self.temp_limit:
                motor_list.append(m)

        if len(motor_list) > 0:
            self.raise_problem(motor_list)

    def raise_problem(self, motor_list):
        for m in motor_list:
            print('{} overheating: {}'.format(m.name, m.present_temperature))
