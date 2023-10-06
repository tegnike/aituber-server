from fastapi import FastAPI
from app.routers import base
import ptvsd
import os

if os.getenv('DEBUG_MODE') == "1":
    # デバッグ用コード
    ptvsd.enable_attach(address=('0.0.0.0', 5678), redirect_output=True)
    ptvsd.wait_for_attach()

app = FastAPI()
app.include_router(base.router)
