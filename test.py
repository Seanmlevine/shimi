import pypot.dynamixel
import pypot.robot
import time

angle_limits = {
    1: (-99, 14.64),
    2: (-111.6, 68.4),
    3: (-50.4, 9.8),
    4: (-101.85, 168.15),
    5: (5.41, 21.14)
}

# def set_angle_limits(dxl_io):
#     dxl_io.set_angle_limit(angle_limits)
#
ports = pypot.dynamixel.get_available_ports()
#
# if not ports:
#     raise IOError('no port found!')
#
print('ports found', ports)

print('connecting on the first available port:', ports[0])
# dxl_io = pypot.dynamixel.DxlIO('/dev/ttyTHS2')
dxl_io = pypot.dynamixel.DxlIO(ports[0])

ids = dxl_io.scan(range(10))
print('found:', ids)

print(dxl_io.get_control_table([5]))

# shimi = pypot.robot.from_json("shimi_robot_model.json")
# shimi.start_sync()
# time.sleep(2)
#
# for m in shimi.motors:
#     m.compliant = False
#
# time.sleep(0.03)
#
# shimi.goto_position({m.name: m.angle_limit[0] + 4 for m in shimi.motors}, 2)
#
# time.sleep(3)
#
# shimi.goto_position({m.name: m.angle_limit[1] - 4 for m in shimi.motors}, 2, control='minjerk')
#
# time.sleep(3)
#
# for m in shimi.motors:
#     m.compliant = False
#     m.goal_position = m.
#
# time.sleep(2)
#
# for m in shimi.motors:
#     print(m.present_position)
#
# time.sleep(2)
#
# for m in shimi.motors:
#     m.compliant = True
#
# time.sleep(2)
#
# shimi.stop_sync()
# time.sleep(0.1)


# set_angle_limits(dxl_io)

# while True:
#     id = input("id: ")
#     id = int(id)
#     print("current pos: ", dxl_io.get_present_position([id]))
#     pos = input("pos: ")
#     pos = float(pos)
#     dxl_io.set_goal_position({
#         id: pos
#     })
#     time.sleep(0.5)
#     cont = input("continue? ")
#     if cont == 'y':
#         continue
#     else:
#         break

# f = True

# while True:
#     if f:
#         dxl_io.set_goal_position({
#             2: 21.6 - 10,
#             3: -20 - 10,
#             5: 5.5
#         })
#     else:
#         dxl_io.set_goal_position({
#             2: 21.6 + 10,
#             3: -20 + 10,
#             5: 20
#         })
#
#     f = not f
#     time.sleep(0.5)

# dxl_io.disable_torque(ids)

# starting_positions = {
#     1: 10,
#     2: 68.4 - 90,
#     3: 0,
#     4: -11.85,
#     5: 5.41
# }

#     time.sleep(4)
#     # id 1: torso, -99 down, 14.64 up
#     # id 2: neck LR -111.6 left, 68.4 right
#     # id 3: neck UD 9.8 down, -50.4 up
#     # id 4: phone, -101.85 left, 78.15 right, -11.85 out, 168.15 away
#     # id 5: foot, 5.41 down, 21.14 up