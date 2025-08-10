# Copyright (c) 2025 SparkAudio
#               2025 Xinsheng Wang (w.xinshawn@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#this code is mainly borrowed from Spark TTS ,using  their license
#created by xiewoc

import os
import sys
import torch
import soundfile as sf
import logging
import platform
from pydub import AudioSegment
from typing import Optional

logging.getLogger("pydub").setLevel(logging.WARNING) #忽略pydb的info输出

sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts"))

sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts","cli"))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts","cli"))

from SparkTTS import SparkTTS

def wav2mp3(wav_path,script_path):
    audio = AudioSegment.from_wav(wav_path)
    audio.export(os.path.join(script_path, "output.mp3"), format="mp3", parameters=["-loglevel", "quiet"])
    os.remove(wav_path)
    mp3_path = os.path.join(script_path, "output.mp3")
    return mp3_path

def initialize_model(model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Spark-TTS-0.5B"), device = 0):
    """Load the model once at the beginning."""
    logging.info(f"Loading model from: {model_dir}")

    # Determine appropriate device based on platform and availability
    if platform.system() == "Darwin":
        # macOS with MPS support (Apple Silicon)
        device = torch.device(f"mps:{device}")
        logging.info(f"Using MPS device: {device}")
    elif torch.cuda.is_available():
        # System with CUDA support
        device = torch.device(f"cuda:{device}")
        logging.info(f"Using CUDA device: {device}")
    else:
        # Fall back to CPU
        device = torch.device("cpu")
        logging.info("GPU acceleration not available, using CPU")

    model = SparkTTS(model_dir, device)
    return model

"""
LEVELS_MAP_UI = {
    1: 'very_low',
    2: 'low',
    3: 'moderate',
    4: 'high',
    5: 'very_high'
}
"""

async def run_tts(
    text,                                               #the text to be generated
    model,                                              #load in 'model = initialize_model(model_dir, device=0)'
    prompt_text = None,                                 #the text in the uploaded wav file 
    prompt_speech = None,                               #the input wav file
    gender = None,                                      #gender of the speaker
    pitch = None,                                       #pitch rta 声调
    speed = None,                                       #the speed of the generated speech 
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"results"),
):
    """Perform TTS inference and save the generated audio."""
    logging.info(f"Saving audio to: {save_dir}")

    if prompt_text is not None:
        prompt_text = None if len(prompt_text) <= 1 else prompt_text

    # Use abspath (relative path -> absolute path)
    if prompt_speech != None:
        prompt_speech = os.path.join(os.path.dirname(os.path.abspath(__file__)),prompt_speech)
    else:
        pass

    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)

    save_path = os.path.join(save_dir, "output.wav")

    logging.info("Starting inference...")

    # Perform inference and save the output audio
    with torch.no_grad():
        wav = model.inference(
            text,                   
            prompt_speech,          
            prompt_text,            
            gender,                 
            pitch,                  
            speed,
            #temperature: float = 0.8,
            #top_k: float = 50,
            #top_p: float = 0.95,                  
        )

        sf.write(save_path, wav, samplerate=16000)

    logging.info(f"Audio saved at: {save_path}")

    return save_path