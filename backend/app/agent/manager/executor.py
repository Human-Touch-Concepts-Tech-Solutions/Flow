import os
import sys
import importlib
from typing import Dict, Any
from manager.permission import Approval
from manager.registry import LocatePath

class Execute:
    def __init__(self, order: Dict[str, Any], user_id: str):
        # variable that holds  the excution payload from the llm 
        self.order = order
        # Sanitize and clean up whitespace around the user's directory ID or email
        self.user_id = user_id.strip() if user_id else None
        
        # Resolve the absolute base folder of your project (e.g., '/app/app/' or '/var/www')
        self.base_project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Build the path to this user's isolated sandbox folder inside active_session/
        self.user_base_dir = os.path.join(self.base_project_dir, "active_session", self.user_id)
        
        # Create a dictionary holding absolute paths for the user's specific processing zones
        self.workspace_paths = {
            "uploads": os.path.join(self.user_base_dir, "uploads"),
            "workspace": os.path.join(self.user_base_dir, "workspace"),
            "exports": os.path.join(self.user_base_dir, "exports")
        }

    async def run(self) -> Dict[str, Any]:
        # --- PRE-CHECK VALIDATIONS ---
        # Safeguard: Ensure the incoming order dict exists and is labeled as a "single" execution type
        if not self.order or self.order.get("type") != "single":
            return {"status": "error", "message": "Invalid or unhandled execution order type format."}
            
        # Extract the action array containing the execution properties
        actions = self.order.get("action", [])
        if not actions:
            return {"status": "error", "message": "Malformed order: No executable actions populated inside payload."}
            
        # Extract the dictionary values for the first action step
        action_data = actions[0]
        tool_name = action_data.get("tool_name")    # e.g., "compression"
        module_name = action_data.get("module")      # e.g., "create"
        class_name = action_data.get("class_name")  # e.g., "CreateCompression"
        method_name = action_data.get("method")      # e.g., "zip_files"
        raw_parameters = action_data.get("parameters", {}) # e.g., {"file_name": "data.txt", ...}

        # --- PIPELINE STEP 1: PERMISSION & CREDIT CHECKS ---
        # Instantiate your Approval security guard, linking it to the user's ID
        gatekeeper = Approval(user_email=self.user_id)
        
        # Request a billing/credit token allowance check
        has_credits, credit_msg = await gatekeeper.credit_check()
        if not has_credits:
            return {"status": "denied", "reason": f"Credit Check Failed: {credit_msg}"}
            
        # Request secondary functional usage clearance check
        is_allowed, usage_msg = await gatekeeper.tool_usage_check()
        if not is_allowed:
            return {"status": "denied", "reason": f"Privilege Check Failed: {usage_msg}"}

        # --- PIPELINE STEP 2: LOCATE CODE DIRECTORY ---
        # Instantiate the Registry locator with the target tool name string
        locator = LocatePath(tool_name=tool_name)
        # Asynchronously search the filesystem for the matching directory route
        resolution_result = await locator.get_tool_directory()
        
        # If the tool name cannot be found in the directory paths, abort safely
        if resolution_result["status"] == "error":
            return {"status": "error", "message": f"Registry failure: {resolution_result['message']}"}
            
        # Capture the found absolute directory path string
        tool_absolute_dir = resolution_result["absolute_path"]

        # --- PIPELINE STEP 3: WORKSPACE PATH INJECTION & MAPS ---
        # Make a shallow copy of the parameters to avoid modifying the core order state
        processed_parameters = raw_parameters.copy()
        
        # Map human-readable file names to full absolute paths inside the 'uploads' folder
        if "file_name" in processed_parameters:
            original_filename = processed_parameters["file_name"]
            processed_parameters["file_path"] = os.path.join(self.workspace_paths["uploads"], original_filename)
            # Remove the old file_name key so it doesn't conflict with our backend arguments
            del processed_parameters["file_name"]

        # --- PIPELINE STEP 4: DYNAMIC IMPORT & CLASS CONSTRUCTOR CALL ---
        try:
            # Tell the Python runtime path registry to look inside our tool folder for module files
            if tool_absolute_dir not in sys.path:
                sys.path.insert(0, tool_absolute_dir)

            # Dynamically import the target module file (e.g., importing 'create.py')
            target_module = importlib.import_module(module_name)
            
            # Fetch the actual class reference out of the loaded module
            target_class = getattr(target_module, class_name)
            
            # --- THE CRITICAL FIX ---
            # Unpack the processed parameters straight into the CLASS constructor (__init__)
            # This instantiates something like: CreateCompression(file_path="/app/.../file.txt", password="...")
            class_instance = target_class(**processed_parameters)
            
            # Locate the callable execution method inside the freshly created class instance
            execution_method = getattr(class_instance, method_name)
            
            # Asynchronously call the class method with empty parameters since they are already stored in the state
            tool_response = await execution_method()
            
            # Return a standardized execution success summary
            return {
                "status": "success",
                "tool_executed": f"{tool_name}.{module_name}.{method_name}",
                "runtime_paths": self.workspace_paths,
                "tool_output": tool_response
            }

        # Error catch block: Triggers if the module file (e.g., 'create.py') does not physically exist
        except ModuleNotFoundError as mnf_err:
            return {"status": "error", "message": f"Execution Aborted: Module file '{module_name}.py' not found. {str(mnf_err)}"}
        # Error catch block: Triggers if the class or method names were typed incorrectly by the LLM
        except AttributeError as attr_err:
            return {"status": "error", "message": f"Execution Aborted: Class '{class_name}' or Method '{method_name}' not found. {str(attr_err)}"}
        # Global catch block: Prevents custom runtime exceptions from crashing your master server loop
        except Exception as global_sys_err:
            return {"status": "error", "message": f"Runtime failure within external module thread context: {str(global_sys_err)}"}