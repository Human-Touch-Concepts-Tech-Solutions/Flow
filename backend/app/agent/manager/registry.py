import os
from typing import Dict, Optional, Any
import json
import asyncio


# This class is responsible for managing the registry of tools and their corresponding paths.
class LocatePath:
    
    def __init__(self, tool_name: Optional[str] = None, user_id: Optional[str] = None, file_name: Optional[str] = None):
        self.tool_name = tool_name.strip() if tool_name else None
        self.user_id = user_id.strip() if user_id else None
        self.file_name = file_name.strip() if file_name else None
        # directory paths
        # Establishes absolute references relative to this file's position
        # 1. Get the absolute path of the 'manager' directory
        manager_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Step up 1 level to the 'agent' directory (where tools live)
        self.agent_dir = os.path.abspath(os.path.join(manager_dir, ".."))
        self.tools_root_dir = os.path.join(self.agent_dir, "tools")
        
        # 3. Step up 2 levels from manager to reach the 'backend' project root (where active_sessions live)
        self.backend_root_dir = os.path.abspath(os.path.join(manager_dir, "..", ".."))
        self.user_root_dir = os.path.join(self.backend_root_dir, "active_sessions")

    async def get_tool_directory(self) -> Dict[str, Any]:
        """
        Asynchronously walks the 'tools/' tree to find the matching tool directory name.
        """
        if not self.tool_name:
            return {"status": "error", "message": "No tool name provided for resolution."}

        if not os.path.exists(self.tools_root_dir):
            return {"status": "error", "message": f"Base tools directory not found at: {self.tools_root_dir}"}

        # We run the file walk engine. This remains highly responsive.
        for root, dirs, _ in os.walk(self.tools_root_dir):
            if self.tool_name in dirs:
                absolute_tool_path = os.path.abspath(os.path.join(root, self.tool_name))
                return {
                    "status": "success",
                    "tool_name": self.tool_name,
                    "absolute_path": absolute_tool_path
                }

        return {
            "status": "error",
            "message": f"Tool target folder '{self.tool_name}' could not be located inside the tools directory tree."
        }
    
    async def get_user_file_directory(self) -> Dict[str, Any]:
        """
        Asynchronously opens the user's metadata.json inside their active session 
        assets directory and searches for the file's absolute path using self.file_name.
        """
        # First check if user_id and file_name have content in them
        if not self.user_id or not self.file_name:
            return {
                "status": "error", 
                "message": "Both user_id and file_name must be provided to locate a user file path."
            }

        # Resolve paths based on your architecture: active_sessions/user_id/assets/metadata.json
        user_session_dir = os.path.join(self.user_root_dir, self.user_id)
        
        # --- DOCKER DOUBLE /APP PATH SANITIZER ---
        if "/app/app" in user_session_dir:
            user_session_dir = user_session_dir.replace("/app/app", "/app")
            
        print(f"Resolved user session directory: {user_session_dir}")
        metadata_file_path = os.path.join(user_session_dir, "assets", "metadata.json")

        # Guard Check: Ensure the user's active session directory exists
        if not os.path.exists(user_session_dir):
            return {"status": "error", "message": f"Active user session profile directory not found for: {self.user_id}"}

        # Guard Check: Ensure the metadata.json tracking file exists
        if not os.path.exists(metadata_file_path):
            return {"status": "error", "message": f"Metadata registry tracking map is missing at: {metadata_file_path}"}

        try:
            # Non-blocking file read operation via thread offloading
            def read_json():
                with open(metadata_file_path, "r", encoding="utf-8") as f:
                    return json.load(f)

            metadata_payload = await asyncio.to_thread(read_json)

            # Safely navigate the nested keys: registry -> files
            registry_data = metadata_payload.get("registry", {})
            files_map = registry_data.get("files", {})

            # Search for the file using its name from the files:{} dictionary
            if self.file_name not in files_map:
                return {
                    "status": "error", 
                    "message": f"Target file '{self.file_name}' is not cataloged in the user's asset logs."
                }

            # Once found, grab the abs_path value
            target_file_entry = files_map[self.file_name]
            absolute_file_path = target_file_entry.get("abs_path")

            if not absolute_file_path:
                return {
                    "status": "error",
                    "message": f"Catalog entry discovered for '{self.file_name}', but 'abs_path' was empty."
                }

            # --- DOCKER DOUBLE /APP PATH SANITIZER FOR FILE PATH ---
            # Also clean the path loaded out of metadata.json if it contains the double-nesting
            if "/app/app" in absolute_file_path:
                absolute_file_path = absolute_file_path.replace("/app/app", "/app")

            return {
                "status": "success",
                "absolute_path": absolute_file_path
            }

        except json.JSONDecodeError:
            return {"status": "error", "message": "Corrupted or malformed JSON data inside metadata.json file."}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error reading user registry map: {str(e)}"}
        


    async def prepare_workspace(self) -> Dict[str, Any]:
        """
        Asynchronously verifies if the user's workspace directory exists inside assets/.
        If it doesn't exist, it creates it. If it does, it ensures it is ready for use.
        Returns the absolute path to the workspace with double '/app' strings removed.
        """
        if not self.user_id:
            return {"status": "error", "message": "User identifier context is required to prepare a workspace."}

        # 1. Build the path: active_sessions/user_id/assets/workspace
        workspace_path = os.path.join(self.user_root_dir, self.user_id, "assets", "workspace")

        # 2. Docker Fail-safe: Strip any double /app nesting if it creeps in
        if "/app/app" in workspace_path:
            workspace_path = workspace_path.replace("/app/app", "/app")

        try:
            # Run the directory checking and creation inside a non-blocking thread
            def handle_disk_io():
                # Check if workspace directory physically exists
                if not os.path.exists(workspace_path):
                    # exist_ok=True prevents race conditions if multiple tasks try to create it simultaneously
                    os.makedirs(workspace_path, exist_ok=True)
                    print(f"Initialized brand new workspace directory at: {workspace_path}")
                else:
                    print(f"Verified existing workspace directory at: {workspace_path}")
                
                return workspace_path

            resolved_workspace = await asyncio.to_thread(handle_disk_io)

            return {
                "status": "success",
                "workspace_path": resolved_workspace
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to initialize or verify file system workspace: {str(e)}"
            }