from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kokoro import KPipeline
import subprocess
import threading
import numpy as np
import os

app = FastAPI()
pipeline = KPipeline(lang_code='a')
ALSA_DEVICE = os.getenv("ALSA_DEVICE", "plughw:1,0")

_speaking = threading.Event()

class SpeakRequest(BaseModel):
    text: str
    voice: str = "af_heart"

@app.post("/speak")
def speak(req: SpeakRequest):
    if _speaking.is_set():
        raise HTTPException(status_code=429, detail="Audio busy")
    
    _speaking.set()
    try:
        audio = next(pipeline(req.text, voice=req.voice))
        pcm_int16 = (audio[2].numpy() * 32767).astype(np.int16)
        
        proc = subprocess.run(
            ["aplay", "-D", ALSA_DEVICE, "-f", "S16_LE", "-r", "24000", "-c", "1"],
            input=pcm_int16.tobytes(),
        )
        
        if proc.returncode != 0:
            raise HTTPException(status_code=500, detail="Audio playback failed")
    finally:
        _speaking.clear()
    
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "ok"}