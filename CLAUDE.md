# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LFC MCP Scheduler is a Python-based Model Context Protocol (MCP) server for schedule management with comprehensive file import/export capabilities. It supports Excel (.xlsx), Word (.docx), and TXT file formats for importing and exporting schedule data.

## Development Setup

### Prerequisites
- Python 3.8+
- pip

### Installation & Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### Running the Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start the MCP server (recommended method)
python start_server.py

# Alternative startup methods
python run_server.py  # Tries multiple server versions
python -m lfc_mcp_scheduler.server_v3  # Direct module execution
```

## Common Development Commands

### Testing
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_schedule_tools.py
python -m pytest tests/test_schedule_models.py

# Run tests with verbose output
python -m pytest tests/ -v
```

### Package Management
```bash
# Install in development mode (editable)
pip install -e .

# Install specific dependencies
pip install mcp>=1.15.0 pydantic>=2.0.0
```

## Architecture Overview

### Project Structure
```
lfc_mcp_scheduler/
├── __init__.py           # Package initialization
├── server.py            # Main MCP server with tool definitions
├── server_v2.py         # Alternative server version
├── server_v3.py         # Latest server version (used by start_server.py)
├── server_simple.py     # Simplified server version
├── models/              # Data models
│   ├── __init__.py
│   └── schedule.py      # Schedule and Event models with Pydantic validation
├── tools/               # Business logic layer
│   ├── __init__.py
│   └── schedule_tools.py # ScheduleManager class with CRUD operations
└── utils/               # Utility functions
    ├── __init__.py
    └── file_handlers.py  # Excel/Word/TXT import/export handlers
```

### Key Components

**Data Models** (`models/schedule.py`):
- `ScheduleEvent`: Individual events with validation using Pydantic
- `Schedule`: Collection of events with metadata
- Enums: `Priority`, `EventStatus`, `RepeatType`
- Full validation including end datetime > start datetime

**Schedule Manager** (`tools/schedule_tools.py`):
- `ScheduleManager`: Core business logic class
- Handles multiple schedules with in-memory storage
- CRUD operations, search, date queries, file I/O
- No persistence layer - data lives during server session

**File Handlers** (`utils/file_handlers.py`):
- `ExcelHandler`: Uses openpyxl for .xlsx files with Chinese headers
- `WordHandler`: Uses python-docx for .docx documents
- `TxtHandler`: Plain text format with structured parsing

**MCP Server** (`server_v3.py`):
- 13 MCP tools for complete schedule management
- Compatible with MCP 1.15+ with proper initialization
- Uses asyncio and stdio for communication

### MCP Tools Available

**Schedule Management:**
- `create_schedule` - Create new schedule with name and description
- `list_schedules` - List all available schedules
- `switch_schedule` - Switch active schedule context
- `get_schedule` - Get detailed schedule information

**Event Operations:**
- `add_event` - Add new event with full metadata support
- `update_event` - Update existing event (all fields optional)
- `delete_event` - Remove event by ID
- `search_events` - Search by title, description, location, tags

**Date Queries:**
- `get_events_by_date` - Get events for specific date
- `get_events_by_date_range` - Get events within date range

**File Operations:**
- `import_from_file` - Import from Excel/Word/TXT files
- `export_to_file` - Export schedule to Excel/Word/TXT files

### Dependencies
- `mcp>=1.15.0` - Model Context Protocol framework
- `pydantic>=2.0.0` - Data validation and serialization
- `openpyxl>=3.1.0` - Excel file handling
- `python-docx>=1.1.0` - Word document handling
- `pandas>=2.0.0` - Data manipulation
- `python-dateutil>=2.8.0` - Date parsing utilities

## Important Implementation Details

### Data Handling
- All datetime parameters use ISO format strings (YYYY-MM-DDTHH:MM:SS)
- Events support priority levels: low/medium/high/urgent
- Event status tracking: pending/in_progress/completed/cancelled
- Recurring events with daily/weekly/monthly/yearly patterns
- Full Chinese language support for user-facing messages

### Server Architecture Notes
- Multiple server versions available (server.py, server_v2.py, server_v3.py)
- `start_server.py` uses `server_v3.py` by default
- `run_server.py` provides fallback mechanism trying different versions
- All data is stored in-memory during server session
- No persistent storage or database layer implemented

### File Format Support
- **Excel**: Complete event preservation with Chinese headers, auto-adjusted columns
- **Word**: Formatted reports with tables, suitable for printing
- **TXT**: Simple text format with basic event information

### Error Handling
- Comprehensive validation using Pydantic models
- Graceful error handling with user-friendly Chinese messages
- Proper MCP error responses with detailed error information