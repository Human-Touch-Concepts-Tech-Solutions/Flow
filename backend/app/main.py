# Package imports
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from app.api.v1.chat import router as chat_router


#Local imports 
from app.core.connection import (
    MongoConnection, 
    MistralConnection, 
    EmailConnection,
    OAuthConnection,
    supabase_manager



)
from app.core.security import OneTimeAuth, TokenSecurity
from app.api.v1.auth import router as auth_v1
from app.core.database import DatabaseProcess



# Load environment variables from .env file
load_dotenv()
INTELLIGENCE_API_URL = os.getenv("MISTRAL_ADDR")
print(INTELLIGENCE_API_URL)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



#Mistral connection instance (AI service)
ai_conn = MistralConnection()
mongo = MongoConnection()






# fastAp instance
app = FastAPI(
    title="Flowtru Assistant API",
    description="API for Flowtru Assistant, a personal assistant that helps you manage your tasks, calendar, and more.",
    version="2.0.0",

)

#router setup 
app.include_router(auth_v1, prefix="/api/v1/auth")
app.include_router(chat_router, prefix="/api/v1")


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

    #Mistral connection test
    ai_ready = await ai_conn.check_ai_health()
    if not ai_ready:
        logger.warning("⚠️ Mistral/Ollama is not responding. AI features will be disabled.")
        return False
    app.state.ai = ai_conn # Attach to state for use in routes

    # Mongo DB service connection
    await mongo.open_connection()
    
    # 2. Create the process instance using the connected DB
    # IMPORTANT: Make sure mongo.db is not None here!
    if mongo.db is not None:
        app.state.db_process = DatabaseProcess(mongo.db)
        logger.info("✅ DatabaseProcess attached to app.state")
    else:
        logger.error("❌ MongoDB Database instance is None!")


    #start email connection
    email_conn = EmailConnection()
    app.state.otp_service = OneTimeAuth(email_conn)

    #Google oAuth
    oauth_manager = OAuthConnection()
    app.state.oauth = oauth_manager.oauth
   
        #Supabase connection
    
    # Initialize the connection
    supabase_manager.connect()
    # Store the client in app.state for global access
    app.state.supabase = supabase_manager.client

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


@app.get("/api/v1/test-ai")
async def test_ai(prompt: str = "Hello Mistral, are you there, list 40 things you can do ?"):
    ai_service: MistralConnection = app.state.ai
    result = await ai_service.generate_response(prompt)
    return {"status": "AI Responded", "output": result.get("response")}

#test endpoints to verify API functionality

@app.get("/api/v1/test-get")
async def test_get(param: str = None):
    return {"message": "GET successful", "received": param}

@app.post("/api/v1/test-post")
async def test_post(data: dict):
    return {"message": "POST successful", "received": data}
