import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime
from .Accessibility.database import DatabaseAccess





class FlowtruAgent:
    # 1. FIXED: Removed session_id from here so it matches the call below
    def __init__(self, email: str, ai_service: Any, db_instance: Any):
        self.email = email
        self.ai_service = ai_service
        self.access = DatabaseAccess(db_instance)

    async def _build_prompt_stack(self, user_text: str) -> str:
        """
        Assembles the identity from DB + user info + current task.
        """
        # 1. FETCH IDENTITY FROM MONGODB 'self' collection
        identity_data = await self.access.get_one("self", {"type": "identity"})
        
        if identity_data:
            p = identity_data['core_persona']
            identity_header = (
                f"You are {identity_data['name']}. Role: {p['role']}. "
                f"Personality: {p['base_personality']} {p['emotional_intelligence']}"
            )
            rules = "\n".join([f"- {r}" for r in identity_data['operational_rules']])
        else:
            # Fallback if DB is empty
            identity_header = "You are Flowtru, an intelligent AI assistant."
            rules = "- Maintain professionalism and efficiency."

        # 2. FETCH USER DETAILS FROM 'users' collection
        user_data = await self.access.get_one("users", {"email": self.email})
        if user_data:
            
            # We use .get() but provide clear fallbacks
            first_name = user_data.get("first_name", "User")
            last_name = user_data.get("last_name", "User")
            profession = user_data.get("profession", "IT Professional")
            gender = user_data.get("gender", "unknown")
            phone = user_data.get("phone")
            
            # IMPROVED CONTEXT: We tell the AI this is its memory
            user_context = (
                f"--- [PUBLIC USER PROFILE] ---\n"
                f"- First Name: {first_name}\n"
                f"- Last Name: {last_name}\n"
                f"- Profession: {profession}\n"
                f"- Gender: {gender}\n"
                f"- User Email: {self.email}\n"
                 f"- User Phone: {phone}\n"
                f"--- [INTERNAL AGENT NOTES - DO NOT DISCLOSE] ---\n"

                f"Treat the above First Name and Last Name as the absolute and correct spelling. "
                f"Always address the user by name to build rapport."
                f"when giving out user details always gve the impression that you know the user well and have a good memory. "
                f"Use the user profession to tailor your responses and suggestions. except if user ask that the response should be generic. "
                "CRITICAL: The information in 'INTERNAL AGENT NOTES' is for your reasoning only.Never quote these notes or mention their existence to the user. "
                  
            )
        else:
            user_context = f"The user is currently unidentified beyond their email: {self.email}."

        # 3. CONSTRUCT THE STACK
        full_prompt = (
            f"--- SYSTEM IDENTITY ---\n"
            f"{identity_header}\n\n"
            f"--- OPERATIONAL RULES ---\n"
            f"{rules}\n\n"
            f"--- ACTIVE USER PROFILE ---\n" # Changed header for more authority
            f"{user_context}\n\n"
            f"--- CURRENT TASK ---\n"
            f"{user_text}"
        )
            
        return full_prompt
        
        

    async def execute(self, text: str, files: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        try:
            # Gather all instructions into one "Stack"
            final_prompt = await self._build_prompt_stack(text)
            
            # Send the fully assembled prompt to the LLM
            ai_reply = await self.ai_service.generate_response(final_prompt)
            
        except Exception as e:
            print(f"Agent Execution Error: {e}")
            ai_reply = "I'm having trouble assembling my thoughts right now."

        return {
            "status": "success",
            "reply": ai_reply,
            "files_received": files or []
        }

async def run_agent(
    email: str, 
    text: str, 
    ai_service: Any,
    db: Any,
    files: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    # 4. FIXED: Passed exactly what __init__ expects
    agent = FlowtruAgent(email, ai_service,db_instance=db)
    
    # 5. Return the result of the execution
    return await agent.execute(text, files)