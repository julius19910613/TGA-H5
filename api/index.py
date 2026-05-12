"""Vercel Serverless Function — LFC Schedule MCP Server.

This is the entry point for Vercel's Python runtime.
It creates a FastMCP server backed by Neon Postgres and
exposes it as an ASGI app via http_app().
"""

import json
import os
import uuid
from fastmcp import FastMCP
from .db import (
    init_db,
    create_schedule as _db_create_schedule,
    list_schedules as _db_list_schedules,
    switch_schedule as _db_switch_schedule,
    get_schedule as _db_get_schedule,
    add_event as _db_add_event,
    update_event as _db_update_event,
    delete_event as _db_delete_event,
    get_events_by_date as _db_get_events_by_date,
    get_events_by_date_range as _db_get_events_by_date_range,
    search_events as _db_search_events,
    delete_schedule as _db_delete_schedule,
)

# ─── FastMCP Server ──────────────────────────────────────────────
mcp = FastMCP("lfc-mcp-scheduler")


@mcp.tool()
async def create_schedule(name: str, description: str = "") -> str:
    """创建新的日程安排"""
    schedule_id = f"schedule_{uuid.uuid4().hex[:8]}"
    result = await _db_create_schedule(schedule_id, name, description or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_schedules() -> str:
    """列出所有日程安排"""
    result = await _db_list_schedules()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def switch_schedule(schedule_id: str) -> str:
    """切换到指定的日程安排"""
    result = await _db_switch_schedule(schedule_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_schedule(schedule_id: str = "") -> str:
    """获取日程安排详细信息"""
    result = await _db_get_schedule(schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def add_event(
    title: str,
    start_datetime: str,
    end_datetime: str = "",
    description: str = "",
    location: str = "",
    priority: str = "medium",
    tags: list[str] = [],
    attendees: list[str] = [],
    notes: str = "",
    repeat_type: str = "none",
    repeat_until: str = "",
    schedule_id: str = "",
) -> str:
    """添加新的日程事件

    Args:
        title: 事件标题
        start_datetime: 开始时间 (ISO格式: YYYY-MM-DDTHH:MM:SS)
        end_datetime: 结束时间（可选）
        description: 事件描述（可选）
        location: 事件地点（可选）
        priority: 优先级 (low/medium/high/urgent)
        tags: 事件标签
        attendees: 参与者
        notes: 备注
        repeat_type: 重复类型 (none/daily/weekly/monthly/yearly)
        repeat_until: 重复结束日期
        schedule_id: 日程安排ID（可选，默认使用当前日程）
    """
    # Resolve schedule_id
    sid = schedule_id or None
    if not sid:
        from .db import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if row:
                sid = row["id"]

    if not sid:
        return json.dumps({"success": False, "message": "未选择日程安排"}, ensure_ascii=False)

    event_id = f"event_{uuid.uuid4().hex[:8]}"
    result = await _db_add_event(
        event_id=event_id,
        schedule_id=sid,
        title=title,
        start_datetime=start_datetime,
        end_datetime=end_datetime or None,
        description=description or None,
        location=location or None,
        priority=priority,
        tags=tags or [],
        attendees=attendees or [],
        notes=notes or None,
        repeat_type=repeat_type,
        repeat_until=repeat_until or None,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def update_event(
    event_id: str,
    title: str = "",
    start_datetime: str = "",
    end_datetime: str = "",
    description: str = "",
    location: str = "",
    priority: str = "",
    status: str = "",
    tags: list[str] = [],
    attendees: list[str] = [],
    notes: str = "",
    schedule_id: str = "",
) -> str:
    """更新现有事件"""
    kwargs = {}
    if title: kwargs["title"] = title
    if start_datetime: kwargs["start_datetime"] = start_datetime
    if end_datetime: kwargs["end_datetime"] = end_datetime
    if description: kwargs["description"] = description
    if location: kwargs["location"] = location
    if priority: kwargs["priority"] = priority
    if status: kwargs["status"] = status
    if tags: kwargs["tags"] = tags
    if attendees: kwargs["attendees"] = attendees
    if notes: kwargs["notes"] = notes

    result = await _db_update_event(event_id, schedule_id or None, **kwargs)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def remove_event(event_id: str, schedule_id: str = "") -> str:
    """删除事件"""
    result = await _db_delete_event(event_id, schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_events_by_date(date: str, schedule_id: str = "") -> str:
    """获取指定日期的所有事件

    Args:
        date: 日期 (ISO格式: YYYY-MM-DD)
        schedule_id: 日程安排ID（可选）
    """
    result = await _db_get_events_by_date(date, schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_events_by_date_range(start_date: str, end_date: str, schedule_id: str = "") -> str:
    """获取指定日期范围内的所有事件"""
    result = await _db_get_events_by_date_range(start_date, end_date, schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_events(query: str, schedule_id: str = "") -> str:
    """搜索事件（按标题、描述、地点匹配）"""
    result = await _db_search_events(query, schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def delete_schedule(schedule_id: str) -> str:
    """删除日程安排"""
    result = await _db_delete_schedule(schedule_id)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_today_events(schedule_id: str = "") -> str:
    """获取今天的所有事件"""
    from datetime import date
    today = date.today().isoformat()
    result = await _db_get_events_by_date(today, schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_upcoming_events(schedule_id: str = "") -> str:
    """获取未来7天的事件"""
    from datetime import date, timedelta
    today = date.today()
    end = today + timedelta(days=7)
    result = await _db_get_events_by_date_range(today.isoformat(), end.isoformat(), schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_events(schedule_id: str = "") -> str:
    """列出当前日程安排的所有事件"""
    result = await _db_get_schedule(schedule_id or None)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def import_schedule(file_path: str, file_type: str) -> str:
    """从文件导入日程安排

    Args:
        file_path: 文件路径
        file_type: 文件类型 (excel/txt/word)
    """
    # File-based import is not supported in serverless environment
    return json.dumps({
        "success": False,
        "message": "文件导入功能在Serverless环境中不可用，请使用API直接添加事件"
    }, ensure_ascii=False, indent=2)


@mcp.tool()
async def export_schedule(file_path: str, file_type: str, schedule_id: str = "") -> str:
    """导出日程安排到文件

    Args:
        file_path: 导出文件路径
        file_type: 文件类型 (excel/txt/word)
        schedule_id: 日程安排ID（可选）
    """
    # File-based export is not supported in serverless environment
    return json.dumps({
        "success": False,
        "message": "文件导出功能在Serverless环境中不可用，请使用get_schedule获取数据"
    }, ensure_ascii=False, indent=2)


# ─── ASGI App for Vercel ─────────────────────────────────────────
from contextlib import asynccontextmanager
from starlette.applications import Starlette

# FastMCP 3.x http_app() returns a Starlette ASGI app with /mcp endpoint
http_app = mcp.http_app(stateless_http=True, json_response=True)


@asynccontextmanager
async def lifespan(app_instance):
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        await init_db()
    async with http_app.lifespan(app_instance):
        yield


# Build the final app with combined lifespan and export as `app` for Vercel
app = Starlette(
    lifespan=lifespan,
    routes=http_app.routes,
)
