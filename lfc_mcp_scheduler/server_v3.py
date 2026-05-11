"""MCP Server v3 - Simplified and working version"""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .tools.schedule_tools import ScheduleManager


# Create server and schedule manager
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
            name="switch_schedule",
            description="切换到指定的日程安排",
            inputSchema={
                "type": "object",
                "properties": {
                    "schedule_id": {"type": "string", "description": "日程安排ID"}
                },
                "required": ["schedule_id"]
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
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "事件标签"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "参与者"},
                    "notes": {"type": "string", "description": "备注"},
                    "repeat_type": {"type": "string", "enum": ["none", "daily", "weekly", "monthly", "yearly"], "description": "重复类型"},
                    "repeat_until": {"type": "string", "description": "重复结束日期"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["title", "start_datetime"]
            }
        ),
        Tool(
            name="update_event",
            description="更新现有事件",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "事件ID"},
                    "title": {"type": "string", "description": "事件标题"},
                    "start_datetime": {"type": "string", "description": "开始时间"},
                    "end_datetime": {"type": "string", "description": "结束时间"},
                    "description": {"type": "string", "description": "事件描述"},
                    "location": {"type": "string", "description": "事件地点"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "cancelled"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "attendees": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string", "description": "备注"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="delete_event",
            description="删除事件",
            inputSchema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "事件ID"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["event_id"]
            }
        ),
        Tool(
            name="get_events_by_date",
            description="获取指定日期的所有事件",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "日期 (ISO格式: YYYY-MM-DD)"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="get_events_by_date_range",
            description="获取指定日期范围内的所有事件",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "开始日期"},
                    "end_date": {"type": "string", "description": "结束日期"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["start_date", "end_date"]
            }
        ),
        Tool(
            name="search_events",
            description="搜索事件",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
                },
                "required": ["query"]
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
        ),
        Tool(
            name="export_to_file",
            description="导出日程安排到文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "导出文件路径"},
                    "file_type": {"type": "string", "enum": ["excel", "txt", "word"], "description": "文件类型"},
                    "schedule_id": {"type": "string", "description": "日程安排ID（可选）"}
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
        elif name == "switch_schedule":
            result = schedule_manager.switch_schedule(arguments["schedule_id"])
        elif name == "get_schedule":
            result = schedule_manager.get_schedule(arguments.get("schedule_id"))
        elif name == "add_event":
            result = schedule_manager.add_event(**arguments)
        elif name == "update_event":
            result = schedule_manager.update_event(**arguments)
        elif name == "delete_event":
            result = schedule_manager.delete_event(
                event_id=arguments["event_id"],
                schedule_id=arguments.get("schedule_id")
            )
        elif name == "get_events_by_date":
            result = schedule_manager.get_events_by_date(
                target_date=arguments["date"],
                schedule_id=arguments.get("schedule_id")
            )
        elif name == "get_events_by_date_range":
            result = schedule_manager.get_events_by_date_range(
                start_date=arguments["start_date"],
                end_date=arguments["end_date"],
                schedule_id=arguments.get("schedule_id")
            )
        elif name == "search_events":
            result = schedule_manager.search_events(
                query=arguments["query"],
                schedule_id=arguments.get("schedule_id")
            )
        elif name == "import_from_file":
            result = schedule_manager.import_from_file(
                file_path=arguments["file_path"],
                file_type=arguments["file_type"]
            )
        elif name == "export_to_file":
            result = schedule_manager.export_to_file(
                file_path=arguments["file_path"],
                file_type=arguments["file_type"],
                schedule_id=arguments.get("schedule_id")
            )
        else:
            result = {"success": False, "message": f"未知工具: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    except Exception as e:
        error_result = {"success": False, "message": f"执行工具时出错: {str(e)}"}
        return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2))]


async def main():
    """Main server entry point."""
    from mcp.server import NotificationOptions
    
    # Create initialization options
    notification_options = NotificationOptions()
    init_options = InitializationOptions(
        server_name="lfc-mcp-scheduler",
        server_version="0.1.0",
        capabilities=server.get_capabilities(
            notification_options=notification_options,
            experimental_capabilities=None
        )
    )
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())