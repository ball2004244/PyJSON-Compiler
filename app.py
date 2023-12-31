from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import CodeRequest, CLIRequest
from code_runner import run_python_code, run_command
from code_translator import Translator
from typing import Dict
from utils import create_path
from config import dumped_config, RESPONSE_TEMPLATE

'''
This file is the main file for the API.
It defines CORS policy and all the endpoints.
'''
app = FastAPI()

# Allow CORS from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "PUT", "POST", "DELETE"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "This is the root of the API."}


@app.get("/config")
async def get_config() -> Dict[str, str]:
    response = {
        "status": "success",
        "config": dumped_config
    }
    return response


@app.post("/pyjson")
async def running_code(code_req: CodeRequest) -> Dict[str, str]:
    # get code from request
    filename = code_req.filename if code_req.filename else 'code.py'
    json_code = code_req.code
    working_dir = 'temp'
    path = f'{working_dir}/{filename}'

    translator = Translator(json_code)
    code = translator.convert()

    response = RESPONSE_TEMPLATE.copy()

    if code[0] == 'error':
        response['status'] = 'error'
        response['stderr'] = code[1]
        return response

    # create file
    create_path(path=path, content=code[1], overwrite=True)

    # run code
    output = run_python_code(path)

    if output[1]:
        response['status'] = 'error'
        response['stderr'] = output[1]
        return response

    response['stdout'] = output[0]
    return response


@app.post("/cli")
def running_cli(cli_req: CLIRequest) -> Dict[str, str]:
    command = cli_req.command
    response = RESPONSE_TEMPLATE.copy()

    # only allow commands to run in temp directory
    working_dir = 'temp'
    output = run_command(command, working_dir)

    if output[1]:
        response['status'] = 'error'
        response['stderr'] = output[1]
        return response

    response['stdout'] = output[0]
    return response
