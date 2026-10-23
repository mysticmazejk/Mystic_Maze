from fastapi import FastAPI

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


@app.get("/")
def root():
    return {
        "message": "Mystic Maze Server läuft"
    }