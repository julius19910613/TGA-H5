"""Schedule data models."""

from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class Priority(str, Enum):
    """Event priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class EventStatus(str, Enum):
    """Event status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RepeatType(str, Enum):
    """Repeat pattern types."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class ScheduleEvent(BaseModel):
    """A single schedule event."""
    
    id: Optional[str] = None
    title: str = Field(..., description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    start_datetime: datetime = Field(..., description="Event start date and time")
    end_datetime: Optional[datetime] = Field(None, description="Event end date and time")
    location: Optional[str] = Field(None, description="Event location")
    priority: Priority = Field(Priority.MEDIUM, description="Event priority")
    status: EventStatus = Field(EventStatus.PENDING, description="Event status")
    tags: List[str] = Field(default_factory=list, description="Event tags")
    repeat_type: RepeatType = Field(RepeatType.NONE, description="Repeat pattern")
    repeat_until: Optional[date] = Field(None, description="Repeat end date")
    attendees: List[str] = Field(default_factory=list, description="Event attendees")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('end_datetime')
    @classmethod
    def validate_end_datetime(cls, v, info):
        """Ensure end datetime is after start datetime."""
        if v and 'start_datetime' in info.data and v <= info.data['start_datetime']:
            raise ValueError('End datetime must be after start datetime')
        return v
    
    @field_validator('repeat_until')
    @classmethod  
    def validate_repeat_until(cls, v, info):
        """Ensure repeat_until is set only when repeat_type is not NONE."""
        if v and info.data.get('repeat_type') == RepeatType.NONE:
            raise ValueError('repeat_until can only be set when repeat_type is not NONE')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleEvent':
        """Create from dictionary."""
        return cls(**data)


class Schedule(BaseModel):
    """A collection of schedule events."""
    
    name: str = Field(..., description="Schedule name")
    description: Optional[str] = Field(None, description="Schedule description")
    events: List[ScheduleEvent] = Field(default_factory=list, description="Schedule events")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_event(self, event: ScheduleEvent) -> None:
        """Add an event to the schedule."""
        if not event.id:
            import uuid
            event.id = f"event_{uuid.uuid4().hex[:8]}"
        self.events.append(event)
        self.updated_at = datetime.now()
    
    def remove_event(self, event_id: str) -> bool:
        """Remove an event by ID."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                del self.events[i]
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_event(self, event_id: str) -> Optional[ScheduleEvent]:
        """Get an event by ID."""
        for event in self.events:
            if event.id == event_id:
                return event
        return None
    
    def get_events_by_date(self, target_date: date) -> List[ScheduleEvent]:
        """Get all events for a specific date."""
        return [
            event for event in self.events
            if event.start_datetime.date() == target_date
        ]
    
    def get_events_by_date_range(self, start_date: date, end_date: date) -> List[ScheduleEvent]:
        """Get all events within a date range."""
        return [
            event for event in self.events
            if start_date <= event.start_datetime.date() <= end_date
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schedule':
        """Create from dictionary."""
        return cls(**data)