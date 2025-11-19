"""Main entry point for CursorMCP"""

import asyncio
from .server.mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())

