import os
import json
from PIL import Image
import time
from camera_util.realsense import RealSenseCamera
from LLaVAController import LLAVAController
from robot_util.RobotController import RobotController


def log_data(log_file, data):
    """Append data to a log file in JSON format."""
    with open(log_file, 'a') as f:
        json.dump(data, f)
        f.write('\n') 


def main():
    Generator = LLAVAController("http://localhost:10000", "llava-ftmodel-Gen")
    Expert = LLAVAController("http://localhost:10000", "llava-ftmodel-Exp")
    robot = RobotController("192.168.56.6", 30003)
    camera = RealSenseCamera(save_path='./LLM_execution/', exposure=100)
    log_file = 'robot_execution_log.json'

    # Action history queues
    move_holder = []

    move_count = 1  # Start counting from 1
    for i in range(100):  # Loop 100 times
        print(f'Loop {i} times')
        loop_dir = f'./LLM_execution/Loop_{i}'
        os.makedirs(loop_dir, exist_ok=True)
        camera.save_path = loop_dir
        robot.go_rand_init()
        try:
            while True:  
                image_rt = f'move_{move_count}.jpg'
                camera.capture_image(image_rt)
                image_path = os.path.join(loop_dir, image_rt)
                image = Image.open(image_path)
                time.sleep(1)
                execute = Generator.send_request_G(image)

                print("Assistant's Message:", execute)
                if execute is None:
                    print("Failed to get a valid response, retrying...")
                    continue  

                command_to_execute = robot.interpret_instruction(execute)

                move_holder.append(command_to_execute)
                print('holder', command_to_execute)
                if len(move_holder) > 10:
                    move_holder.pop(0)  # Keep the queue size to 10

                # Execute the determined majority action
                command_executed = robot.move_based_on_instruction(command_to_execute)

                log_data(log_file, {
                    'move_count': move_count,
                    'image_path': image_path,
                    'assistant_message': execute,
                    'command_executed': command_executed
                })

                # Perform evaluation every 10 steps
                if move_count % 10 == 0:
                    # Compare current image with the image from 10 moves ago
                    image_path_past = f'./LLM_execution/move_{max(1, move_count-10)}.jpg' 
                    image_past = Image.open(image_path_past)
                    eva = Expert.send_request_G(image_past, image)
                    robot.correct(eva, move_holder)  

                    move_count += 1

                if command_executed == 'done':
                    print("Process completed.")
                    break  # Exit the loop if 'done' command is executed

        except KeyboardInterrupt:
            print("Stopping the process.")
        except Exception as e:
            Generator.logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
