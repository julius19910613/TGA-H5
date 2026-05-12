"""Database layer using asyncpg + Neon Postgres for Vercel deployment."""

import os
import json
import asyncpg
from typing import Optional, Dict, Any, List
from datetime import datetime, date


# Global pool — reused across Vercel cold starts
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        _pool = await asyncpg.create_pool(
            database_url,
            min_size=1,
            max_size=5,
            # Neon requires SSL
            ssl="require",
        )
    return _pool


async def init_db():
    """Create tables if they don't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                is_current BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                schedule_id TEXT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT,
                start_datetime TIMESTAMPTZ NOT NULL,
                end_datetime TIMESTAMPTZ,
                location TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                tags JSONB DEFAULT '[]',
                repeat_type TEXT DEFAULT 'none',
                repeat_until DATE,
                attendees JSONB DEFAULT '[]',
                notes TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );

            CREATE INDEX IF NOT EXISTS idx_events_schedule_id ON events(schedule_id);
            CREATE INDEX IF NOT EXISTS idx_events_start_datetime ON events(start_datetime);
        """)


# ─── Schedule CRUD ───────────────────────────────────────────────

async def create_schedule(schedule_id: str, name: str, description: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Unset any current schedule
        await conn.execute("UPDATE schedules SET is_current = FALSE WHERE is_current = TRUE")
        await conn.execute(
            "INSERT INTO schedules (id, name, description, is_current) VALUES ($1, $2, $3, TRUE)",
            schedule_id, name, description
        )
    return {"success": True, "schedule_id": schedule_id, "message": f"创建日程安排 '{name}' 成功"}


async def list_schedules() -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, description, is_current, created_at, updated_at FROM schedules ORDER BY created_at"
        )
        # Get event counts
        counts = await conn.fetch(
            "SELECT schedule_id, COUNT(*) as cnt FROM events GROUP BY schedule_id"
        )
        count_map = {r["schedule_id"]: r["cnt"] for r in counts}
        current_id = None
        schedules_info = []
        for r in rows:
            if r["is_current"]:
                current_id = r["id"]
            schedules_info.append({
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "event_count": count_map.get(r["id"], 0),
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            })
    return {"success": True, "schedules": schedules_info, "current_schedule": current_id}


async def switch_schedule(schedule_id: str) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name FROM schedules WHERE id = $1", schedule_id)
        if not row:
            return {"success": False, "message": "未找到指定的日程安排"}
        await conn.execute("UPDATE schedules SET is_current = FALSE WHERE is_current = TRUE")
        await conn.execute("UPDATE schedules SET is_current = TRUE WHERE id = $1", schedule_id)
    return {"success": True, "message": f"已切换到日程安排: {row['name']}"}


async def get_schedule(schedule_id: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not schedule_id:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if not row:
                return {"success": False, "message": "未找到当前的日程安排"}
            schedule_id = row["id"]

        sched = await conn.fetchrow("SELECT * FROM schedules WHERE id = $1", schedule_id)
        if not sched:
            return {"success": False, "message": "未找到指定的日程安排"}

        events = await conn.fetch(
            "SELECT * FROM events WHERE schedule_id = $1 ORDER BY start_datetime", schedule_id
        )
        event_list = [_row_to_event(e) for e in events]

    return {
        "success": True,
        "schedule": {
            "name": sched["name"],
            "description": sched["description"],
            "events": event_list,
            "created_at": sched["created_at"].isoformat() if sched["created_at"] else None,
            "updated_at": sched["updated_at"].isoformat() if sched["updated_at"] else None,
        }
    }


# ─── Event CRUD ──────────────────────────────────────────────────

async def add_event(
    event_id: str, schedule_id: str, title: str, start_datetime: str,
    end_datetime: Optional[str] = None, description: Optional[str] = None,
    location: Optional[str] = None, priority: str = "medium",
    tags: Optional[List[str]] = None, attendees: Optional[List[str]] = None,
    notes: Optional[str] = None, repeat_type: str = "none",
    repeat_until: Optional[str] = None
) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verify schedule exists
        row = await conn.fetchrow("SELECT id FROM schedules WHERE id = $1", schedule_id)
        if not row:
            return {"success": False, "message": "未选择日程安排"}

        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = None
        if end_datetime:
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        repeat_until_date = None
        if repeat_until:
            repeat_until_date = date.fromisoformat(repeat_until)

        await conn.execute(
            """INSERT INTO events 
               (id, schedule_id, title, description, start_datetime, end_datetime,
                location, priority, status, tags, repeat_type, repeat_until, attendees, notes)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', $9::jsonb, $10, $11, $12::jsonb, $13)
            """,
            event_id, schedule_id, title, description, start_dt, end_dt,
            location, priority, json.dumps(tags or []), repeat_type,
            repeat_until_date, json.dumps(attendees or []), notes
        )
        await conn.execute("UPDATE schedules SET updated_at = NOW() WHERE id = $1", schedule_id)
    return {"success": True, "event_id": event_id, "message": f"成功添加事件: {title}"}


async def update_event(event_id: str, schedule_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not schedule_id:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if row:
                schedule_id = row["id"]

        # Build SET clause dynamically
        sets = []
        values = []
        idx = 1
        for field, value in kwargs.items():
            if value is None:
                continue
            idx += 1
            if field in ('start_datetime', 'end_datetime'):
                sets.append(f"{field} = ${idx}")
                values.append(datetime.fromisoformat(value.replace('Z', '+00:00')))
            elif field == 'repeat_until':
                sets.append(f"{field} = ${idx}")
                values.append(date.fromisoformat(value))
            elif field in ('tags', 'attendees'):
                sets.append(f"{field} = ${idx}::jsonb")
                values.append(json.dumps(value))
            else:
                sets.append(f"{field} = ${idx}")
                values.append(value)

        if not sets:
            return {"success": False, "message": "没有需要更新的字段"}

        idx += 1
        sets.append(f"updated_at = NOW()")
        # Filter by schedule_id if provided
        if schedule_id:
            idx += 1
            where = f"id = ${idx} AND schedule_id = ${idx + 1}"
            values.extend([event_id, schedule_id])
        else:
            idx += 1
            where = f"id = ${idx}"
            values.append(event_id)

        result = await conn.execute(
            f"UPDATE events SET {', '.join(sets)} WHERE {where}",
            *values
        )
        if result == "UPDATE 0":
            return {"success": False, "message": "未找到指定的事件"}

    return {"success": True, "message": f"成功更新事件"}


async def delete_event(event_id: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if schedule_id:
            result = await conn.execute(
                "DELETE FROM events WHERE id = $1 AND schedule_id = $2",
                event_id, schedule_id
            )
        else:
            result = await conn.execute("DELETE FROM events WHERE id = $1", event_id)
        if result == "DELETE 0":
            return {"success": False, "message": "未找到指定的事件"}
    return {"success": True, "message": "成功删除事件"}


async def delete_schedule(schedule_id: str) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT name FROM schedules WHERE id = $1", schedule_id)
        if not row:
            return {"success": False, "message": "未找到指定的日程安排"}
        await conn.execute("DELETE FROM schedules WHERE id = $1", schedule_id)
    return {"success": True, "message": f"成功删除日程安排: {row['name']}"}


async def get_events_by_date(target_date: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not schedule_id:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if row:
                schedule_id = row["id"]

        date_obj = date.fromisoformat(target_date)
        rows = await conn.fetch(
            """SELECT * FROM events 
               WHERE schedule_id = $1 AND start_datetime::date = $2
               ORDER BY start_datetime""",
            schedule_id, date_obj
        )
    return {
        "success": True,
        "date": target_date,
        "events": [_row_to_event(r) for r in rows]
    }


async def get_events_by_date_range(start_date: str, end_date: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not schedule_id:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if row:
                schedule_id = row["id"]

        start_obj = date.fromisoformat(start_date)
        end_obj = date.fromisoformat(end_date)
        rows = await conn.fetch(
            """SELECT * FROM events 
               WHERE schedule_id = $1 AND start_datetime::date BETWEEN $2 AND $3
               ORDER BY start_datetime""",
            schedule_id, start_obj, end_obj
        )
    return {
        "success": True,
        "start_date": start_date,
        "end_date": end_date,
        "events": [_row_to_event(r) for r in rows]
    }


async def search_events(query: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        if not schedule_id:
            row = await conn.fetchrow("SELECT id FROM schedules WHERE is_current = TRUE")
            if row:
                schedule_id = row["id"]

        pattern = f"%{query}%"
        rows = await conn.fetch(
            """SELECT * FROM events 
               WHERE schedule_id = $1 
               AND (title ILIKE $2 OR description ILIKE $2 OR location ILIKE $2)
               ORDER BY start_datetime""",
            schedule_id, pattern
        )
    return {
        "success": True,
        "query": query,
        "events": [_row_to_event(r) for r in rows],
        "count": len(rows)
    }


def _row_to_event(r: asyncpg.Record) -> Dict[str, Any]:
    """Convert a database row to an event dict."""
    return {
        "id": r["id"],
        "title": r["title"],
        "description": r["description"],
        "start_datetime": r["start_datetime"].isoformat() if r["start_datetime"] else None,
        "end_datetime": r["end_datetime"].isoformat() if r["end_datetime"] else None,
        "location": r["location"],
        "priority": r["priority"],
        "status": r["status"],
        "tags": json.loads(r["tags"]) if isinstance(r["tags"], str) else (r["tags"] or []),
        "repeat_type": r["repeat_type"],
        "repeat_until": r["repeat_until"].isoformat() if r["repeat_until"] else None,
        "attendees": json.loads(r["attendees"]) if isinstance(r["attendees"], str) else (r["attendees"] or []),
        "notes": r["notes"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
    }
