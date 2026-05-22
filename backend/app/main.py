# Package imports
import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from app.api.v1.chat import router as chat_router
from app.api.v1.ws import router as ws_router
from app.agent.manager.monitor import Monitor
from app.agent.manager.data import DataState
from app.agent.Accessibility.vectordatabase import VectorManager


#Local imports 
from app.core.connection import (
    MongoConnection, 
    MistralConnection, 
    EmailConnection,
    OAuthConnection,
    supabase_manager,
    manager,
    VectorConnection



)
from app.core.security import OneTimeAuth, TokenSecurity
from app.api.v1.auth import router as auth_v1
from app.core.database import DatabaseProcess



# Load environment variables from .env file
load_dotenv()
INTELLIGENCE_API_URL = os.getenv("MISTRAL_ADDR")
# print(INTELLIGENCE_API_URL)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



#Mistral connection instance (AI service)


# state management for agent logs and system persona
state_registry = DataState()





# Lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Directory setup
    os.makedirs("active_sessions", exist_ok=True)
    logger.info("Starting up Flowtru Assistant API...")
   
    # 2. Connections Initialization
    ai_conn = MistralConnection()
    mongo = MongoConnection()
    vector_conn = VectorConnection() # Initialize the connection object

    # 3. AI Health Check
    ai_ready = await ai_conn.check_ai_health()
    if not ai_ready:
        logger.warning("⚠️ Mistral Cloud API is not responding. AI features may fail.")
    app.state.ai = ai_conn

    # 4. Connect to Vector DB First
    await vector_conn.connect()
    vector_conn.attach_to_app(app)
    # Initialize the Manager (This is the 'vector_db' the Monitor needs)
    vector_manager = VectorManager(vector_conn)
    app.state.vector_manager = vector_manager

    # 5. Connect to MongoDB
    await mongo.open_connection()
    if mongo.db is not None:
        app.state.data_state = DataState()
        app.state.db_process = DatabaseProcess(mongo.db)
        
        # FIX: Pass the vector_manager as the 3rd argument here!
        app.state.monitor = Monitor(
            mongo.db, 
            app.state.data_state, 
            vector_manager
        )
        
        await app.state.monitor.start()
        logger.info("✅ DataState, VectorDB, and Monitor are synchronized.")
    else:
        logger.error("❌ MongoDB Database instance is None!")

    # 6. Initialize remaining services
    email_conn = EmailConnection()
    app.state.otp_service = OneTimeAuth(email_conn)
    
    oauth_manager = OAuthConnection()
    app.state.oauth = oauth_manager.oauth
   
    supabase_manager.connect()
    app.state.supabase = supabase_manager.client
    app.state.connection_manager = manager

    yield  # Application runs...

    # 7. CLEANUP
    logger.info("Shutting down Flowtru Assistant API...")
    await mongo.close_connection()


# fastAp instance
app = FastAPI(
    title="Flowtru Assistant API",
    description="API for Flowtru Assistant, a personal assistant that helps you manage your tasks, calendar, and more.",
    version="2.0.0",
    lifespan=lifespan

)

#router setup 
app.include_router(auth_v1, prefix="/api/v1/auth")
app.include_router(chat_router, prefix="/api/v1")
# Include the router
app.include_router(ws_router, prefix="/api/v1")

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




# test routes 

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


@app.get("/api/v1/test/monitor-check/{email}")
async def check_user_signal_box(email: str):
    """
    Test endpoint to see if the Monitor has deposited any logs 
    for a specific user in the DataState.
    """
    # Grab the DataState from app.state
    state_registry = app.state.data_state
    
    # Consume logs (This will pull them out and clear the box)
    logs = await state_registry.consume_logs(email)
    
    if not logs:
        return {
            "status": "empty",
            "message": f"No new updates found for {email}. Try changing something in MongoDB!"
        }
    
    return {
        "status": "updates_found",
        "user": email,
        "log_count": len(logs),
        "updates": logs
    }


@app.get("/api/v1/debug/state")
async def inspect_system_state():
    """
    Complete view of the Brain: 
    Shows Identity, Rules, and Detailed User Logs.
    """
    state: DataState = app.state.data_state
    config = await state.get_config()
    
    # 1. Prepare detailed view of user logs
    detailed_registry = {}
    async with state._lock: # Lock for safety while reading
        for email, logs in state._registry.items():
            detailed_registry[email] = {
                "pending_count": len(logs),
                "history": logs  # Shows timestamp, event, description, and raw_data
            }
    
    # 2. Return everything in one clean report
    return {
        "status": "success",
        "memory_report": {
            "system_config": config,  # This brings back your 'identity' and 'app_config'
            "live_user_updates": detailed_registry,
            "counts": {
                "config_categories": list(config.keys()),
                "users_with_pending_logs": len(detailed_registry)
            }
        },
        "environment": os.getenv("ENV", "development")
    }


# vector database test endpoint
@app.get("/api/v1/debug/vector-test")
async def test_vector_logic(
    action: str = Query(..., description="Options: 'embed', 'store', 'search'"),
    text: str = "This is a test sentence about artificial intelligence"
):
    """
    Playground to test the Vector Engine logic.
    """
    engine: VectorConnection = app.state.vector_engine
    
    # Check if engine is initialized
    if not engine or not engine.client:
        return {"error": "Vector engine not initialized"}

    try:
        # 1. TEST EMBEDDING ONLY
        if action == "embed":
            vector = engine.get_embedding(text)
            return {
                "input": text,
                "vector_sample": vector[:5], # Just show the first 5 dimensions
                "dimensions": len(vector)
            }

        # 2. TEST STORAGE (Upsert)
        elif action == "store":
            # Get or create a test collection
            collection = engine.client.get_or_create_collection(name="test_collection")
            
            # Generate the vector
            vector = engine.get_embedding(text)
            
            # Add to ChromaDB
            # We use a static ID for testing
            collection.upsert(
                ids=["test_doc_1"],
                embeddings=[vector],
                metadatas=[{"source": "debug_route", "timestamp": "now"}],
                documents=[text]
            )
            return {"status": "stored", "id": "test_doc_1", "text": text}

        # 3. TEST SEARCH (The "Magic" part)
        elif action == "search":
            collection = engine.client.get_collection(name="test_collection")
            
            # Convert query to vector
            query_vector = engine.get_embedding(text)
            
            # Search for the top 1 result
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=1
            )
            
            return {
                "query": text,
                "match": results["documents"][0][0] if results["documents"] else "No match",
                "distance": results["distances"][0][0] if results["distances"] else None,
                "metadata": results["metadatas"][0][0] if results["metadatas"] else None
            }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    


from fastapi import Query

@app.get("/test-dispatcher")
async def debug_dispatcher(text: str = Query(..., description="The message to analyze")):
    try:
        # 1. Initialize the agent (mocking the database/session parts for the test)
        from app.agent.run import FlowtruAgent
        import json
        
        agent = FlowtruAgent(
            email="test@flowtru.ai",
            ai_service=app.state.ai, # Using the AI state you initialized
            db_instance=None,
            env_context={},
            pending_logs=[],
            session_id="debug_session",
            data_state=None
        )
        
        # 2. Get the prompt string from your Dispatcher method
        dispatcher_instructions = await agent.Dispatcher(text)
        
        # 3. Call the AI service directly to see the raw output
        raw_ai_response = await app.state.ai.generate_response(dispatcher_instructions)
        
        # 4. Attempt to parse it as JSON for a clean browser view
        try:
            # Cleaning common LLM markdown artifacts
            clean_json = raw_ai_response.replace("```json", "").replace("```", "").strip()
            json_decision = json.loads(clean_json)
            return {
                "input": text,
                "decision": json_decision,
                "status": "success"
            }
        except Exception:
            return {
                "input": text,
                "raw_reply": raw_ai_response,
                "error": "AI did not return valid JSON"
            }
            
    except Exception as e:
        return {"error": str(e)}
    


@app.get("/api/v1/debug/vector-inspect")
async def inspect_vector_db(collection_name: str = "system_tools"):
    """
    Directly peek into a ChromaDB collection to see stored documents and metadata.
    """
    try:
        # 1. Access the manager
        vm: VectorManager = app.state.vector_manager
        
        # 2. Get the collection
        collection = vm.client.get_collection(name=collection_name)
        
        # 3. Get all data (peek at the first 10 items)
        data = collection.get(
            include=["documents", "metadatas", "embeddings"] # Leave out embeddings if it's too much text
        )
        
        return {
            "collection": collection_name,
            "count": collection.count(),
            "items": [
                {
                    "id": data["ids"][i],
                    "content": data["documents"][i],
                    "metadata": data["metadatas"][i]
                }
                for i in range(len(data["ids"]))
            ]
        }
    except Exception as e:
        return {"error": str(e), "message": f"Could not find collection '{collection_name}'"}

@app.get("/api/v1/debug/vector-collections")
async def list_collections():
    """List all active collections in ChromaDB."""
    vm: VectorManager = app.state.vector_manager
    colls = vm.client.list_collections()
    return {"collections": [c.name for c in colls]}



@app.get("/api/v1/debug/vector-search")
async def search_vector_db(
    q: str = Query(..., description="The natural language query to search for"),
    collection_name: str = "system_tools",
    limit: int = 3
):
    """
    Search a collection using natural language.
    """
    try:
        vm: VectorManager = app.state.vector_manager
        
        # Use the query method from your VectorManager
        results = await vm.query(
            collection_name=collection_name,
            query_text=q,
            limit=limit
        )
        
        return {
            "query": q,
            "collection": collection_name,
            "match_count": len(results),
            "results": results
        }
    except Exception as e:
        return {"error": str(e)}