# GenCo: A Dual LVLM Generate-Correct Framework for Adaptive Peg-in-Hole Robotics

This repository is developed for the GenCo Framework, which integrates LVLM-based Motion Generator and Motion Expert. Both the Generator and Expert are fine-tuned using the pre-trained LLaVA, enhancing their adaptability and scaling efficiently to diverse tasks.

## How to Use

### Clone the Repository

1. Clone the repository to a local path:
2. Clone the LLaVA repository into the `UR5e_script/automatic_motion` folder:

git clone https://github.com/haotian-liu/LLaVA.git
- Follow the installation steps in the LLaVA repository to install the necessary requirements.

3. Clone the Motion Generator and the Motion Expert:
   git clone https://huggingface.co/Zhengxue/llava-ftmodel-Gen
   git clone https://huggingface.co/Zhengxue/llava-ftmodel-Exp

### Launch the Services

4. Launch the controller:
  ```
  python -m llava.serve.controller --host 0.0.0.0 --port 10000
  ```
5. Launch the model workers for the Motion Generator and the Motion Expert:
- For the Motion Generator:
  ```
  python -m llava.serve.model_worker --host 0.0.0.0 --controller http://localhost:10000 --port 40000 --worker http://localhost:40000 --model-path llava_ftmodel_Gen
  ```
- For the Motion Expert:
  ```
  python -m llava.serve.model_worker --host 0.0.0.0 --controller http://localhost:10000 --port 40001 --worker http://localhost:40001 --model-path llava_ftmodel_Exp
  ```

### Run the Interaction Script

6. Set up the robot IP address and run the interaction script:
  ```
  python interact_llm_robot.py
  ```
