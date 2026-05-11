# LFC MCP Scheduler

一个基于Model Context Protocol (MCP)的日程安排管理服务器，支持多种文件格式的导入导出功能。

## 功能特性

- 📅 **完整的日程管理**: 创建、查看、编辑和删除日程事件
- 📊 **多格式支持**: 支持Excel (.xlsx)、Word (.docx)、TXT文件的导入导出
- 🔍 **智能搜索**: 按标题、描述、地点和标签搜索事件
- 📆 **日期查询**: 支持按单日或日期范围查询事件
- 🏷️ **标签系统**: 为事件添加标签便于分类管理
- 👥 **参与者管理**: 为事件添加参与者信息
- 🔄 **重复事件**: 支持日、周、月、年重复模式
- ⚡ **优先级管理**: 支持低、中、高、紧急四个优先级

## 安装

1. 克隆项目：
```bash
git clone <repository-url>
cd lfc-mcp
```

2. 创建虚拟环境并安装依赖：
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

或使用pip安装：
```bash
pip install -e .
```

## 使用方法

### 启动MCP服务器

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务器
python start_server.py
```

### 可用工具

#### 日程管理
- `create_schedule` - 创建新的日程安排
- `list_schedules` - 列出所有日程安排
- `switch_schedule` - 切换到指定的日程安排
- `get_schedule` - 获取日程安排详细信息

#### 事件管理
- `add_event` - 添加新事件
- `update_event` - 更新现有事件
- `delete_event` - 删除事件
- `get_events_by_date` - 获取指定日期的事件
- `get_events_by_date_range` - 获取日期范围内的事件
- `search_events` - 搜索事件

#### 文件操作
- `import_from_file` - 从文件导入日程安排
- `export_to_file` - 导出日程安排到文件

## 文件格式支持

### Excel格式 (.xlsx)
- 完整的事件信息导入导出
- 自动调整列宽
- 支持中文标题

### Word格式 (.docx)
- 格式化的日程报告
- 表格形式展示事件详情
- 适合打印和分享

### TXT格式 (.txt)
- 简洁的文本格式
- 易于阅读和编辑
- 支持基本的事件信息

## 数据模型

### 事件属性
- **标题**: 事件名称（必填）
- **开始时间**: 事件开始时间（必填）
- **结束时间**: 事件结束时间（可选）
- **描述**: 事件详细描述（可选）
- **地点**: 事件地点（可选）
- **优先级**: low/medium/high/urgent（默认medium）
- **状态**: pending/in_progress/completed/cancelled（默认pending）
- **标签**: 事件标签列表
- **参与者**: 参与者列表
- **重复类型**: none/daily/weekly/monthly/yearly
- **重复结束日期**: 重复事件的结束日期
- **备注**: 额外备注信息

## 示例用法

### 创建日程安排
```json
{
  "name": "create_schedule",
  "arguments": {
    "name": "工作日程",
    "description": "2024年工作安排"
  }
}
```

### 添加事件
```json
{
  "name": "add_event",
  "arguments": {
    "title": "团队会议",
    "start_datetime": "2024-01-15T10:00:00",
    "end_datetime": "2024-01-15T11:30:00",
    "location": "会议室A",
    "priority": "high",
    "tags": ["会议", "工作"],
    "attendees": ["张三", "李四"]
  }
}
```

### 导出到Excel
```json
{
  "name": "export_to_file",
  "arguments": {
    "file_path": "/path/to/schedule.xlsx",
    "file_type": "excel"
  }
}
```

## 开发

### 项目结构
```
lfc_mcp_scheduler/
├── __init__.py           # 包初始化
├── server.py            # MCP服务器主文件
├── models/              # 数据模型
│   ├── __init__.py
│   └── schedule.py      # 日程和事件模型
├── tools/               # MCP工具
│   ├── __init__.py
│   └── schedule_tools.py # 日程管理工具
└── utils/               # 工具函数
    ├── __init__.py
    └── file_handlers.py  # 文件处理器
```

### 运行测试
```bash
python -m pytest tests/
```

## 许可证

MIT License