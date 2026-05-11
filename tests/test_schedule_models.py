"""Tests for schedule models."""

import pytest
from datetime import datetime, date
from lfc_mcp_scheduler.models.schedule import (
    ScheduleEvent, Schedule, Priority, EventStatus, RepeatType
)


def test_schedule_event_creation():
    """Test creating a schedule event."""
    event = ScheduleEvent(
        title="Test Event",
        start_datetime=datetime(2024, 1, 15, 10, 0),
        description="Test description",
        location="Test location",
        priority=Priority.HIGH
    )
    
    assert event.title == "Test Event"
    assert event.priority == Priority.HIGH
    assert event.status == EventStatus.PENDING
    assert event.repeat_type == RepeatType.NONE


def test_schedule_event_validation():
    """Test schedule event validation."""
    # Test end datetime validation
    with pytest.raises(ValueError):
        ScheduleEvent(
            title="Test Event",
            start_datetime=datetime(2024, 1, 15, 10, 0),
            end_datetime=datetime(2024, 1, 15, 9, 0)  # Before start
        )


def test_schedule_creation():
    """Test creating a schedule."""
    schedule = Schedule(name="Test Schedule", description="Test description")
    
    assert schedule.name == "Test Schedule"
    assert schedule.description == "Test description"
    assert len(schedule.events) == 0


def test_schedule_add_event():
    """Test adding events to schedule."""
    schedule = Schedule(name="Test Schedule")
    event = ScheduleEvent(
        title="Test Event",
        start_datetime=datetime(2024, 1, 15, 10, 0)
    )
    
    schedule.add_event(event)
    
    assert len(schedule.events) == 1
    assert event.id is not None
    assert schedule.events[0] == event


def test_schedule_remove_event():
    """Test removing events from schedule."""
    schedule = Schedule(name="Test Schedule")
    event = ScheduleEvent(
        title="Test Event",
        start_datetime=datetime(2024, 1, 15, 10, 0)
    )
    
    schedule.add_event(event)
    assert len(schedule.events) == 1
    
    result = schedule.remove_event(event.id)
    assert result is True
    assert len(schedule.events) == 0
    
    # Test removing non-existent event
    result = schedule.remove_event("non-existent")
    assert result is False


def test_schedule_get_events_by_date():
    """Test getting events by date."""
    schedule = Schedule(name="Test Schedule")
    
    # Add events on different dates
    event1 = ScheduleEvent(
        title="Event 1",
        start_datetime=datetime(2024, 1, 15, 10, 0)
    )
    event2 = ScheduleEvent(
        title="Event 2",
        start_datetime=datetime(2024, 1, 15, 14, 0)
    )
    event3 = ScheduleEvent(
        title="Event 3",
        start_datetime=datetime(2024, 1, 16, 10, 0)
    )
    
    schedule.add_event(event1)
    schedule.add_event(event2)
    schedule.add_event(event3)
    
    # Get events for Jan 15
    events_jan_15 = schedule.get_events_by_date(date(2024, 1, 15))
    assert len(events_jan_15) == 2
    
    # Get events for Jan 16
    events_jan_16 = schedule.get_events_by_date(date(2024, 1, 16))
    assert len(events_jan_16) == 1


def test_schedule_get_events_by_date_range():
    """Test getting events by date range."""
    schedule = Schedule(name="Test Schedule")
    
    # Add events across multiple days
    for day in range(10, 20):
        event = ScheduleEvent(
            title=f"Event {day}",
            start_datetime=datetime(2024, 1, day, 10, 0)
        )
        schedule.add_event(event)
    
    # Get events for Jan 12-15
    events = schedule.get_events_by_date_range(
        date(2024, 1, 12),
        date(2024, 1, 15)
    )
    assert len(events) == 4  # Days 12, 13, 14, 15