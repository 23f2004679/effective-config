import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import yaml

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ENV_FILE = dotenv_values(".env")

ENV_CONFIG = {}

for key, value in ENV_FILE.items():
    if key.startswith("APP_"):
        config_key = key[4:].lower()
        ENV_CONFIG[config_key] = value

if "NUM_WORKERS" in ENV_FILE:
    ENV_CONFIG["workers"] = ENV_FILE["NUM_WORKERS"]

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

with open("config.development.yaml", "r") as f:
    YAML_CONFIG = yaml.safe_load(f) or {}

OS_ENV = {}

for key, value in os.environ.items():
    if key.startswith("APP_"):
        config_key = key[4:].lower()
        OS_ENV[config_key] = value

def convert_value(key, value):
    if value is None:
        return value

    if key in ["port", "workers"]:
        return int(value)

    if key == "debug":
        return str(value).strip().lower() in {"true", "1", "yes", "on"}

    return value

def get_config():
    config = DEFAULTS.copy()

    config.update(YAML_CONFIG)
    config.update(ENV_CONFIG)
    config.update(OS_ENV)

    for key in config:
        config[key] = convert_value(key, config[key])

    return config

def apply_overrides(config, request):
    for item in request.query_params.getlist("set"):
        if "=" not in item:
            continue

        key, value = item.split("=", 1)
        config[key] = convert_value(key, value)

    return config

@app.get("/effective-config")
def effective_config(request: Request):
    config = get_config()
    config = apply_overrides(config, request)

    if "api_key" in config:
        config["api_key"] = "*****"

    return config