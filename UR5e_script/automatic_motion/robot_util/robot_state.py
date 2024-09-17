# -*- encoding:utf-8 -*-
from UR_tasks import URTasks as URT



def main():
    robot = URT(ip="192.168.56.6", port=30003)
    robot.get_joint_states()
    robot.get_tcp()


if __name__ == '__main__':
    main()
