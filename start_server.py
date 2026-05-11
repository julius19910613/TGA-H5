#!/usr/bin/env python3
"""启动LFC MCP Schedule服务器"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """主函数"""
    try:
        from lfc_mcp_scheduler.server_v3 import main as server_main
        print("🚀 启动LFC MCP Schedule服务器...")
        print("📋 可用工具:")
        print("  - create_schedule: 创建日程安排")
        print("  - add_event: 添加事件")
        print("  - list_schedules: 列出所有日程")
        print("  - search_events: 搜索事件")
        print("  - import_from_file: 导入文件")
        print("  - export_to_file: 导出文件")
        print("  - 以及更多...")
        print("\n✅ 服务器已启动，等待MCP客户端连接...")
        
        asyncio.run(server_main())
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return 0
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())