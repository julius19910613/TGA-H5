"""Schedule management tools for MCP server."""

import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models.schedule import Schedule, ScheduleEvent, Priority, EventStatus, RepeatType
from ..utils.file_handlers import ExcelHandler, TxtHandler, WordHandler


class ScheduleManager:
    """Main schedule management class."""
    
    def __init__(self):
        self.schedules: Dict[str, Schedule] = {}
        self.current_schedule_id: Optional[str] = None
    
    def create_schedule(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new schedule."""
        import uuid
        schedule_id = f"schedule_{uuid.uuid4().hex[:8]}"
        schedule = Schedule(name=name, description=description)
        self.schedules[schedule_id] = schedule
        self.current_schedule_id = schedule_id
        
        return {
            "success": True,
            "schedule_id": schedule_id,
            "message": f"创建日程安排 '{name}' 成功"
        }
    
    def get_schedule(self, schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Get schedule information."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未找到指定的日程安排"}
        
        schedule = self.schedules[schedule_id]
        return {
            "success": True,
            "schedule": schedule.to_dict()
        }
    
    def list_schedules(self) -> Dict[str, Any]:
        """List all schedules."""
        schedules_info = []
        for schedule_id, schedule in self.schedules.items():
            schedules_info.append({
                "id": schedule_id,
                "name": schedule.name,
                "description": schedule.description,
                "event_count": len(schedule.events),
                "created_at": schedule.created_at.isoformat(),
                "updated_at": schedule.updated_at.isoformat()
            })
        
        return {
            "success": True,
            "schedules": schedules_info,
            "current_schedule": self.current_schedule_id
        }
    
    def switch_schedule(self, schedule_id: str) -> Dict[str, Any]:
        """Switch to a different schedule."""
        if schedule_id not in self.schedules:
            return {"success": False, "message": "未找到指定的日程安排"}
        
        self.current_schedule_id = schedule_id
        return {
            "success": True,
            "message": f"已切换到日程安排: {self.schedules[schedule_id].name}"
        }
    
    def add_event(self, title: str, start_datetime: str, end_datetime: Optional[str] = None,
                  description: Optional[str] = None, location: Optional[str] = None,
                  priority: str = "medium", tags: Optional[List[str]] = None,
                  attendees: Optional[List[str]] = None, notes: Optional[str] = None,
                  repeat_type: str = "none", repeat_until: Optional[str] = None,
                  schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Add a new event to the schedule."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        try:
            # Parse datetime strings
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = None
            if end_datetime:
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
            repeat_until_date = None
            if repeat_until:
                repeat_until_date = datetime.fromisoformat(repeat_until).date()
            
            event = ScheduleEvent(
                title=title,
                description=description,
                start_datetime=start_dt,
                end_datetime=end_dt,
                location=location,
                priority=Priority(priority),
                tags=tags or [],
                attendees=attendees or [],
                notes=notes,
                repeat_type=RepeatType(repeat_type),
                repeat_until=repeat_until_date
            )
            
            self.schedules[schedule_id].add_event(event)
            
            return {
                "success": True,
                "event_id": event.id,
                "message": f"成功添加事件: {title}"
            }
        
        except Exception as e:
            return {"success": False, "message": f"添加事件失败: {str(e)}"}
    
    def update_event(self, event_id: str, schedule_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Update an existing event."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        schedule = self.schedules[schedule_id]
        event = schedule.get_event(event_id)
        
        if not event:
            return {"success": False, "message": "未找到指定的事件"}
        
        try:
            # Update event fields
            for field, value in kwargs.items():
                if hasattr(event, field) and value is not None:
                    if field in ['start_datetime', 'end_datetime']:
                        setattr(event, field, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    elif field == 'repeat_until':
                        setattr(event, field, datetime.fromisoformat(value).date())
                    elif field == 'priority':
                        setattr(event, field, Priority(value))
                    elif field == 'status':
                        setattr(event, field, EventStatus(value))
                    elif field == 'repeat_type':
                        setattr(event, field, RepeatType(value))
                    else:
                        setattr(event, field, value)
            
            event.updated_at = datetime.now()
            schedule.updated_at = datetime.now()
            
            return {
                "success": True,
                "message": f"成功更新事件: {event.title}"
            }
        
        except Exception as e:
            return {"success": False, "message": f"更新事件失败: {str(e)}"}
    
    def delete_event(self, event_id: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Delete an event."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        schedule = self.schedules[schedule_id]
        if schedule.remove_event(event_id):
            return {
                "success": True,
                "message": "成功删除事件"
            }
        else:
            return {"success": False, "message": "未找到指定的事件"}
    
    def get_events_by_date(self, target_date: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Get events for a specific date."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        try:
            date_obj = datetime.fromisoformat(target_date).date()
            schedule = self.schedules[schedule_id]
            events = schedule.get_events_by_date(date_obj)
            
            return {
                "success": True,
                "date": target_date,
                "events": [event.to_dict() for event in events]
            }
        
        except Exception as e:
            return {"success": False, "message": f"获取日期事件失败: {str(e)}"}
    
    def get_events_by_date_range(self, start_date: str, end_date: str, 
                                schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Get events within a date range."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        try:
            start_date_obj = datetime.fromisoformat(start_date).date()
            end_date_obj = datetime.fromisoformat(end_date).date()
            
            schedule = self.schedules[schedule_id]
            events = schedule.get_events_by_date_range(start_date_obj, end_date_obj)
            
            return {
                "success": True,
                "start_date": start_date,
                "end_date": end_date,
                "events": [event.to_dict() for event in events]
            }
        
        except Exception as e:
            return {"success": False, "message": f"获取日期范围事件失败: {str(e)}"}
    
    def import_from_file(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Import schedule from file."""
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"success": False, "message": "文件不存在"}
            
            if file_type.lower() == "excel" or file_path.endswith(('.xlsx', '.xls')):
                schedule = ExcelHandler.import_from_excel(file_path)
            elif file_type.lower() == "txt" or file_path.endswith('.txt'):
                schedule = TxtHandler.import_from_txt(file_path)
            elif file_type.lower() == "word" or file_path.endswith(('.docx', '.doc')):
                schedule = WordHandler.import_from_word(file_path)
            else:
                return {"success": False, "message": "不支持的文件类型"}
            
            schedule_id = f"imported_{int(datetime.now().timestamp())}"
            self.schedules[schedule_id] = schedule
            self.current_schedule_id = schedule_id
            
            return {
                "success": True,
                "schedule_id": schedule_id,
                "message": f"成功导入 {len(schedule.events)} 个事件",
                "events_count": len(schedule.events)
            }
        
        except Exception as e:
            return {"success": False, "message": f"导入文件失败: {str(e)}"}
    
    def export_to_file(self, file_path: str, file_type: str, 
                      schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Export schedule to file."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        try:
            schedule = self.schedules[schedule_id]
            
            if file_type.lower() == "excel" or file_path.endswith(('.xlsx', '.xls')):
                ExcelHandler.export_to_excel(schedule, file_path)
            elif file_type.lower() == "txt" or file_path.endswith('.txt'):
                TxtHandler.export_to_txt(schedule, file_path)
            elif file_type.lower() == "word" or file_path.endswith(('.docx', '.doc')):
                WordHandler.export_to_word(schedule, file_path)
            else:
                return {"success": False, "message": "不支持的文件类型"}
            
            return {
                "success": True,
                "message": f"成功导出到 {file_path}",
                "events_count": len(schedule.events)
            }
        
        except Exception as e:
            return {"success": False, "message": f"导出文件失败: {str(e)}"}
    
    def search_events(self, query: str, schedule_id: Optional[str] = None) -> Dict[str, Any]:
        """Search events by title, description, or location."""
        if not schedule_id:
            schedule_id = self.current_schedule_id
        
        if not schedule_id or schedule_id not in self.schedules:
            return {"success": False, "message": "未选择日程安排"}
        
        schedule = self.schedules[schedule_id]
        query_lower = query.lower()
        
        matching_events = []
        for event in schedule.events:
            if (query_lower in event.title.lower() or
                (event.description and query_lower in event.description.lower()) or
                (event.location and query_lower in event.location.lower()) or
                any(query_lower in tag.lower() for tag in event.tags)):
                matching_events.append(event.to_dict())
        
        return {
            "success": True,
            "query": query,
            "events": matching_events,
            "count": len(matching_events)
        }