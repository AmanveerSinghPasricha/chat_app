from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from core.database import engine, Base
from core.exceptions import http_exception_handler
from core.cors import setup_cors
from auth.router import router as auth_router
from user.router import router as user_router
from friend.router import router as friend_router
from user.router import router as user_router
from chat.router import router as chat_router

app = FastAPI()

app.add_exception_handler(HTTPException, http_exception_handler)

setup_cors(app)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(friend_router)
app.include_router(chat_router)