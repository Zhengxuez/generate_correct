import requests
import datetime
import os
import json
import hashlib
import time
import gradio as gr
from LLaVA.llava.constants import LOGDIR
from LLaVA.llava.conversation import default_conversation, conv_templates, SeparatorStyle
from LLaVA.llava.utils import build_logger, server_error_msg



class LLAVAController:
    def __init__(self, controller_url, model_name):
        self.controller_url = controller_url
        self.model_name = model_name
        self.worker_url = self.get_worker_address()
        self.headers = {"User-Agent": "LLaVA Client"}

        # Default parameters for the conversation and model interaction
        self.state = default_conversation.copy()
        self.temperature = 0.7
        self.top_p = 0.9
        self.max_new_tokens = 500
        self.text_Gen = "Which direction to move the peg to align with the hole?"
        self.text_Expert = "Is peg closer to the hole?"
        self.image_process_mode = "Default"
        self.logger = build_logger("gradio_web_server", "gradio_web_server.log")
    def get_worker_address(self):
        """Fetch the worker address for a specific model from the controller."""
        payload = {"model": self.model_name}
        response = requests.post(f"{self.controller_url}/get_worker_address", json=payload)
        if response.status_code != 200 or 'address' not in response.json():
            self.logger.error("Failed to fetch worker address or bad response")
            return None
        
    def get_conv_log_filename(self):
        t = datetime.datetime.now()
        name = os.path.join(LOGDIR, f"{t.year}-{t.month:02d}-{t.day:02d}-conv.json")
        return name

    def send_request_G(self, imagebox):
        request = self.worker_url
        text_Gen = "Which direction to move the peg to align with the hole?"
        state = self.add_text(self.state, text_Gen, imagebox, self.image_process_mode, request)
        start_tstamp = time.time()
        model_name = self.model_name

        if len(state.messages) == state.offset + 2:
            # First round of conversation
            if "llava" in model_name.lower():
                if 'llama-2' in model_name.lower():
                    template_name = "llava_llama_2"
                elif "mistral" in model_name.lower() or "mixtral" in model_name.lower():
                    if 'orca' in model_name.lower():
                        template_name = "mistral_orca"
                    elif 'hermes' in model_name.lower():
                        template_name = "chatml_direct"
                    else:
                        template_name = "mistral_instruct"
                elif 'llava-v1.6-34b' in model_name.lower():
                    template_name = "chatml_direct"
                elif "v1" in model_name.lower():
                    if 'mmtag' in model_name.lower():
                        template_name = "v1_mmtag"
                    elif 'plain' in model_name.lower() and 'finetune' not in model_name.lower():
                        template_name = "v1_mmtag"
                    else:
                        template_name = "llava_v1"
                elif "mpt" in model_name.lower():
                    template_name = "mpt"
                else:
                    if 'mmtag' in model_name.lower():
                        template_name = "v0_mmtag"
                    elif 'plain' in model_name.lower() and 'finetune' not in model_name.lower():
                        template_name = "v0_mmtag"
                    else:
                        template_name = "llava_v0"
            elif "mpt" in model_name:
                template_name = "mpt_text"
            elif "llama-2" in model_name:
                template_name = "llama_2"
            else:
                template_name = "vicuna_v1"

            new_state = conv_templates[template_name].copy()
            new_state.append_message(new_state.roles[0], state.messages[-2][1])
            new_state.append_message(new_state.roles[1], None)
            state = new_state

        try:
            controller_url = self.controller_url
            response = requests.post(controller_url + "/get_worker_address", json={"model": self.model_name})
            if response.status_code == 200:
                worker_addr = response.json().get('address')
                if worker_addr:
                    self.logger.info(f"model_name: {self.model_name}, worker_addr: {worker_addr}")
                    # Proceed with additional logic using worker_addr
                else:
                    raise ValueError("Worker address not found in response")
            else:
                raise Exception("Failed to fetch worker address, status code: " + str(response.status_code))
        except Exception as e:
            self.logger.error(f"An error occurred while fetching worker address: {e}")
            # Optionally return or continue based on error handling logic
            return None  # or continue
        # Construct prompt
        prompt = state.get_prompt()

        all_images = state.get_images(return_pil=True)
        all_image_hash = [hashlib.md5(image.tobytes()).hexdigest() for image in all_images]
        for image, hash in zip(all_images, all_image_hash):
            t = datetime.datetime.now()

            # the function to save images
            filename = os.path.join(LOGDIR, "serve_images", f"{t.year}-{t.month:02d}-{t.day:02d}", f"{hash}.jpg")
            if not os.path.isfile(filename):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                image.save(filename)
        
        
        # Make requests
        pload = {
            "model": model_name,
            "prompt": prompt,
            "temperature": float(self.temperature),
            "top_p": float(self.top_p),
            "max_new_tokens": min(int(self.max_new_tokens), 1536),
            "stop": state.sep if state.sep_style in [SeparatorStyle.SINGLE, SeparatorStyle.MPT] else state.sep2,
            "images": f'List of {len(state.get_images())} images: {all_image_hash}',
        }
        # logger.info(f"==== request ====\n{pload}")

        pload['images'] = state.get_images()

        state.messages[-1][-1] = "▌"

        try:
            # Stream output
            response = requests.post(worker_addr + "/worker_generate_stream",
                headers=self.headers, json=pload, stream=True, timeout=10)
            for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
                if chunk:
                    data = json.loads(chunk.decode())
                    if data["error_code"] == 0:
                        output = data["text"][len(prompt):].strip()
                        state.messages[-1][-1] = output + "▌"
                    else:
                        output = data["text"] + f" (error_code: {data['error_code']})"
                        state.messages[-1][-1] = output
                        return
                    time.sleep(0.03)
        except requests.exceptions.RequestException as e:
            state.messages[-1][-1] = server_error_msg
            return

        state.messages[-1][-1] = state.messages[-1][-1][:-1]
        ###############################
        # print('state at the end', self.extract_assistant_message(state.messages))
        assistant_msg = self.extract_assistant_message(state.messages)
        # print('type(assistant_msg):',type(assistant_msg))
        ###############################

        finish_tstamp = time.time()
        # logger.info(f"{output}")

        with open(self.get_conv_log_filename(), "a") as fout:
            data = {
                "tstamp": round(finish_tstamp, 4),
                "type": "chat",
                "model": model_name,
                "start": round(start_tstamp, 4),
                "finish": round(finish_tstamp, 4),
                "state": state.dict(),
                "images": all_image_hash,
            }
            fout.write(json.dumps(data) + "\n")

            return assistant_msg

    def send_request_E(self, imagebox1, imagebox2):
        request = self.worker_url
        text_Eval = "Is the peg closer to the hole?"
        # Initialize conversation state for two images
        state = self.add_text(self.state, text_Eval, imagebox1, imagebox2, self.image_process_mode, request)

        start_tstamp = time.time()
        model_name = self.model_name

        if len(state.messages) >= state.offset + 4:  # for two images
            template_name = "llava_v0"  

            new_state = conv_templates.get(template_name, {}).copy()
            # Append both images' last messages to the new state
            new_state.append_message(new_state.roles[0], state.messages[-4][1])
            new_state.append_message(new_state.roles[1], "")
            new_state.append_message(new_state.roles[0], state.messages[-2][1])
            new_state.append_message(new_state.roles[1], "")
            state = new_state

        # Handle fetching worker address and making the request as in send_request()
        try:
            controller_url = self.controller_url
            response = requests.post(controller_url + "/get_worker_address", json={"model": self.model_name})
            if response.status_code == 200:
                worker_addr = response.json().get('address')
                if worker_addr:
                    self.logger.info(f"model_name: {model_name}, worker_addr: {worker_addr}")
                else:
                    raise ValueError("Worker address not found in response")
            else:
                raise Exception("Failed to fetch worker address, status code: " + str(response.status_code))
        except Exception as e:
            self.logger.error(f"An error occurred while fetching worker address: {e}")
            return None

        prompt = state.get_prompt()
        all_images = state.get_images(return_pil=True)
        all_image_hash = [hashlib.md5(image.tobytes()).hexdigest() for image in all_images]

        for image, hash in zip(all_images, all_image_hash):
            t = datetime.datetime.now()
            filename = os.path.join(LOGDIR, "serve_images", f"{t.year}-{t.month:02d}-{t.day:02d}", f"{hash}.jpg")
            if not os.path.isfile(filename):
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                image.save(filename)

        pload = {
            "model": model_name,
            "prompt": prompt,
            "temperature": float(self.temperature),
            "top_p": float(self.top_p),
            "max_new_tokens": min(int(self.max_new_tokens), 1536),
            "stop": state.sep if state.sep_style in [SeparatorStyle.SINGLE, SeparatorStyle.MPT] else state.sep2,
            "images": f'List of {len(all_images)} images: {all_image_hash}',
        }

        pload['images'] = state.get_images()

        state.messages[-1][-1] = "▌"
        try:
            response = requests.post(worker_addr + "/worker_generate_stream",
                                    headers=self.headers, json=pload, stream=True, timeout=10)
            for chunk in response.iter_lines(decode_unicode=False, delimiter=b"\0"):
                if chunk:
                    data = json.loads(chunk.decode())
                    if data["error_code"] == 0:
                        output = data["text"][len(prompt):].strip()
                        state.messages[-1][-1] = output + "▌"
                    else:
                        output = data["text"] + f" (error_code: {data['error_code']})"
                        state.messages[-1][-1] = output
                        return
                    time.sleep(0.03)
        except requests.exceptions.RequestException as e:
            state.messages[-1][-1] = server_error_msg
            return None

        state.messages[-1][-1] = state.messages[-1][-1][:-1]
        finish_tstamp = time.time()

        with open(self.get_conv_log_filename(), "a") as fout:
            data = {
                "tstamp": round(finish_tstamp, 4),
                "type": "chat",
                "model": model_name,
                "start": round(start_tstamp, 4),
                "finish": round(finish_tstamp, 4),
                "state": state.dict(),
                "images": all_image_hash,
            }
            fout.write(json.dumps(data) + "\n")

        return self.extract_assistant_message(state.messages)

    def add_text(self, state, text, image, image_process_mode, request: gr.Request):
        # logger.info(f"add_text. ip: {request.client.host}. len: {len(text)}")

        text = text[:1536]  # Hard cut-off
        if image is not None:
            text = text[:1200]  # Hard cut-off for images
            if '<image>' not in text:
                # text = '<Image><image></Image>' + text
                text = text + '\n<image>'
            text = (text, image, image_process_mode)
            state = default_conversation.copy()
        state.append_message(state.roles[0], text)
        state.append_message(state.roles[1], None)
        state.skip_next = False
        # print('state under add text', state.messages)
        # print('state under add text', len(state.messages))
        return state

    def add_text_2(self, state, text, imagebox1, imagebox2, image_process_mode, request: gr.Request):

        text = "Is the peg closer to the hole?\n<image_1>\n<image_2>"[:1200]  # Apply hard cut-off
        text = text.replace("<image_1>", "").replace("<image_2>", "")  # Remove placeholders for initial text setting
        state = default_conversation.copy()

        if imagebox1 is not None and imagebox2 is not None:
            text_with_images = (f"{text}\n<image_1>\n<image_2>", imagebox1, imagebox2, image_process_mode)
            state.append_message(state.roles[0], text_with_images)
            state.append_message(state.roles[1], None)  # Prepare for the response
        else:
            print("Both images must be provided.")
            return None  # Ensure both images are present to proceed

        state.skip_next = False

        return state

    def extract_assistant_message(self, state_messages):
        # This function will return the first message where the role is 'Assistant'
        for role, content in state_messages:
            if role == 'Assistant' and isinstance(content, str):  # Ensure it's a string response
                return content
        return "No assistant response found."  # Fallback in case there's no such message

