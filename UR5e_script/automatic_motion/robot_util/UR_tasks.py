# ur_tasks.py
from UR_Functions import URfunctions as URControl
import logging
import math
import random
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class URTasks:
    def __init__(self, ip, port):
        self.robot = URControl(ip=ip, port=port)

    def initialize_robot(self):
        """Initializes robot connection and prepares it for operations."""
        self.robot.reconnect_socket()
        print("Robot initialized and ready.")
        
    def get_joint_states(self):
        js = self.robot.get_current_joint_positions()
        formatted_js = ', '.join([f"{val:.8f}" for val in js]) 
        print('joint state, 'f"[{formatted_js}]")
        # print(js)
        return js

    def get_tcp(self):
        tcp = self.robot.get_current_tcp()
        formatted_tcp = ', '.join([f"{val:.8f}" for val in tcp]) 
        print('tcp pose', f"[{formatted_tcp}]")
        # print(tcp)
        return tcp

    '''
    robot manipulation taks
    '''

    ###
    def go_rand_init(self):
        tcp = self.above_hole_circle
        # [-0.56758035, -0.03142121, 0.12421664, -2.21667038, -2.22297235, -0.00275497]
        x_offset = random.randint(-5, 5)  # Random int between -40 and 40
        y_offset = random.randint(-5, 0)
        z_offset = random.randint(0, 5)    # Random int between 0 and 40
        x_offset = x_offset/1000
        y_offset = y_offset/1000
        z_offset = z_offset/1000
        
        tcp[0] += x_offset
        tcp[1] += y_offset
        tcp[2] += z_offset
        self.robot.movel_tcp(tcp, 1.2, 0.25)

    def rand_roat(self):
        angle = random.randint(-15, 15)
        js = self.get_joint_states()
        rad = angle/180 * math.pi
        js[5] += rad # rad
        logging.info("Rotate Randomlly...")
        self.robot.move_joint_list(js, 1.4, 1.05, 0.02)

    def done(self):
        tcp = self.get_tcp()
        tcp[2] -= 0.005 # m
        logging.info("Inserting...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def step_down(self,length):
        tcp = self.get_tcp()
        tcp[2] -= length # m
        logging.info("Moving down...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def step_up(self,length):
        tcp = self.get_tcp()
        tcp[2] += length # m
        logging.info("Moving up...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)    

    def step_left(self,length):
        tcp = self.get_tcp()
        tcp[1] += length # m
        logging.info("Moving left...")
        self.robot.movel_tcp(tcp, 0.5, 0.2) 

    def step_right(self,length):
        tcp = self.get_tcp()
        tcp[1] -= length # mm
        logging.info("Moving right...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def step_forward(self,length):
        tcp = self.get_tcp()
        tcp[0] -= length # mm
        logging.info("Moving forward...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def step_back(self,length):
        tcp = self.get_tcp()
        tcp[0] += length # mm
        logging.info("Moving backward...")
        self.robot.movel_tcp(tcp, 0.5, 0.2) 

    def step_clockwise(self,angle):
        js = self.get_joint_states()
        rad = angle/180 * math.pi
        js[5] += rad # rad
        logging.info("Moving clockwise...")
        self.robot.move_joint_list(js, 1.4, 1.05, 0.02)

    def step_anticlockwise(self,angle):
        js = self.get_joint_states()
        rad = angle/180 * math.pi
        js[5] -= rad # rad
        logging.info("Moving anticlockwise...")
        self.robot.move_joint_list(js, 1.4, 1.05, 0.02)
  
    def go_home(self):
        joint_state = [0.00000744, -1.57083954, 1.57082969, -1.57077511, -1.57079918, -0.00003463]
        logging.info("Moving to home position...")
        self.robot.move_joint_list(joint_state, 1.4, 1.05, 0.02)

    def move_up(self, length):
        tcp = self.get_tcp()
        tcp[2] += length # mm
        logging.info("Moving up...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def move_back(self, length):
        tcp = self.get_tcp()
        tcp[1] -= length
        logging.info("Moving back...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)

    def move_down(self, length):
        tcp = self.get_tcp()
        tcp[2] -= length
        logging.info("Moving down...")
        self.robot.movel_tcp(tcp, 0.5, 0.2)
