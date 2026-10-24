from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routes.game_routes import (
    router as game_router,
)
from app.routes.websocket_routes import (
    router as websocket_router,
)


app = FastAPI(
    title="Mystic Maze"
)

app.include_router(
    game_router
)

app.include_router(
    websocket_router
)

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static"
)


@app.get("/")
def root():
    """
    Liefert die Startseite der Webanwendung aus.
    """
    return FileResponse(
        "frontend/index.html"
    )