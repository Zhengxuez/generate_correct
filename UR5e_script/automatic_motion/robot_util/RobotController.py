from robot_util.UR_tasks import URTasks as URT

class RobotController:
    def __init__(self, ip, port):
        self.robot = URT(ip=ip, port=port)
        self.step = 0.001
        self.angle = 1
        pass

    def go_rand_init(self):

        self.robot.go_home()
        self.robot.go_rand_init()


    def interpret_instruction(self, instruction):
        """Interprets the LLM instruction and returns a robot command without executing it."""
        commands = {
            'backward': 'backward',
            'right': 'right',
            'left': 'left',
            'down': 'down',
            'forward': 'forward',
            'clockwise': 'clockwise',
            'anticlockwise': 'anticlockwise',
            'done': 'done'
        }
        for command in commands.keys():
            if command in instruction:
                return command
        return None  # Return None if no known command is found


    def reverse_x(self, move_holder):
        forward_count = move_holder.count('forward')
        backward_count = move_holder.count('backward')
        if forward_count > backward_count:
            move_holder[:] = ['backward' if x == 'forward' else x for x in move_holder]
            correct_steps = move_holder.count('backward')
            for _ in range(correct_steps):
                self.robot.step_backward(self.step) 
            print(f"Corrected X direction: converted forwards to backwards, steps corrected: {correct_steps}")
        else:
            move_holder[:] = ['forward' if x == 'backward' else x for x in move_holder]
            correct_steps = move_holder.count('forward')
            for _ in range(correct_steps):
                self.robot.step_forward(self.step)  
            print(f"Corrected X direction: converted backwards to forwards, steps corrected: {correct_steps}")

    def reverse_y(self, move_holder):
        left_count = move_holder.count('left')
        right_count = move_holder.count('right')
        if left_count > right_count:
            move_holder[:] = ['right' if x == 'left' else x for x in move_holder]
            correct_steps = move_holder.count('right')
            for _ in range(correct_steps):
                self.robot.step_right(self.step)  
            print(f"Corrected Y direction: converted lefts to rights, steps corrected: {correct_steps}")
        else:
            move_holder[:] = ['left' if x == 'right' else x for x in move_holder]
            correct_steps = move_holder.count('left')
            for _ in range(correct_steps):
                self.robot.step_left(self.step) 
            print(f"Corrected Y direction: converted rights to lefts, steps corrected: {correct_steps}")

    def reverse_clockwise(self, move_holder):
        clockwise_count = move_holder.count('clockwise')
        anticlockwise_count = move_holder.count('anticlockwise')
        if clockwise_count > anticlockwise_count:
            move_holder[:] = ['anticlockwise' if x == 'clockwise' else x for x in move_holder]
            correct_steps = move_holder.count('anticlockwise')
            for _ in range(correct_steps):
                self.robot.step_anticlockwise(self.angle) 
            print(f"Corrected RZ direction: converted clockwise to anticlockwise, steps corrected: {correct_steps}")
        else:
            move_holder[:] = ['clockwise' if x == 'anticlockwise' else x for x in move_holder]
            correct_steps = move_holder.count('clockwise')
            for _ in range(correct_steps):
                self.robot.step_clockwise(self.angle) 
            print(f"Corrected RZ direction: converted anticlockwise to clockwise, steps corrected: {correct_steps}")

    def correct(self, eva, move_holder):
        # Sample eva: 'No, closer along x, closer along y, not closer along rz'
        parts = eva.split(', ')
        x_correct = parts[1].startswith('closer')
        y_correct = parts[2].startswith('closer')
        rz_correct = parts[3].startswith('closer')

        if not x_correct:
            self.reverse_x(move_holder)
        if not y_correct:
            self.reverse_y(move_holder)
        if not rz_correct:
            self.reverse_clockwise(move_holder)


    def move_based_on_instruction(self, instruction):
        # Define all possible movement commands including 'done'
        current_pose = self.robot.get_tcp() 
        z = current_pose[2] 
        commands = {
            'backward': lambda:  self.robot.step_back(self.step),
            'right': lambda: self.robot.step_right(self.step),
            'left': lambda: self.robot.step_left(self.step),
            'down': lambda: self.robot.step_down(self.step) if z > 0.12403579 else print("Skip down due to safety limits"),
            'forward': lambda: self.robot.step_forward(self.step),
            'clockwise': lambda: self.robot.step_clockwise(self.angle),
            'anticlockwise': lambda: self.robot.step_anticlockwise(self.angle),
            'done': lambda: self.robot.done()  # Adding the done command
        }
        for command, action in commands.items():
            if command in instruction:
                action()
                return command  # Return the command executed

        print(f"No actionable command found in instruction: '{instruction}'")
        return None  # No command found
