import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import re
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import logging
from typing import Optional

app = FastAPI()
security = HTTPBearer()

global if_remove_think_tag, prompt_text, prompt_speech,gender,pitch,speed,if_preload,if_loaded,model,CORRECT_API_KEY
if_remove_think_tag: bool = False
prompt_text: Optional[str] = None
prompt_speech = None
gender: Optional[str] = None
pitch: Optional[str] = None
speed: Optional[str] = None
if_preload = False
if_loaded = False
model = None

def remove_thinktag(text):
    if text:
        cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        return cleaned_text
    else:
        return ''
    
async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    global CORRECT_API_KEY
    if credentials.scheme != "Bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )
    if credentials.credentials != CORRECT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return credentials.credentials

class SpeechRequest(BaseModel):
    model: str
    input: str
    voice: str

class Config(BaseModel):
    if_remove_think_tag: bool = False
    prompt_text: Optional[str] = None
    prompt_speech: Optional[str] = None
    gender: Optional[str] = None
    pitch: str = "moderate"
    speed: str = "moderate"
    if_preload: bool = False
    CORRECT_API_KEY: str = ""

def run_service():
    uvicorn.run(app, host="0.0.0.0", port=5080)
    
@app.post("/audio/speech")
async def generate_speech(request: Request, speech_request: SpeechRequest, api_key: str = Depends(verify_api_key)):
    
    script_path = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Spark-TTS-0.5B")

    import tts_tofile as ts
    try:
        global if_remove_think_tag
        if if_remove_think_tag == True:
            input_text = remove_thinktag(speech_request.input)
        else:
            input_text = speech_request.input
        
        if input_text != "":
            global prompt_text, prompt_speech,gender,pitch,speed,if_preload,if_loaded,model
            if if_preload == True:
                pass
            else:
                if (if_loaded == False):
                    model = ts.initialize_model(model_dir,0)
                    if_loaded = True
                else:
                    pass
                

            logging.info("Generating sound,using args:",
                        input_text,"\n",
                        model,"\n",
                        prompt_text,"\n",
                        prompt_speech,"\n",
                        gender,"\n",
                        pitch,"\n",
                        speed,"\n",
                        api_key,"\n"
                        )
            
            wav_path = await ts.run_tts(
                input_text,
                model,
                prompt_text,
                prompt_speech,
                gender,
                pitch,
                speed,
                os.path.join(script_path, "results")
                )
            #mp3_path = ts.wav2mp3(wav_path,script_path)
        else:
            return ""

        if not wav_path or not os.path.exists(wav_path) or not os.access(wav_path, os.R_OK):
            raise HTTPException(status_code=500, detail="Failed to generate speech")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # 使用FileResponse返回生成的语音文件
    return FileResponse(path=wav_path, media_type='audio/wav', filename="output.wav")
@app.post("/config")
async def update_config(config: Config):
    global if_remove_think_tag
    if_remove_think_tag = config.if_remove_think_tag
    global prompt_text
    prompt_text = config.prompt_text
    global prompt_speech
    prompt_speech = config.prompt_speech
    global gender
    gender = config.gender
    global pitch
    pitch = config.pitch
    global speed
    speed = config.speed
    global if_preload
    if_preload = config.if_preload
    if(if_preload == True):
        if_preload = False
        model_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Spark-TTS-0.5B")
        import tts_tofile as ts
        global if_loaded
        if if_loaded == False:
            global model
            model = ts.initialize_model(model_dir,0)
            if_loaded = True
        else:
            pass
    global CORRECT_API_KEY
    CORRECT_API_KEY = config.CORRECT_API_KEY
    logging.info(
        "Configuration updated",
        extra={
            "if_remove_think_tag": if_remove_think_tag,
            "prompt_text": prompt_text,
            "prompt_speech": prompt_speech,
            "gender": gender,
            "pitch": pitch,
            "speed": speed,
            "if_preload": if_preload,
            "CORRECT_API_KEY": CORRECT_API_KEY
        }
            )
    return (f"Configuration updated successfully. \n if_remove_think_tag: {if_remove_think_tag}, \n prompt_text: {prompt_text}, \n prompt_speech: {prompt_speech}, \n CORRECT_API_KEY: {CORRECT_API_KEY}")
    
if __name__ == "__main__":
    print("This is a model ,you can't run this seperately.")