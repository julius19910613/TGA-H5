"""Simplified MCP Server for Schedule Management."""

import asyncio
import json
from typing import Any

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP library not found. Please install with: pip install mcp")
    exit(1)

from .tools.schedule_tools import ScheduleManager


def create_server():
    """Create and configure the MCP server."""
    server = Server("lfc-mcp-scheduler")
    schedule_manager = ScheduleManager()
    
    @server.list_tools()
    async def list_tools():
        """List available tools."""
        return [
            Tool(
                name="create_schedule",
                description="创建新的日程安排",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "日程安排名称"},
                        "description": {"type": "string", "description": "日程安排描述（可选）"}
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="list_schedules",
                description="列出所有日程安排",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="add_event",
                description="添加新的日程事件",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "事件标题"},
                        "start_datetime": {"type": "string", "description": "开始时间 (ISO格式: YYYY-MM-DDTHH:MM:SS)"},
                        "end_datetime": {"type": "string", "description": "结束时间（可选）"},
                        "description": {"type": "string", "description": "事件描述（可选）"},
                        "location": {"type": "string", "description": "事件地点（可选）"},
                        "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "description": "优先级"},
                    },
                    "required": ["title", "start_datetime"]
                }
            ),
            Tool(
                name="get_schedule",
                description="获取日程安排详细信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                    }
                }
            ),
            Tool(
                name="search_events", 
                description="搜索事件",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="export_to_file",
                description="导出日程安排到文件",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "导出文件路径"},
                        "file_type": {"type": "string", "enum": ["excel", "txt", "word"], "description": "文件类型"}
                    },
                    "required": ["file_path", "file_type"]
                }
            ),
            Tool(
                name="import_from_file",
                description="从文件导入日程安排", 
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "文件路径"},
                        "file_type": {"type": "string", "enum": ["excel", "txt", "word"], "description": "文件类型"}
                    },
                    "required": ["file_path", "file_type"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None):
        """Handle tool calls."""
        if arguments is None:
            arguments = {}
        
        try:
            if name == "create_schedule":
                result = schedule_manager.create_schedule(
                    name=arguments["name"],
                    description=arguments.get("description")
                )
            elif name == "list_schedules":
                result = schedule_manager.list_schedules()
            elif name == "add_event":
                result = schedule_manager.add_event(**arguments)
            elif name == "get_schedule":
                result = schedule_manager.get_schedule(arguments.get("schedule_id"))
            elif name == "search_events":
                result = schedule_manager.search_events(
                    query=arguments["query"],
                    schedule_id=arguments.get("schedule_id")
                )
            elif name == "export_to_file":
                result = schedule_manager.export_to_file(
                    file_path=arguments["file_path"],
                    file_type=arguments["file_type"],
                    schedule_id=arguments.get("schedule_id")
                )
            elif name == "import_from_file":
                result = schedule_manager.import_from_file(
                    file_path=arguments["file_path"],
                    file_type=arguments["file_type"]
                )
            else:
                result = {"success": False, "message": f"未知工具: {name}"}
            
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        
        except Exception as e:
            error_result = {"success": False, "message": f"执行工具时出错: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2))]
    
    return server


async def main():
    """Main server entry point."""
    server = create_server()
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())