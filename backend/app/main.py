# Package imports
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

#Local imports 


# Load environment variables from .env file
load_dotenv()


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# fastAp instance
app = FastAPI()



app = FastAPI(
    title="Flowtru Assistant API",
    description="API for Flowtru Assistant, a personal assistant that helps you manage your tasks, calendar, and more.",
    version="2.0.0",

)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to restrict origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Session Middleware
# Used for OAuth (Google/GitHub) and temporary state
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("JWT_SECRET", "dev-session-secret"),
    session_cookie="ai_platform_session",
    same_site="lax",
    https_only=False  # Set to True if using HTTPS/Production
)




# Lifecycle events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Flowtru Assistant API...")
    # Initialize database connections, load models, etc. here  
    pass



@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Flowtru Assistant API...")
    # Clean up resources, close database connections, etc. here
    pass




# Include API routes

@app.get("/")
async def health_check():
    """Basic health check to verify API is live"""
    return {
        "status": "online",
        "version": "2.0.0",
        "environment": os.getenv("ENV", "development")
    }


#test endpoints to verify API functionality

@app.get("/api/v1/test-get")
async def test_get(param: str = None):
    return {"message": "GET successful", "received": param}

@app.post("/api/v1/test-post")
async def test_post(data: dict):
    return {"message": "POST successful", "received": data}
