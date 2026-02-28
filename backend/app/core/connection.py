# app/core/connection.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv



# Enviroment variables
load_dotenv()

INTELLIGENCE_API_URL = os.getenv("MISTRAL_ADDR")


# Set up logging
logger = logging.getLogger(__name__)




# MongoDB Connection Class

class MongoConnection:
    def __init__(self):
        self.client = None
        self.db = None
        # Don't assign from top-level variables here
        self.database_name = None 

    async def open_connection(self):
        # Fetch directly from environment when calling the function
        # Added a fallback "flow_db" so it is NEVER None
        uri = os.getenv("MONGODB_URI")
        self.database_name = os.getenv("MONGODB_DB_NAME") or "flow_db"
        
        if not uri:
            logger.error("❌ MONGODB_URI is not set in .env")
            return

        try:
            self.client = AsyncIOMotorClient(uri)
            # Now self.database_name is guaranteed to be a string
            self.db = self.client[self.database_name]
            logger.info(f"✅ MongoDB connected: {self.database_name}")
        except Exception as e:
            logger.error(f"❌ MongoDB Connection Error: {e}")

    def attach_to_app(self, app):
        if self.db is None:
            raise RuntimeError("MongoDB connection not opened yet")
        app.state.db = self.db





# Connection instance for Mistral 7b 

class MistralConnection:
    def __init__(self, base_url: str = INTELLIGENCE_API_URL):
        self.base_url = base_url
 

    async def check_ai_health(self):
        """Verify Ollama is awake and has Mistral loaded"""
        try:
            async with httpx.AsyncClient() as client:
                # Ollama health check endpoint
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    logger.info("🤖 AI Service (Ollama) is reachable")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Cannot connect to AI Service: {e}")
            return False

    async def generate_response(self, prompt: str, model: str = "mistral"):
        """Send a prompt to Mistral"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120.0 # AI takes time to think
            )
            return response.json()