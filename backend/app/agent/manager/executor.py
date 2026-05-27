import sys
import os
import shutil
import importlib
import asyncio
from typing import Dict, Any
from app.agent.manager.permission import Approval
from app.agent.manager.registry import LocatePath

class Execute:
    def __init__(self, order: Dict[str, Any], user_id: str):
        """
        Initializes the Core Execution Engine with the target order context.
        :param order: The parsed JSON dictionary instruction layout from the LLM.
        :param user_id: The unique sanitized identifier/email of the active user.
        """
        self.order = order
        self.user_id = user_id.strip() if user_id else None

    async def run(self) -> Dict[str, Any]:
        """
        Evaluates the order validation parameters and forwards the payloads 
        to distinct execution workflows based on runtime configuration type keys.
        """
        if not self.order or not isinstance(self.order, dict):
            return {"status": "error", "message": "Execution rejected: Malformed or empty order object."}
            
        order_type = self.order.get("type")

        if order_type == "single":
            return await self._execute_single_order()
            
        return {
            "status": "error", 
            "message": f"Execution rejected: The payload type system mapping '{order_type}' is unhandled."
        }

    async def _execute_single_order(self) -> Dict[str, Any]:
        """
        Internal isolation handler tasked with navigating permissions, path resolutions, 
        and runtime evaluation for self-contained, single-process operations.
        """
        actions = self.order.get("action", [])
        if not actions or not isinstance(actions, list):
            return {"status": "error", "message": "Malformed order: Target execution actions list missing."}

        action_data = actions[0]
        tool_name = action_data.get("tool_name")
        module_name = action_data.get("module")
        class_name = action_data.get("class_name")
        method_name = action_data.get("method")
        raw_parameters = action_data.get("parameters", {})

        # --- STEP 1: SECURITY GATEKEEPING RESOLUTION ---
        gatekeeper = Approval(user_email=self.user_id, tool_name=tool_name)
        is_allowed, usage_msg = await gatekeeper.tool_usage_check()
        
        if not is_allowed:
            return {
                "status": "denied", 
                "reason": f"Privilege Check Failed. Security feedback signature: {usage_msg}"
            }

        # --- STEP 2: MULTI-ZONE PATH RESOLUTIONS FROM REGISTRY ---
        target_filename = raw_parameters.get("file_name")

        locator = LocatePath(
            tool_name=tool_name, 
            user_id=self.user_id, 
            file_name=target_filename
        )

        # Asynchronously discover where the target tool codebase lives
        tool_res = await locator.get_tool_directory()
        if tool_res["status"] == "error":
            return {"status": "error", "message": f"Registry path mapping failed for tool: {tool_res['message']}"}
        tool_absolute_dir = tool_res["absolute_path"]

        # --- STEP 3: CONSTRUCT PARAMETER MATRICES ---
        processed_parameters = raw_parameters.copy()

        # If a file context was specified, swap out its raw string name for its verified storage tracking path
        if target_filename:
            file_res = await locator.get_user_file_directory()
            if file_res["status"] == "error":
                return {"status": "error", "message": f"Registry resource track error: {file_res['message']}"}
            
            processed_parameters["file_path"] = file_res["absolute_path"]
            
            # Remove structural file_name key to prevent arguments mismatch errors on initialization
            if "file_name" in processed_parameters:
                del processed_parameters["file_name"]

        # --- STEP 4: DYNAMIC CODE LOADING ---
        try:
            if tool_absolute_dir not in sys.path:
                sys.path.insert(0, tool_absolute_dir)

            target_module = importlib.import_module(module_name)
        except ModuleNotFoundError as mnf_err:
            return {"status": "error", "message": f"Execution Aborted: The system module file '{module_name}.py' could not be found. {str(mnf_err)}"}

        # --- STEP 5: STRUCTURAL ENTRY EXTRACTION ---
        try:
            target_class = getattr(target_module, class_name)
            class_instance = target_class(**processed_parameters)
            execution_method = getattr(class_instance, method_name)
        except AttributeError as attr_err:
            return {"status": "error", "message": f"Execution Aborted: Structural entry error. Class '{class_name}' or Method '{method_name}' was not discovered. {str(attr_err)}"}

        # --- STEP 6: RUNTIME PROCESS INVOCATION & POST-PROCESSING ---
        try:
            # Fire the tool
            tool_response = await execution_method()

            # If the tool succeeded and returned an output file path, the executor handles workspace placement
            if tool_response.get("status") == "success" and "output_file_path" in tool_response:
                generated_file = tool_response["output_file_path"]
                
                if not os.path.exists(generated_file):
                    return {"status": "error", "message": f"Tool claimed success, but file was not found at: {generated_file}"}

                # Ask registry to fetch/verify the workspace path context
                workspace_res = await locator.prepare_workspace()
                if workspace_res["status"] == "error":
                    return {"status": "error", "message": f"Workspace preparation failed: {workspace_res['message']}"}
                
                workspace_dir = workspace_res["workspace_path"]
                destination_path = os.path.join(workspace_dir, os.path.basename(generated_file))

                # Handle the file move operation safely within a worker thread
                def move_file():
                    if os.path.abspath(generated_file) != os.path.abspath(destination_path):
                        shutil.move(generated_file, destination_path)
                    return destination_path

                final_saved_path = await asyncio.to_thread(move_file)
                
                # Update the final tool response with our structured tracking path
                tool_response["saved_workspace_path"] = final_saved_path

            return {
                "status": "success",
                "execution_signature": f"{tool_name}.{module_name}.{method_name}",
                "tool_output": tool_response
            }

        except Exception as runtime_fault:
            return {"status": "error", "message": f"Runtime exception intercepted within external file thread processing: {str(runtime_fault)}"}