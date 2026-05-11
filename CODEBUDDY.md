# CODEBUDDY.md

This file provides essential information for Terminal Assistant Agent instances working in this repository.

## Project Overview

LFC MCP Scheduler is a Python-based Model Context Protocol (MCP) server for schedule management with comprehensive file import/export capabilities. It supports Excel, Word, and TXT file formats for importing and exporting schedule data.

## Development Setup

### Prerequisites
- Python 3.8+
- pip

### Installation
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 或者开发安装
pip install -e .
```

### Running the Server
```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器（推荐）
python start_server.py

# 或者直接运行
python -m lfc_mcp_scheduler.server_v3
```

## Commands

### Testing
```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python -m pytest tests/
```

### Package Installation
```bash
pip install -e .  # Development installation
```

### Running Individual Components
```bash
# Run the MCP server directly
python lfc_mcp_scheduler/server.py
```

## Architecture

### Project Structure
```
lfc_mcp_scheduler/
├── __init__.py           # Package initialization
├── server.py            # Main MCP server with tool definitions
├── models/              # Data models
│   ├── __init__.py
│   └── schedule.py      # Schedule and Event models with Pydantic
├── tools/               # Business logic
│   ├── __init__.py
│   └── schedule_tools.py # ScheduleManager class with CRUD operations
└── utils/               # Utilities
    ├── __init__.py
    └── file_handlers.py  # Excel/Word/TXT import/export handlers
```

### Key Components

1. **Data Models** (`models/schedule.py`):
   - `ScheduleEvent`: Individual event with datetime, priority, status, tags, etc.
   - `Schedule`: Collection of events with metadata
   - Uses Pydantic for validation and serialization

2. **Schedule Manager** (`tools/schedule_tools.py`):
   - `ScheduleManager`: Main business logic class
   - Handles multiple schedules, CRUD operations, search, file I/O
   - In-memory storage (no persistence layer yet)

3. **File Handlers** (`utils/file_handlers.py`):
   - `ExcelHandler`: Uses openpyxl for .xlsx files
   - `WordHandler`: Uses python-docx for .docx files  
   - `TxtHandler`: Plain text format with structured parsing

4. **MCP Server** (`server_v3.py`):
   - Defines 13 MCP tools for schedule management
   - Handles tool calls and returns JSON responses
   - Uses asyncio and stdio for MCP communication
   - Compatible with MCP 1.15+ with proper initialization options

### MCP Tools Available
- Schedule management: create, list, switch, get schedules
- Event operations: add, update, delete, search events
- Date queries: get events by date or date range
- File operations: import/export Excel, Word, TXT files

### Dependencies
- `mcp>=1.0.0` - Model Context Protocol framework
- `pydantic>=2.0.0` - Data validation and serialization
- `openpyxl>=3.1.0` - Excel file handling
- `python-docx>=1.1.0` - Word document handling
- `pandas>=2.0.0` - Data manipulation
- `python-dateutil>=2.8.0` - Date parsing utilities

## Development Notes

- All datetime handling uses ISO format strings for MCP tool parameters
- Events support priorities (low/medium/high/urgent) and statuses (pending/in_progress/completed/cancelled)
- Supports recurring events with daily/weekly/monthly/yearly patterns
- File import/export preserves all event metadata including tags, attendees, notes
- Chinese language support throughout for user-facing messages
- No persistent storage yet - all data is in-memory during server session