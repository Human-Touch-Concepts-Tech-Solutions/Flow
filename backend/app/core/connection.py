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
from supabase import create_client, Client



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
        



# Connection for Email 
class EmailConnection:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.username = os.getenv("EMAIL")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.logo_url = os.getenv("APP_LOGO_URL", "https://flowtru.vercel.app/logo.svg")

    def send_otp_email(self, to_email: str, otp: str, is_admin: bool = False, is_recovery: bool = False):
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = to_email
        
        # Determine content based on the flags
        if is_admin:
            subject = "Admin Access Verification - Flow"
            title = "Admin Security Check"
            message = "An admin login was attempted. Use the secret code below:"
        elif is_recovery:
            subject = "Reset Your Password - Flow"
            title = "Password Recovery"
            message = "We received a request to reset your password. Use the code below to proceed:"
        else:
            subject = "Verify Your Account - Flow"
            title = "Welcome to Flow!"
            message = "Please use the following One-Time Password to verify your email:"

        # Merged Professional HTML Template
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 20px;">
                <img src="{self.logo_url}" alt="Logo" style="width: 120px;">
            </div>
            <h2 style="color: #333; text-align: center;">{title}</h2>
            <p style="color: #666; font-size: 16px; line-height: 1.5; text-align: center;">{message}</p>
            <div style="background: #f4f7ff; padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;">
                <span style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #2563eb;">{otp}</span>
            </div>
            <p style="font-size: 12px; color: #999; text-align: center;">
                This code will expire in 5 minutes. If you did not request this, please ignore this email.
            </p>
        </div>
        """
        
        msg['Subject'] = subject
        msg.attach(MIMEText(html, 'html'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"EMAIL ERROR: {e}")
            return False




class OAuthConnection:
    def __init__(self):
        self.oauth = OAuth()
        self._register_google()

    def _register_google(self):
        self.oauth.register(
            name="google",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            }
        )





# Connection for Supabase (PostgreSQL + Auth)
class SupabaseManager:
    def __init__(self):
        # We use the service_role key to ensure full backend access
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.client: Client = None

    def connect(self):
        if not self.url or not self.key:
            raise ValueError("Supabase credentials are not set!")
        self.client = create_client(self.url, self.key)
        print("Supabase connection established.")

# Create a single instance to be used throughout the app
supabase_manager = SupabaseManager()