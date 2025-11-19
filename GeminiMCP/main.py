from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
import uvicorn

# Import the tool registry from our new module
from tools.system import TOOL_REGISTRY as SYSTEM_TOOLS

app = FastAPI(
    title="GeminiMCP Server",
    description="A dedicated MCP server for Gemini, providing a suite of powerful tools.",
    version="0.1.0",
)

# Combine all tool registries here
MASTER_TOOL_REGISTRY = {**SYSTEM_TOOLS}

class ToolInvocationRequest(BaseModel):
    params: dict

@app.get("/")
async def read_root():
    """A simple endpoint to confirm the server is running."""
    return {"message": "Welcome to GeminiMCP!"}

@app.get("/tools")
async def list_tools():
    """Lists all available tools with their descriptions and input schemas."""
    return {
        name: {
            "description": details["description"],
            "schema": details["request_model"].schema()
        }
        for name, details in MASTER_TOOL_REGISTRY.items()
    }

@app.post("/invoke_tool/{tool_name}")
async def invoke_tool(tool_name: str, request: ToolInvocationRequest):
    """Invokes a specified tool with the given parameters."""
    if tool_name not in MASTER_TOOL_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")
    
    tool_details = MASTER_TOOL_REGISTRY[tool_name]
    tool_function = tool_details["function"]
    RequestModel = tool_details["request_model"]
    
    try:
        # Create an instance of the Pydantic model from the request params
        # This automatically handles validation.
        parsed_request = RequestModel(**request.params)
        
        # Call the tool function with the validated request model
        result = tool_function(parsed_request)
        return {"tool": tool_name, "result": result}
    except ValidationError as e:
        # If validation fails, return a 422 error with details
        raise HTTPException(status_code=422, detail={"errors": e.errors()})
    except Exception as e:
        # For any other errors during tool execution
        raise HTTPException(status_code=500, detail=f"Error invoking tool '{tool_name}': {str(e)}")

if __name__ == "__main__":
    # The Docker CMD will run this, but this is good for local testing if needed.
    uvicorn.run(app, host="0.0.0.0", port=8001)
