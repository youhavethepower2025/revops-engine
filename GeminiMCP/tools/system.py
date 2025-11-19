import os
from pydantic import BaseModel

class ListDirectoryRequest(BaseModel):
    path: str = "."

def list_directory(request: ListDirectoryRequest):
    """Lists the contents of a specified directory."""
    path = request.path
    if not os.path.isdir(path):
        return {"error": f"Path '{path}' is not a valid directory."}
    
    try:
        items = os.listdir(path)
        return {"directory": path, "contents": items}
    except Exception as e:
        return {"error": str(e)}

# Example of how you might want to register the tool
TOOL_REGISTRY = {
    "list_directory": {
        "function": list_directory,
        "request_model": ListDirectoryRequest,
        "description": "Lists the names of files and subdirectories in a specified directory."
    }
}
