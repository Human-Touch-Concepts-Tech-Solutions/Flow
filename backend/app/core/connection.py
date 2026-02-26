# app/core/connection.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv



# Enviroment variables
load_dotenv()
MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB_NAME = os.getenv("MONGODB_DB_NAME")


# Set up logging
logger = logging.getLogger(__name__)



# MongoDB Connection Class

class MongoConnection:
    def __init__(self):
        self.client = None
        self.db = None
        self.database_name = MONGO_DB_NAME

    async def open_connection(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[self.database_name]
        logger.info(f"✅ MongoDB connected: {self.database_name}")

    async def close_connection(self):
        if self.client:
            self.client.close()
            logger.info("❌ MongoDB connection closed")

    def attach_to_app(self, app):
        if self.db is None:
            raise RuntimeError("MongoDB connection not opened yet")
        app.state.db = self.db

