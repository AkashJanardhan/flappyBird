from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/time")
def read_time():
    return {"current_time": datetime.now().isoformat()}

@app.get("/")
def read_time():
    return "Home"