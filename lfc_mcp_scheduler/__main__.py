"""LFC MCP Scheduler - Entry point for python -m lfc_mcp_scheduler"""
import asyncio
from lfc_mcp_scheduler.server_v3 import main

if __name__ == "__main__":
    asyncio.run(main())
