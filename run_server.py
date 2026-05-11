#!/usr/bin/env python3
"""启动脚本 - 尝试不同的方式启动MCP服务器"""

import sys
import asyncio
import traceback

def try_import_mcp():
    """尝试导入MCP库并检查版本"""
    try:
        import mcp
        print(f"MCP version: {getattr(mcp, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        print(f"无法导入MCP库: {e}")
        print("请安装MCP: pip install mcp")
        return False

def main():
    """主函数"""
    if not try_import_mcp():
        return 1
    
    print("尝试启动MCP服务器...")
    
    # 尝试方法1: 使用原始服务器
    try:
        print("方法1: 使用原始server.py")
        from lfc_mcp_scheduler.server import main as server_main
        asyncio.run(server_main())
        return 0
    except Exception as e:
        print(f"方法1失败: {e}")
        traceback.print_exc()
    
    # 尝试方法2: 使用简化服务器
    try:
        print("\n方法2: 使用简化server_simple.py")
        from lfc_mcp_scheduler.server_simple import main as simple_main
        asyncio.run(simple_main())
        return 0
    except Exception as e:
        print(f"方法2失败: {e}")
        traceback.print_exc()
    
    print("\n所有方法都失败了。请检查MCP库安装和版本兼容性。")
    return 1

if __name__ == "__main__":
    sys.exit(main())