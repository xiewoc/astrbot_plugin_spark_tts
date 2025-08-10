#有关tts的详细配置请移步service.py
from astrbot.api.event import filter
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import *
from multiprocessing import Process
from astrbot.api import logger
from typing import Optional
import subprocess
import aiohttp
import asyncio
import atexit
import glob
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def post_with_session_auth(
    server_ip: str,
    port: str,
    if_remove_think_tag: bool,
    prompt_text: str,
    prompt_speech: str,
    gender: str,
    pitch: str,
    speed: str,
    if_preload: bool,
    api_key: str,
    timeout_seconds: Optional[float] = 60.0  # 默认60秒超时
):
    """
    发送带认证的POST请求到指定服务器
    
    Args:
        server_ip: 服务器IP地址
        port: 服务器端口
        if_remove_think_tag: 是否移除思考标签
        prompt_text: 文本提示
        prompt_speech: 语音提示
        gender: 性别
        pitch: 音高
        speed: 语速
        if_preload: 是否预加载
        api_key: API密钥
        timeout: 请求超时时间(秒)
    """
    url = f"http://{server_ip}:{port}/config"
    payload = {
        "if_remove_think_tag": if_remove_think_tag,
        "prompt_text": prompt_text, 
        "prompt_speech": prompt_speech,
        "gender": gender,
        "pitch": pitch,
        "speed": speed,
        "if_preload": if_preload,
        "CORRECT_API_KEY": api_key
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 设置超时
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)
    
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()  # 如果状态码不是200-299，抛出异常
                result = await response.json()
                logger.info(f"请求成功: {result}")
                return result
                
    except asyncio.TimeoutError:
        logger.error("请求超时")
        raise
    except aiohttp.ClientError as e:
        logger.error(f"请求失败: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"发生未知错误: {str(e)}")
        raise

global on_init ,reduce_parenthesis
on_init = True
reduce_parenthesis = False
# 锁文件路径
lock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),"child_process.lock")

global server_ip
global if_remove_think_tag 

def download_model_and_repo():
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts")):#克隆仓库
        logger.info("Spark TTS Github Repo found, skipping download.")
        pass
    else:
        base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"spark_tts")
        run_command(f"git clone --recursive https://github.com/SparkAudio/Spark-TTS.git {base_dir}")
        logger.info("Downloading Spark TTS Github Repo...")
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)),"Spark-TTS-0.5B")):#下载模型
        logger.info("Spark TTS 0.5B model found, skipping download.")
        pass
    else:
        from modelscope import snapshot_download
        snapshot_download("SparkAudio/Spark-TTS-0.5B", local_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)),"Spark-TTS-0.5B"))#下载模型
        logger.info("Downloading Spark TTS 0.5B model...")

def run_command(command):#cmd line Git required!!!!
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        logger.error(f"Error: {error.decode()}")
    return output.decode()

def cleanup():
    """清理函数，用于在程序结束时删除锁文件"""
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)

def child_process_function():
    import service 
    service.run_service()

def start_child_process():
    global on_init 

    """启动子进程的函数"""
    if os.path.exists(lock_file_path):
        if on_init == True:
            cleanup()
            on_init = False
            pass
        else:
            logger.warning("Another instance of the child process is already running.")
            return None
    
    # 创建锁文件
    with open(lock_file_path, 'w') as f:
        f.write("Locked")
    
    # 注册清理函数
    atexit.register(cleanup)
    
    # 创建并启动子进程
    p = Process(
        target=child_process_function,
        args=()
        )
    p.start()
    logger.info("Sub process (service.py) started")
    return p

def terminate_child_process_on_exit(child_process):
    """注册一个函数，在主进程退出时终止子进程"""
    def cleanup_on_exit():
        if child_process and child_process.is_alive():
            child_process.terminate()
            child_process.join()  # 确保子进程已经完全终止
            logger.info("Service.py process terminated.")
        cleanup()
    atexit.register(cleanup_on_exit)

@register("astrbot_plugin_spark_tts", "xiewoc ", "使用SparkTTS对Astrbot的tts进行补充", "0.0.1", "https://github.com/xiewoc/astrbot_plugin_spark_tts")
class astrbot_plugin_tts_Cosyvoice2(Star):
    def __init__(self, context: Context,config: dict):
        super().__init__(context)

        download_model_and_repo()

        self.config = config
        sub_config_misc = self.config.get('misc', {})
        sub_config_serve = self.config.get('serve_config', {})
        #读取设置

        global reduce_parenthesis#减少‘（）’提示词
        reduce_parenthesis = self.config['if_reduce_parenthesis']
        global if_remove_think_tag
        if_remove_think_tag = self.config["if_remove_think_tag"]
        global if_preload
        if_preload =  self.config['if_preload']

        global prompt_speech
        prompt_speech = sub_config_misc.get("prompt_speech","")
        global prompt_text
        prompt_text = sub_config_misc.get("prompt_text","")
        global gender
        gender = sub_config_misc.get("gender","")
        global pitch
        pitch = sub_config_misc.get("pitch","")
        global speed
        speed = sub_config_misc.get("speed","")

        global server_ip
        server_ip = sub_config_serve.get("server_ip","")
        global if_seperate_serve
        if_seperate_serve = sub_config_serve.get("if_seperate_serve","")
        global CORRECT_API_KEY
        CORRECT_API_KEY = sub_config_serve.get("CORRECT_API_KEY","")
        
        #加载完成时
        @filter.on_astrbot_loaded()
        async def on_astrbot_loaded(self):
            global reduce_parenthesis, if_remove_think_tag, if_preload, prompt_text, prompt_speech, gender, pitch, speed
            if if_seperate_serve:#若为分布式部署
                pass
            else:
                child_process = start_child_process()
                if child_process:
                    terminate_child_process_on_exit(child_process)

            await asyncio.sleep(5)

            task = asyncio.create_task(
                post_with_session_auth(
                    server_ip,
                    "5080",
                    if_remove_think_tag,
                    prompt_text,
                    prompt_speech,
                    gender,
                    pitch,
                    speed,
                    if_preload,
                    CORRECT_API_KEY,
                    timeout_seconds=120.0
                    )
            )
            await task
