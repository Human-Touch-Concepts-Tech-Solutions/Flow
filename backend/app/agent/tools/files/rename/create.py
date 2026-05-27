import os
import shutil

class CreateRename:
    def __init__(self, file_path: str, new_name: str):
        """
        Pure parameters. Works on a source file path and creates a new target file.
        """
        self.file_path = file_path
        self.new_name = new_name

    async def rename_file(self) -> dict:
        """
        Copies the file to a new name in the same directory, keeping the source intact.
        """
        if not os.path.exists(self.file_path):
            return {"status": "error", "message": f"File not found: {self.file_path}"}

        # Find where the uploaded file lives
        file_dir = os.path.dirname(self.file_path)
        # Create the new renamed file path right next to it temporarily
        new_file_path = os.path.join(file_dir, self.new_name)

        try:
            # CRITICAL FIX: Use copy instead of rename so original uploads are never lost!
            shutil.copy(self.file_path, new_file_path)
            
            return {
                "status": "success",
                "output_file_path": new_file_path
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}