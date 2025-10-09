from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
import os

app = FastAPI()
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
env = Environment(loader=FileSystemLoader("templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return env.get_template("index.html").render()

@app.get("/api/ping")
def ping():
    return {"ok": True}
