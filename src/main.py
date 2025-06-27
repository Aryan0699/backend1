from fastapi import FastAPI
from dotenv import load_dotenv
from src.database.database import Base,engine
from src.routes.auth_routes import authRouter
from src.routes.user_routes import userRouter
from src.routes.chat_route import chatRouter
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()

Base.metadata.create_all(bind=engine)
app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(authRouter,prefix="/auth")
app.include_router(userRouter,prefix="/user")
app.include_router(chatRouter,prefix="/chat")


@app.get("/")
def hello():
    return "Hello World"