"""MCP Bridge — stdio→HTTP bridge for local Claude Code / Claude Desktop.

This script runs as a local stdio MCP server, forwarding all
tool calls to the remote Vercel-hosted MCP server via HTTP.

Usage:
    python bridge.py <endpoint_url>

Example .mcp.json:
    {
      "mcpServers": {
        "lfc-scheduler": {
          "command": "python3",
          "args": ["bridge.py", "https://your-app.vercel.app"]
        }
      }
    }
"""

import argparse
import asyncio
import json
import sys
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bridge MCP requests to a remote MCP server")
    parser.add_argument("endpoint", help="Remote MCP server URL (e.g. https://your-app.vercel.app)")
    parser.add_argument("--api-key", help="API key for authentication", default=None)
    return parser.parse_args()


class RemoteMCPBridge:
    def __init__(self, endpoint: str, api_key: Optional[str] = None):
        self.endpoint = endpoint.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)
        self.api_key = api_key

    async def forward_request(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        request_data = {"jsonrpc": "2.0", "method": method, "id": 1}
        if params:
            request_data["params"] = params

        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            url = f"{self.endpoint}/mcp"
            response = await self.client.post(url, json=request_data, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Bridge error: {str(e)}"},
                "id": 1,
            }


async def main():
    args = parse_arguments()
    bridge = RemoteMCPBridge(args.endpoint, args.api_key)

    # Extract server name from URL
    from urllib.parse import urlparse
    hostname = urlparse(args.endpoint).hostname or "remote"
    server_name = hostname.replace(".", "_").replace("-", "_")

    server = Server(server_name)

    @server.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        try:
            response = await bridge.forward_request("tools/list")
            if "result" in response and "tools" in response["result"]:
                tools = []
                for tool_data in response["result"]["tools"]:
                    tools.append(
                        types.Tool(
                            name=tool_data["name"],
                            description=tool_data.get("description", ""),
                            inputSchema=tool_data.get("inputSchema", {}),
                        )
                    )
                print(f"Loaded {len(tools)} tools from {args.endpoint}", file=sys.stderr)
                return tools
            return []
        except Exception as e:
            print(f"Error listing tools: {e}", file=sys.stderr)
            return []

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: Dict[str, Any]
    ) -> List[types.TextContent]:
        try:
            response = await bridge.forward_request(
                "tools/call", {"name": name, "arguments": arguments}
            )
            if "result" in response:
                result = response["result"]
                content_items = []
                for content in result.get("content", []):
                    if content.get("type") == "text":
                        content_items.append(
                            types.TextContent(type="text", text=content["text"])
                        )
                return content_items or [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]
            elif "error" in response:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: {response['error'].get('message', 'Unknown error')}",
                    )
                ]
            return [types.TextContent(type="text", text="Unknown response format")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Bridge error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print(f"MCP Bridge → {args.endpoint}", file=sys.stderr)
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=server_name,
                server_version="0.1.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=True)
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
