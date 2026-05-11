"""Tests for schedule tools."""

import pytest
import time
from datetime import datetime
from lfc_mcp_scheduler.tools.schedule_tools import ScheduleManager


@pytest.fixture
def schedule_manager():
    """Create a fresh schedule manager for each test."""
    return ScheduleManager()


def test_create_schedule(schedule_manager):
    """Test creating a schedule."""
    result = schedule_manager.create_schedule("Test Schedule", "Test description")
    
    assert result["success"] is True
    assert "schedule_id" in result
    assert schedule_manager.current_schedule_id is not None
    assert len(schedule_manager.schedules) == 1


def test_list_schedules(schedule_manager):
    """Test listing schedules."""
    # Create a few schedules with small delay to ensure different timestamps
    result1 = schedule_manager.create_schedule("Schedule 1")
    time.sleep(0.001)  # Small delay to ensure different timestamps
    result2 = schedule_manager.create_schedule("Schedule 2")
    
    # Verify both schedules were created
    assert result1["success"] is True
    assert result2["success"] is True
    
    result = schedule_manager.list_schedules()
    
    assert result["success"] is True
    assert len(result["schedules"]) == 2
    assert result["current_schedule"] is not None


def test_add_event(schedule_manager):
    """Test adding an event."""
    # Create a schedule first
    schedule_manager.create_schedule("Test Schedule")
    
    result = schedule_manager.add_event(
        title="Test Event",
        start_datetime="2024-01-15T10:00:00",
        end_datetime="2024-01-15T11:00:00",
        description="Test description",
        location="Test location",
        priority="high"
    )
    
    assert result["success"] is True
    assert "event_id" in result
    
    # Verify event was added
    schedule_result = schedule_manager.get_schedule()
    assert len(schedule_result["schedule"]["events"]) == 1


def test_add_event_without_schedule(schedule_manager):
    """Test adding an event without a schedule."""
    result = schedule_manager.add_event(
        title="Test Event",
        start_datetime="2024-01-15T10:00:00"
    )
    
    assert result["success"] is False
    assert "未选择日程安排" in result["message"]


def test_update_event(schedule_manager):
    """Test updating an event."""
    # Create schedule and add event
    schedule_manager.create_schedule("Test Schedule")
    add_result = schedule_manager.add_event(
        title="Original Title",
        start_datetime="2024-01-15T10:00:00"
    )
    event_id = add_result["event_id"]
    
    # Update the event
    result = schedule_manager.update_event(
        event_id=event_id,
        title="Updated Title",
        description="Updated description"
    )
    
    assert result["success"] is True
    
    # Verify update
    schedule_result = schedule_manager.get_schedule()
    event = schedule_result["schedule"]["events"][0]
    assert event["title"] == "Updated Title"
    assert event["description"] == "Updated description"


def test_delete_event(schedule_manager):
    """Test deleting an event."""
    # Create schedule and add event
    schedule_manager.create_schedule("Test Schedule")
    add_result = schedule_manager.add_event(
        title="Test Event",
        start_datetime="2024-01-15T10:00:00"
    )
    event_id = add_result["event_id"]
    
    # Delete the event
    result = schedule_manager.delete_event(event_id)
    
    assert result["success"] is True
    
    # Verify deletion
    schedule_result = schedule_manager.get_schedule()
    assert len(schedule_result["schedule"]["events"]) == 0


def test_get_events_by_date(schedule_manager):
    """Test getting events by date."""
    # Create schedule and add events
    schedule_manager.create_schedule("Test Schedule")
    schedule_manager.add_event(
        title="Event 1",
        start_datetime="2024-01-15T10:00:00"
    )
    schedule_manager.add_event(
        title="Event 2",
        start_datetime="2024-01-15T14:00:00"
    )
    schedule_manager.add_event(
        title="Event 3",
        start_datetime="2024-01-16T10:00:00"
    )
    
    # Get events for Jan 15
    result = schedule_manager.get_events_by_date("2024-01-15")
    
    assert result["success"] is True
    assert len(result["events"]) == 2


def test_search_events(schedule_manager):
    """Test searching events."""
    # Create schedule and add events
    schedule_manager.create_schedule("Test Schedule")
    schedule_manager.add_event(
        title="Meeting with team",
        start_datetime="2024-01-15T10:00:00",
        tags=["work", "meeting"]
    )
    schedule_manager.add_event(
        title="Doctor appointment",
        start_datetime="2024-01-15T14:00:00",
        tags=["personal", "health"]
    )
    
    # Search for "meeting"
    result = schedule_manager.search_events("meeting")
    
    assert result["success"] is True
    assert len(result["events"]) == 1
    assert "Meeting with team" in result["events"][0]["title"]