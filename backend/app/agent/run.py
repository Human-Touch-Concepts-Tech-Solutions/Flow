import asyncio
import email
import json
# from click import prompt
import pytz
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from .Accessibility.database import DatabaseAccess
from app.agent.manager.time import TimeManager
from app.agent.Accessibility.vectordatabase import VectorManager
from app.agent.manager.registry import LocatePath
from app.agent.manager.permission import Approval
from app.agent.manager.executor import Execute
from app.agent.tools.information.internal import Aquire
from app.agent.tools.information.external import ExternalAquire






class FlowtruAgent:
    # 1. FIXED: Removed session_id from here so it matches the call below
    def __init__(
            self, 
            email: str, 
            ai_service: Any, 
            db_instance: Any, 
             vector_manager: VectorManager,
            env_context: Dict,
            pending_logs: List,
            session_id: str,
            data_state: Any,
           
            ):
        self.email = email
        self.ai_service = ai_service
        self.access = DatabaseAccess(db_instance)
        self.env_context = env_context
        self.pending_logs = pending_logs
        self.session_id = session_id
        self.data_state = data_state
        self.vector_manager = vector_manager
        safe_email = email.replace("@", "_").replace(".", "_")
        self.session_file = Path(f"active_sessions/{safe_email}/{session_id}.json")

       
    
    async def _sync_state(self):
        """
        Syncs the in-memory state with the session file.
        Ensures latest logs and user profile are loaded before processing input.
        """
        if not self.session_file.exists():
            raise PermissionError("SESSION_NOT_FOUND")

        # Load existing session data
        with open(self.session_file, 'r') as f:
            data = json.load(f) or {}

        # Ensure core keys exist to prevent KeyErrors later
        if "events" not in data:
            data["events"] = []
        if "user_profile" not in data:
            data["user_profile"] = {}
        if "metadata" not in data:
            data["metadata"] = {"version": "1.0", "interaction_count": 0}

        # Get user's timezone for localization
        user_tz = self.env_context.get("timezone", "UTC")

        # 1. INITIALIZE PROFILE (Only if not already done)
        if not data.get("initialized"):
            user_doc = await self.access.get_one("users", {"email": self.email})
            if user_doc:
                # Security: Remove sensitive data
                user_doc.pop("_id", None)
                user_doc.pop("hashed_password", None)
                user_doc.pop("refresh_token", None)
                user_doc.pop("token_expires", None)
                
                # CLEANING LOOP: Convert date objects to localized strings
                for key, value in user_doc.items():
                    if isinstance(value, datetime):
                        user_doc[key] = TimeManager.localize_timestamp(value.isoformat(), user_tz)
                
                data["user_profile"] = user_doc
            data["initialized"] = True

        # 2. MERGE PENDING SYSTEM LOGS
        # Logic: We check if there are logs in self.pending_logs and add them to session events
        if self.pending_logs and isinstance(self.pending_logs, list):
            for log in self.pending_logs:
                if not log or not isinstance(log, dict):
                    continue
                    
                utc_ts = log.get("utc_timestamp")
                if not utc_ts:
                    continue 

                details = log.get("raw_data") or {}
                event_type = log.get("event", "UNKNOWN_EVENT")
                
                # Process User Agent for Source Identification
                ua = details.get("user_agent", "")
                details["source"] = "Web App" if "Mozilla" in ua or "Chrome" in ua else "Mobile App"
                
                # Cleanup raw data
                details.pop("user_agent", None)
                details.pop("logged_at_utc", None)

                # Safe Date Parsing for Client-side time
                raw_device_time = details.get("client_time")
                if isinstance(raw_device_time, str):
                    try:
                        # Parsing "05/05/2026, 15:19:55"
                        converted_device_time = datetime.strptime(raw_device_time, "%d/%m/%Y, %H:%M:%S") 
                        details["client_time"] = converted_device_time.strftime("%A, %B %d, %Y, at %I:%M %p")
                    except Exception:
                        pass # Keep original format if parsing fails

                # Create the formatted event entry
                event_entry = {
                    "type": "system_event",
                    "event": event_type,
                    "description": log.get("description", "No description provided"),
                    "user_details": details, 
                    "logged_at": TimeManager.localize_timestamp(utc_ts, user_tz)
                }
                
                data["events"].append(event_entry)
            
            # Save the updated data back to the file
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=4)

        # CRITICAL: Always return data, even if no pending logs were processed
        return data


    def events_phaser(self, events):
        """
        Transforms raw session events into a chronological narrative for the AI prompt.
        Converts technical metadata into human-readable context sentences.
        """
        repharsed = []
        
        # Ensure we are iterating over a list
        if not isinstance(events, list):
            return ""

        for event in events:
            # Safety check: Skip invalid event entries
            if not isinstance(event, dict):
                continue

            etype = event.get("type")
            details = event.get('user_details') or {}
            
            # Extract technical metadata with safe defaults
            platform = details.get('platform', 'unknown system')
            source = details.get('source', 'Web App')
            tz = details.get('timezone', 'UTC')
            res = details.get('resolution', 'N/A')
            vp = details.get('viewport', 'N/A')
            ip = details.get('ip_address', '0.0.0.0')
            
            # Robust check for touch status (handles "true", True, or 1)
            is_touch_raw = str(details.get('is_touch', '')).lower()
            touch_status = "touch-enabled" if is_touch_raw == "true" else "non-touch"

            if etype == "system_event":
                # System events use 'client_time' and 'logged_at'
                client_time = details.get('client_time', 'unknown time')
                logged_at = event.get('logged_at', 'unknown')
                description = event.get('description', 'No description provided')
                
                environmental_sentence = (
                    f"Connection via {platform} ({source}) in {tz}. "
                    f"Device clock: {client_time}. Display: {res} ({vp}) {touch_status} at IP {ip}."
                )
                
                log_entry = f" - [System Log @ {logged_at}] {description}. Context: {environmental_sentence}"
                repharsed.append(log_entry)

            elif etype == "chat":
                # Chat interactions use 'device_clock' and 'timestamp'
                dev_clock = details.get('device_clock', 'unknown time')
                timestamp = event.get('timestamp', 'unknown')
                user_msg = event.get('user', '')
                ai_msg = event.get('ai', '')
                
                environmental_sentence = (
                    f"Origin: {platform} ({source}) in {tz}. "
                    f"Clock: {dev_clock}. Display: {res} ({vp}) {touch_status}."
                )
                
                interaction_entry = (
                    f" - [Interaction @ {timestamp}] "
                    f"User: '{user_msg}' | AI: '{ai_msg}'. "
                    f"Context: {environmental_sentence}"
                )
                repharsed.append(interaction_entry)

        # Return as a single string block with newlines for the prompt stack
        return "\n".join(repharsed)


    async def get_relevant_tools(self, user_text: str, files: Optional[List[Any]] = None) -> List[str]:
        """
        Priority Flow:
        1. info_search (Default)
        2. File Extension Matches (Hard Logic)
        3. Re-ranked Vector Results (Semantic + Keyword/Action Boosts)
        """
        selected_tool_names = ["info_search"]
        user_text_lower = user_text.lower()
        
        # Get all tools cached in DataState
        all_tools = self.data_state.tools 
        # print("ALL TOOLS IN DATA STATE:", all_tools)

        # 1. HANDLE FILE EXTENSIONS (High Priority)
        if files:
            extensions = set()
            for file_obj in files:
                file_name = file_obj.get("name", "") if isinstance(file_obj, dict) else str(file_obj)
                if "." in file_name:
                    extensions.add(file_name.split(".")[-1].lower())

            for ext in extensions:
                for tool in all_tools:
                    t_name = tool.get("tool_name")
                    # Check if extension exists in the keywords
                    if ext in [k.lower() for k in tool.get("keywords", [])]:
                        if t_name not in selected_tool_names:
                            selected_tool_names.append(t_name)
                if len(selected_tool_names) >= 5: break

        # 2. SEMANTIC SEARCH + RE-RANKING
        if len(selected_tool_names) < 5 and self.vector_manager:
            # Pull more candidates (10) so we have room to re-rank a hidden gem to the top
            candidates = await self.vector_manager.query(
                collection_name="system_tools",
                query_text=user_text,
                limit=10 
            )

            scored_candidates = []
            for res in candidates:
                tool_name = res.get("metadata", {}).get("tool_name")
                if tool_name in selected_tool_names:
                    continue

                # Start with the raw vector distance (lower is better)
                current_score = res.get("score", 1.0)
                
                # Find the actual tool doc in our state to check actions/keywords
                tool_doc = next((t for t in all_tools if t.get("tool_name") == tool_name), None)
                
                if tool_doc:
                    # A. Action Phrase Bonus (-0.5)
                    # Check if an entire phrase like "resize image" is in the user text
                    for action in tool_doc.get("action", []):
                        if action.lower() in user_text_lower:
                            current_score -= 0.5
                            break # Only one action bonus needed
                    
                    # B. Keyword Bonus (-0.1 per match)
                    # Check for individual word overlaps
                    user_words = set(user_text_lower.split())
                    tool_keywords = set(k.lower() for k in tool_doc.get("keywords", []))
                    overlap = user_words.intersection(tool_keywords)
                    current_score -= (len(overlap) * 0.1)

                scored_candidates.append({
                    "name": tool_name,
                    "final_score": current_score
                })

            # Sort candidates by their new adjusted score
            scored_candidates.sort(key=lambda x: x["final_score"])

            # Fill the remaining slots up to 5
            for candidate in scored_candidates:
                if candidate["name"] not in selected_tool_names:
                    selected_tool_names.append(candidate["name"])
                if len(selected_tool_names) >= 5:
                    break

        # print(f"Final Tool Selection: {selected_tool_names}")
        return selected_tool_names

            
            
         
        
            
    # prompting layers creation
    async def Dispatcher(self, user_text: str, session_data: Dict, tools_context:List[str], files: Optional[List[Dict]]) -> dict:
         
        # the First layer is the Dispatcher, which analyzes the user input and session context to determine the optimal orchestration strategy. 
        # It decides how to structure the prompt for the AI, what information to prioritize, and how to integrate any uploaded files or recent system events into the response generation process. 
        # The Dispatcher ensures that the AI's output is perfectly aligned with the user's needs and the current session dynamics.
       
       # need users informations
        users_data = session_data.get("user_profile", {})
        first_name = users_data.get("first_name", "User")
        last_name = users_data.get("last_name", "")
        gender = users_data.get("gender", "unknown")

        #tools 
        
        
        if tools_context:
            all_tools = self.data_state.tools
            prompt_segments = []
            for i, name in enumerate(tools_context,1):
                tool_doc = next((t for t in all_tools if t.get("tool_name") == name), None)

                if not tool_doc:
                    continue

                #  tools headers and description 

                segment = f" ### {i}.{name}\n"
                segment += f"**Description**: {tool_doc.get('details', 'No description')}\n"
                segment += "**Modules:**\n"

                #looping through the modules of each tool to add them to the prompt
                modules = tool_doc.get("modules", {})
                for mod_file, mod_info in modules.items():
                    mod_desc = mod_info.get("description", "Perform operations.")
                    segment += f"- `{mod_file}`: {mod_desc}\n"
                
                prompt_segments.append(segment)
            
        
        available_tools = "\n\n".join(prompt_segments)
        # print(f"full available tools: {available_tools}")
        file_attachments = "\n".join(files) 

    
    
        instructions = f"""
                <system_instructions> 
                ## ROLE: ARCHITECTURAL DISPATCHER
                You are the primary logic gate for the Flowtru ecosystem. Your sole purpose is to analyze user input and return a JSON configuration that dictates how the backend should assemble context for the final execution layer.

                ## USER_DETAILS:
                this are  is just the basic information about the user that can be useful  to know in order to provide better answers and also to have a better understanding of the user context.
                - First Name: {first_name}
                - Last Name: {last_name}
                - Gender: {gender}

                ## USER_FILE_ATTACHEMENTS:
                this is the list of files that the user has uploaded with the current request. You can use the file names and extensions to determine if any specialized tools are needed to handle them effectively. For example, if a user uploads a "report.pdf", you might want to select a tool that can extract text from PDFs or analyze document content.
                {file_attachments}

                

                ## TASK
                1. **Intent Analysis**: Identify the user intent with surgical precision, categorizing it into one of the **INTENT OPTIONS** specified to determine the appropriate response structure and tone.
                2. **Orchestration Planning**: Map out the complexity and the depth of context required to fulfill the request.
                3. **JSON Delivery**: Return a strictly formatted plan that the backend can parse to trigger the correct micro-services.
                4. **Language Detection**: If the user input is in a language other than English, identify the language and include it in the output JSON to ensure proper handling in subsequent processing layers.
                5. **Tool Selection**: For each intent, select up to tools from the <available_tools> list that are essential. If no tool is needed , return `false` ,if tools from list are not applicable, return `Nill`.

 
                ## AVAILABLE TOOLS:
                {available_tools}
                

                ## INTENT OPTIONS:
                1. GREETING: Use this for "Hi", "Hello", "Good morning", "Hey", "how far"etc.
                2. INFORMATION_REQUEST: Use this when the user is asking for specific information either about the company or this platform , if related to the user, or others that require acquiring more information.
                3. FUNCTIONAL_TASK: Use this when the user wants the system to produce, modify, or execute something. This includes generating code, creating images/logos, writing songs, editing uploaded files, or performing complex data analysis. If the backend needs to "build" or "run" something to satisfy the user, it belongs here.
                4. AUTOMATION_SCHEDULER:Use this when the intent involves recurring actions, triggers, or future-dated events. If the user mentions "every day," "remind me in 2 hours," "whenever X happens, do Y," or "set up a workflow," classify it here. This tells the backend to look for timing and logic parameters.
                5. CREATIVE_FUN: Use for lighthearted, non-functional requests like poems, jokes, fun facts, riddles, or "tell me a story." This triggers a playful and artistic persona rather than a technical one.


                ## OUTPUT RULES:
                - Return ONLY valid JSON.
                - No conversational text.
                
                ## SCHEMA:
                If intent is GREETING:
                
                {{
                    "intent": "GREETING",
                    "tone": "provide a tone to use based on the users input (e.g., formal, casual, witty),",
                    "language": give the detected language if it's not English, otherwise return "English",
                    "reply": "generated greeting here",
                   
                    

                }}

                If intent is INFORMATION_REQUEST:
                {{
                    "intent": "INFORMATION_REQUEST",
                    "tone": provide a tone to use based on the users input (e.g., formal, casual, technical),
                    "language": give the detected language if it's not English, otherwise return "English",
                    "about": specify if the user input is related to "company_info" , "user_info", or "other". This will help the backend to know where to look for the information.,
                    "selected_tools": by default the main to for this intent is info_search so provide also provide the module best for it  eg ["tool_name": "tool_module"] | false | "Nill",
                    
                    "research_queries": "Analyze the user's intent. If the topic requires up-to-date information, technical specifics, or data the LLM might not have in its static training (e.g., latest software versions, current events, or deep-dive technical specs), generate an array of at least 8 targeted search queries and at most 15 . These queries should cover at least 90% of the scope needed to provide a professional, expert-level answer. If no external research is needed (e.g., 'write a story'), return an empty array [].",
                    "prompt": "Write a high-quality, professional system prompt starting with 'You are...'. It must be written in the first person as if talking directly to the LLM that will execute it. Include a specific persona, a detailed step-by-step methodology, and strict output constraints. Do not provide commentary; only output the final prompt text here.",
                    "token_allocation": "Based on the complexity of the user's request and the depth of information needed, provide a token allocation recommendation for the execution layer. For example, if the user is asking for a simple fact, you might allocate lower amount of tokens. If they are asking for an in-depth analysis with multiple steps, you might allocate higher amount of tokens. This helps ensure that the execution layer has enough resources to generate a complete and accurate response without running out of tokens prematurely. the max tokens to allocate is 1500."
                    "quick_reply": "Act as a strict, professional system coordinator. Evaluate if the user's intent is too vague to resolve to a specific database asset or action. If crucial context is missing, write a single, highly precise markdown sentence inviting the user to provide clarification. Frame it as a helpful question. You are ONLY allowed to ask for: 1. Specific file names or file extensions, 2. A more specific date/time window, 3. The specific tool action they intended to perform. DO NOT speculate about edge cases like other users, locations, or devices. Focus entirely on parameters that narrow down database search results. Example: 'To find the exact files you uploaded last week, could you please specify the **file names** or their **file extensions** (e.g., .pdf, .jpeg)?'. If the input is already sufficient to run an initial query or search, return an empty string \"\".",
               
                 }}
                If intent is FUNCTIONAL_TASK:
                {{
                    "intent": "FUNCTIONAL_TASK",
                    "tone": provide a tone to use based on the users input (e.g., formal, casual, technical, witty),
                    "language": give the detected language if it's not English, otherwise return "English",
                    "insight": provide a more insight so to help enable better search in the vector database. For example, if the user is asking "What is my current subscription plan?" you can provide insight such as "The user is likely asking for details about their subscription benefits, limitations, or renewal date." ,
                    "about": specify if the user input is related to "company_info" or "user_info". This will help the backend to know where to look for the information.,
                    "selected_tools": ["tool_name":"provide the module based on the tool selected best suited for the task"] | false | "Nill",
                    "prompt": "Write the 'You are...' system prompt as a 'Final Task Executor.' It should assume that all necessary details from the 'quick_reply' phase have already been provided. Instead of telling the LLM to 'gather' or 'prompt' for info, instruct it to 'use the provided data' to build the final output. The instructions should focus entirely on formatting, tone, and the final structure of the result (e.g., 'Generate the receipt using the following data...')."
                    "quick_reply": "Act as a professional consultant. If more detail is needed to reach 99% accuracy, write a brief, polite sentence in markdown that invites the user to provide the missing specifics. Frame it as a helpful question (e.g., 'To make this perfect, could you please provide...'). Use bolding for the key items. make sure it is related to the user and dont assume another users in relation to your answer. If the user's input is already perfect, return an empty string \"\"."
                }}

                 If intent is AUTOMATION_SCHEDULER:
                
                {{
                    "intent": "AUTOMATION_SCHEDULER",
                    "tone": "provide a tone to use based on the users input (e.g., formal, casual, witty),",
                    "language": give the detected language if it's not English, otherwise return "English",
                    "insight": provide a more insight so to help enable better search in the vector database. For example, if the user is asking "What is my current subscription plan?" you can provide insight such as "The user is likely asking for details about their subscription benefits, limitations, or renewal date." ,
                    "about": specify if the user input is related to "company_info" or "user_info". This will help the backend to know where to look for the information.,
                    "selected_tools": ["tool_name"] | false | "Nill",
                    "prompt": "Write the 'You are...' system prompt as a 'Final Task Executor.' It should assume that all necessary details from the 'quick_reply' phase have already been provided. Instead of telling the LLM to 'gather' or 'prompt' for info, instruct it to 'use the provided data' to build the final output. The instructions should focus entirely on formatting, tone, and the final structure of the result (e.g., 'Generate the receipt using the following data...')."
                    "quick_reply": "Act as a professional consultant. If more detail is needed to reach 99% accuracy, write a brief, polite sentence in markdown that invites the user to provide the missing specifics. Frame it as a helpful question (e.g., 'To make this perfect, could you please provide...'). Use bolding for the key items. If the user's input is already perfect, return an empty string \"\"."
                    
                   
                    

                }}

                 If intent is CREATIVE_FUN:
                
                {{
                    "intent": "CREATIVE_FUN",
                    "tone": "provide a tone to use based on the users input (e.g., formal, casual, witty),",
                    "language": give the detected language if it's not English, otherwise return "English",
                    "insight": provide a more insight so to help enable better search in the vector database. For example, if the user is asking "What is my current subscription plan?" you can provide insight such as "The user is likely asking for details about their subscription benefits, limitations, or renewal date." ,
                    "about": specify if the user input is related to "company_info" or "user_info". This will help the backend to know where to look for the information.,
                    "selected_tools": ["tool_name"] | false | "Nill",
                    "prompt": "Write the 'You are...' system prompt as a 'Final Task Executor.' It should assume that all necessary details from the 'quick_reply' phase have already been provided. Instead of telling the LLM to 'gather' or 'prompt' for info, instruct it to 'use the provided data' to build the final output. The instructions should focus entirely on formatting, tone, and the final structure of the result (e.g., 'Generate the receipt using the following data...')."
                    "quick_reply": "Act as a professional consultant. If more detail is needed to reach 99% accuracy, write a brief, polite sentence in markdown that invites the user to provide the missing specifics. Frame it as a helpful question (e.g., 'To make this perfect, could you please provide...'). Use bolding for the key items. If the user's input is already perfect, return an empty string \"\"."
                    
                   
                    

                }}
                </system_instructions>

                


                <user_input>
                {user_text}
                </user_input>
                """
        return instructions

    async def _build_prompt_stack(self, user_text: str, session_data: Dict, tools_context: Dict) -> str:

        # getting user bio:
        # session_data = session_data or {}
    
        # # Force user_profile to be a dict
        # user_profile = session_data.get("user_profile") or {}
        
        # first_name = user_profile.get("first_name", "User")
        # last_name = user_profile.get("last_name", "")
        # gender = user_profile.get("gender", "unknown")
        # profession = user_profile.get("profession", "unknown")
        # phone = user_profile.get("phone", "unknown")
        # role = user_profile.get("role", "unknown")
        # access_level = user_profile.get("access_level", "unknown")
        # time_zone = user_profile.get("timezone", "unknown")
        
        # # CRITICAL FIX: Add 'or {}' here
        # credit = user_profile.get("credits") or {} 
        # credits_bal = credit.get("balance", "unknown")
        # total_used = credit.get("total_used", "unknown")
        # total_bought = credit.get("total_bought", "unknown")

        # # CRITICAL FIX: Add 'or {}' here
        # subscription = user_profile.get("subscription") or {}
        # sub_plan = subscription.get("plan", "unknown")
        
        print("TOOLS CONTEXT FOR PROMPT:", tools_context)   
       

    # We start with the XML container for high-priority logic
        prompt = f"""
       
        you are a dispatcher agent for a system called Flowtru. Your job is to analyze the user's input and the session context to determine the best way to fulfill their request. You will return a JSON object that tells the backend how to structure the final prompt for the execution layer, what tools to use, and any other relevant information.
        ### USER INPUT
        {user_text}

                
                
        """
        return prompt
        


    async def execute(self, text: str, files: Optional[List[Any]] = None) -> Dict[str, Any]:
        try:
            #users chats and logs for current day or current session,
            session_data = await self._sync_state()
            # converting  users email to a safe format for file naming
            safe_email = self.email.replace("@", "_").replace(".", "_")

            # tools filtering based on users inout and file attachments if exist, 
            tools_context = await self.get_relevant_tools(text, files)

            # ====== credit and permission  might be here
            # ======    # ======       # ======


            # First layer Dispatcher: 
            # Analyzes user input and session context to determine orchestration strategy
            first_layer_prompt = await self.Dispatcher(text, session_data, tools_context , files)
            ai_reply = await self.ai_service.generate_response(first_layer_prompt)

            # rephrasal layer: takes the raw AI output and transforms it into a structured format that the backend can easily parse for execution. It also extracts any critical insights or parameters needed for the next steps.
            rephrase = json.loads(ai_reply.strip().replace("```json", "").replace("```", "").strip())

            # test  print 
            # print("DISPATCHER OUTPUT:", rephrase)

            #conditional logic based on intents 
            if rephrase["intent"] == "GREETING":
                 ai_reply = rephrase["reply"].strip()
            
            elif rephrase["intent"] == "INFORMATION_REQUEST":
                pass

            # final_prompt = await self._build_prompt_stack(text, session_data, tools_context)
            
          

           
        
           
            





            #registry aspect
            # This would be dynamically determined based on the user's request
            
            # locator = LocatePath(user_id=safe_email)
            # resolution_result = await locator.prepare_workspace()
            
           # registry logic works good 
           # permission aspect
            # approval = Approval(self.email)
            # credit_decision, credit_message = await approval.credit_check()
            # tool_decision, tool_message = await approval.tool_usage_check()
            # 1. Prepare your array of semantic queries
            queries_to_search = ["FastAPI", "Python (programming language)"]

            # 2. Pass the required dependencies into the initializer
            search_tool = ExternalAquire(
                vector_db=self.vector_manager,  # Replace with where your VectorManager lives
                db_access=self.access,  # Your DatabaseAccess instance
                queries=queries_to_search,
                max_results=3,                           # Optional: defaults to 4
                bypass_cache=False                       # Optional: set to True for real-time news forced lookup
            )

            # 3. Execute the pipeline
            context_payload = await search_tool.execute()

            print(f"Search Tool Result: {context_payload}")
            #=================================================================
            # order = {
            #             "type": "single",
            #             "action": [
            #                 {
            #                     "tool_name": "rename",
            #                     "module": "create",
            #                     "class_name": "CreateRename",
            #                     "method": "rename_file",
            #                     "parameters": {
            #                         "file_name": "WhatsApp Image 2026-05-20 at 9.12.40 AM.jpeg",
            #                         "new_name": "new name.jpeg"
            #                     }
            #                 }
            #             ]
            #         }
            # tool_call = Execute(order=order, user_id=safe_email)
            # result = await tool_call.run()
            # print("Execution Result:", result)

           
            


            
             # For greetings, we can directly use the reply from the Dispatcher without further processing.
            
          
            # Localize the current chat time
            user_tz = self.env_context.get("timezone", "UTC")
            
            current_local_dt = TimeManager.get_user_time(user_tz)

            ua = self.env_context.get("user_agent", "")
            app_source = "Web App" if "Mozilla" in ua or "Chrome" in ua else "Mobile App"
            
            # Format the device clock for AI clarity
            # We convert the raw string "22/04/2026..." into the pretty "Thursday..." format
            raw_device_time = self.env_context.get("client_time")
            formatted_device_clock = TimeManager.localize_device_time(raw_device_time, user_tz)
            

            #CHAT LOG: Includes user_details and localized time
            session_data["events"].append({
                "type": "chat",
                "user": text,
                "ai": ai_reply,
                "timestamp": TimeManager.format_for_ai(current_local_dt),
                "user_details": {
                    "source": app_source,
                    "timezone": user_tz,
                    "device_clock": formatted_device_clock, # Pretty format
                    "platform": self.env_context.get("platform"),
                    "resolution": self.env_context.get("resolution"),
                    "viewport": self.env_context.get("viewport"),
                    "is_touch": self.env_context.get("is_touch"),
                    "ip_address": self.env_context.get("ip_address")
                }
            })
            
            session_data["metadata"]["interaction_count"] += 1
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=4)

            return {"status": "success", "reply": ai_reply}
        except Exception as e:
            print(f"Agent Error: {e}")
            return {"status": "error", "reply": "Internal error."}

    
        

    
async def run_agent(
    email: str, 
    text: str, 
    ai_service: Any,
    db: Any,
    vector_manager: VectorManager,
    files: Optional[List[Any]] = None,
    env_context: Dict = None,
    pending_logs: List = None,
    session_id: str = None,
    data_state: Any = None,
    
) -> Dict[str, Any]:
    # 4. FIXED: Passed exactly what __init__ expects
    agent = FlowtruAgent(
        email, 
        ai_service,
        db, 
        vector_manager,
        env_context,
       pending_logs,
        session_id,
        data_state,
       
        
        )
    
    # 5. Return the result of the execution
    return await agent.execute(text, files)