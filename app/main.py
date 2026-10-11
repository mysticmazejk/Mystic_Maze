from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Mystic Maze Server läuft"}