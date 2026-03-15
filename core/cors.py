from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # # Add your Vercel frontend URL here
    "https://chat-app-ui-two.vercel.app", 
    "https://chat-app-ui-two.vercel.app/", # With trailing slash just in case


]

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
