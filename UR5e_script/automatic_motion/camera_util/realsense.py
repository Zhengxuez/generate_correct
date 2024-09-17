import pyrealsense2 as rs
import numpy as np
import cv2
import os
import time

class RealSenseCamera:
    def __init__(self, width=1920, height=1080, fps=30,  save_path='./', exposure=156):
        # Configure the RealSense pipeline to stream from the D435i
        self.pipeline = rs.pipeline()
        self.config = rs.config()

        # Enable the color stream with the specified width, height, and fps
        self.config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, fps)

        # Start streaming
        self.pipeline.start(self.config)

        # Save path for captured images
        self.save_path = save_path
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)

        # Set the exposure value for the camera
        self.exposure = exposure
        self.set_exposure(self.exposure)

    def set_exposure(self, value):
        # Get the device from the pipeline profile
        profile = self.pipeline.get_active_profile()
        sensor = profile.get_device().query_sensors()[1]  # Color sensor is at index 1

        # Set exposure value
        sensor.set_option(rs.option.exposure, value)
        print(f"Exposure set to {value}")

    def capture_image(self, filename='capture.jpg'):
        try:
            # Delay to allow the camera to adjust its settings
            time.sleep(1)  # 2-second delay before capturing the image

            # Wait for a coherent pair of frames: depth and color
            frames = self.pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            # Validate that the frame is valid
            if not color_frame:
                raise Exception("Could not capture color frame.")

            # Convert image to numpy array
            color_image = np.asanyarray(color_frame.get_data())

            # Full path for saving the image
            full_path = os.path.join(self.save_path, filename)

            # Save the captured image to a file
            cv2.imwrite(full_path, color_image)
            print(f"Image captured and saved as {full_path}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def stop(self):
        # Stop streaming
        self.pipeline.stop()

if __name__ == "__main__":
    camera = RealSenseCamera(save_path='./captures', exposure=200)
    camera.capture_image('realsense_capture.jpg')
    camera.stop()