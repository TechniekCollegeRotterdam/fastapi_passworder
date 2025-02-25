import traceback
import uvicorn
import yaml
from typing import Optional

from fastapi import FastAPI

from passworder import Passworder
from random_password import get_random_salt
from pydantic import BaseModel


class EncryptRequest(BaseModel):
    salt: Optional[str] = None
    cleartext: str
    algorithm: Optional[str] = Passworder.DEFAULT_ALGO
    random_salt: Optional[bool] = True


with open("settings.yaml") as settings_file:
    settings = yaml.safe_load(settings_file)
main_parameters = {}
if not settings["openapi_console"]:
    main_parameters["docs_url"] = None

app = FastAPI(**main_parameters)
passworder = Passworder()


@app.get("/encrypt/generators")
async def generators_list():
    return [list(Passworder.ALGO_MAP.keys())]


@app.get("/encrypt/version")
async def show_version():
    with open("version.txt", "r") as version_file:
        version = version_file.read()
    return {"version": version}


@app.post("/encrypt/")
async def encrypt(encrypt_request: EncryptRequest):
    result = {}
    try:
        # Request validation steps..
        if not encrypt_request.cleartext:
            raise ValueError("Missing cleartext entry to encrypt")
        if not encrypt_request.random_salt and not encrypt_request.salt:
            raise ValueError("Either random salt or a set salt should be given")

        parameters = encrypt_request.dict()

        # It could be a random salt was requested. In this case, generate one
        # and include it in the function call
        if parameters.get("random_salt"):
            parameters["salt"] = get_random_salt()
        del parameters["random_salt"]
        shadow_string = passworder.get_linux_password(**parameters)

        result = {
            "shadow_string": shadow_string,
            "salt": parameters["salt"],
        }
    except Exception as e:
        print(e)
        traceback.print_exc()
        result = {"error": str(e)}
    finally:
        return result


if __name__ == '__main__':
    uvicorn.run(app="main:app", reload=settings["reload"], host=settings["listen_address"],
                port=settings["listen_port"])
