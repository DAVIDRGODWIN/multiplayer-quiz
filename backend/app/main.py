from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, questions, rooms, scores, internal

app = FastAPI(title="Multiplayer Quiz API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(rooms.router)
app.include_router(scores.router)
app.include_router(internal.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
