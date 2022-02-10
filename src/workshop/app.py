import logging
import os.path
import sys

from fastapi import FastAPI

from src.workshop.constants import LOG_DIR
from src.workshop.api import router
from src.workshop.db.connection import metadata
from src.workshop.db.connection import engine
from src.workshop.db.connection import database
from src.workshop.constants import FORMATTER_TEMPLATE


logger = logging.getLogger('main')
logger.setLevel(logging.INFO)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

fh = logging.FileHandler(f'{LOG_DIR}/all.log')
fh.setLevel(logging.INFO)
fh_formatter = logging.Formatter()
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch_formatter = logging.Formatter(FORMATTER_TEMPLATE)
ch.setFormatter(ch_formatter)
logger.addHandler(ch)

app = FastAPI()
app.include_router(router)


@app.on_event("startup")
async def startup() -> None:
    metadata.create_all(engine)
    if not database.is_connected:
        await database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    if database.is_connected:
        await database.disconnect()
