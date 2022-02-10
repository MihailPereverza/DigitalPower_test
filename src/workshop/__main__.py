import uvicorn

from src.workshop.settings import settings


uvicorn.run(
    'src.workshop.app:app',
    host=settings.server_host,
    port=settings.server_port,
    reload=True,
)
