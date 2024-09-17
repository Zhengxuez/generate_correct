# UR_Commands.py

import socket
import numpy as np
import util
from time import sleep
import struct
from rtde_control import RTDEControlInterface
from rtde_io import RTDEIOInterface


class URfunctions:
    def __init__(self, ip="192.168.56.6", port=30003):
        self.target_ip = (ip, port)
        self.sk = socket.socket()
        print('Connected to robot')
        self.rtde_io = RTDEIOInterface(ip)

        self.home_joint_config = [0, -(90 / 360.0) * 2 * np.pi, 0, -(90 / 360.0) * 2 * np.pi, 0, 0.0]

    def send_script(self, script_path):
        with open(script_path, 'r') as file:
            script = file.read()
            self.sk.send(script.encode('utf-8'))
        print(f"Script {script_path} sent.")

    def reconnect_socket(self):
        self.sk = socket.socket()  # Recreate the socket object
        self.sk.connect(self.target_ip)  # Reconnect to the robot

    def close_connection(self):
        self.sk.close()

    def get_current_joint_positions(self):
        self.reconnect_socket()
        state_data = self.sk.recv(1500)
        actual_joint_positions = self.parse_tcp_state_data(state_data, 'joint_data')
        self.close_connection()
        return np.asarray(actual_joint_positions)

    def get_current_tcp(self):
        self.reconnect_socket()
        state_data = self.sk.recv(1500)
        actual_tool_positions = self.parse_tcp_state_data(state_data, 'cartesian_info')
        self.close_connection()
        return np.asarray(actual_tool_positions)

    def move_joint_list(self, q, v = 0.5, a = 0.2, r = 0.05):
        """
        move the arm according joint state
        :param q: joint state list
        :param v: vel
        :param a: acc
        :param r: blend radius
        """
        self.reconnect_socket()
        joint_positions = ','.join([f"{pos}" for pos in q])
        tcp_command = f"def process():\n"
        tcp_command += f"  movej([{joint_positions}], a={a}, v={v}, a={r})\n"
        tcp_command += "end\n"
        self.sk.send(str.encode(tcp_command))
        self.wait_for_target_joints(q)
        self.close_connection()

    def wait_for_target_joints(self, target_joints, tol=0.01):
        actual_joints = self.get_current_joint_positions()
        while not all(np.abs(actual_joints - np.array(target_joints)) < tol):
            sleep(0.1)
            actual_joints = self.get_current_joint_positions()

    def move_joint_enum(self, q1, q2, q3, q4, q5, q6, a, v):
        """
        move the arm according joint state
        :param q1 q2 q3 q4 q5 q6: each joint state
        :param a: acc
        :param v: vel
        """
        self.reconnect_socket()
        data = "def test():\n movej(["
        data += str(q1)
        data += ","
        data += str(q2)
        data += ","
        data += str(q3)
        data += ","
        data += str(q4)
        data += ","
        data += str(q5)
        data += ","
        data += str(q6)
        data += "],a="
        data += str(a)
        data += ",v="
        data += str(v)
        data += ")\nend\n"
        print(data)
        self.sk.send(data.encode('utf-8'))


    def speedj_list(self, qd, a, t):
        """
        control 6 joint vel
        :param qd: target vel list
        :param a: acc
        :param t: duration time
        """
        data = "def test():\n speedj(["
        for i in range(len(qd) - 1):
            data += str(qd[i])
            data += ","
        data += str(qd[5])
        data += "],a="
        data += str(a)
        data += ",t="
        data += str(t)
        data += ")\nend\n"
        self.sk.send(data.encode('utf-8'))


    def speedj_enum(self, qd1, qd2, qd3, qd4, qd5, qd6, a, t):
        """
        control 6 joint vel
        :param qd1 ~ qd6: each joint vel
        :param a: acc
        :param t: duration time
        """
        data = "def test():\n speedj(["
        data += str(qd1)
        data += ","
        data += str(qd2)
        data += ","
        data += str(qd3)
        data += ","
        data += str(qd4)
        data += ","
        data += str(qd5)
        data += ","
        data += str(qd6)
        data += "],a="
        data += str(a)
        data += ",t="
        data += str(t)
        data += ")\nend\n"
        print(data)
        self.sk.send(data.encode('utf-8'))


    def movel_tcp(self, target_tcp, vel = 0.5, acc = 0.2):
        self.reconnect_socket()
        tool_acc = acc  # Safe: 0.5
        tool_vel = vel  # Safe: 0.2
        tcp_command = "movel(p[%f,%f,%f,%f,%f,%f],a=%f,v=%f,t=0,r=0)\n" % (
            target_tcp[0], target_tcp[1], target_tcp[2], target_tcp[3], target_tcp[4],
            target_tcp[5], tool_acc, tool_vel)
        self.sk.send(str.encode(tcp_command))
        self.wait_for_target_position(target_tcp)
        self.close_connection()

    def movej_tcp(self, target_tcp, vel, acc):
        self.reconnect_socket()
        tool_acc = acc  # Safe: 0.5
        tool_vel = vel  # Safe: 0.2
        tcp_command = "movej(p[%f,%f,%f,%f,%f,%f],a=%f,v=%f,t=0,r=0)\n" % (
            target_tcp[0], target_tcp[1], target_tcp[2], target_tcp[3], target_tcp[4],
            target_tcp[5], tool_acc, tool_vel)
        self.sk.send(str.encode(tcp_command))
        self.wait_for_target_position(target_tcp)

        self.close_connection()

    def wait_for_target_position(self, target_tcp, tol=[0.001, 0.001, 0.001, 0.05, 0.05, 0.05]):
        actual_tcp = self.get_current_tcp()
        target_rpy = util.rv2rpy(target_tcp[3], target_tcp[4], target_tcp[5])
        actual_rpy = util.rv2rpy(actual_tcp[3], actual_tcp[4], actual_tcp[5])

        while not (all(np.abs(actual_tcp[:3] - target_tcp[:3]) < tol[:3]) and
                   all(np.abs(actual_rpy - target_rpy) < tol[3:])):
            sleep(0.1)
            actual_tcp = self.get_current_tcp()
            actual_rpy = util.rv2rpy(actual_tcp[3], actual_tcp[4], actual_tcp[5])

    def relative_move(self, delta_x, delta_y, delta_z, delta_theta_x, delta_theta_y, delta_theta_z, vel, acc):
        """
        Move the end effector relative to its current position and orientation.
        """
        self.reconnect_socket()
        current_tcp = self.get_current_tcp()
        rpy = util.rv2rpy(current_tcp[3], current_tcp[4], current_tcp[5])
        rpy[0] += delta_theta_x  # Adjust roll (rotation around x-axis)
        rpy[1] += delta_theta_y  # Adjust pich (rotation around y-axis)
        rpy[2] += delta_theta_z  # Adjust yaw (rotation around Z-axis)
        target_rv = util.rpy2rv(rpy)
        target_tcp = np.array([
            current_tcp[0] + delta_x,
            current_tcp[1] + delta_y,
            current_tcp[2] + delta_z,
            target_rv[0], target_rv[1], target_rv[2]
        ])
        self.movel_tcp(target_tcp,vel, acc)
        self.close_connection()

    def get_state(self):
        self.reconnect_socket()
        state_data = self.sk.recv(1500)
        self.close_connection()
        return state_data
        
