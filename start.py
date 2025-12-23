#!/usr/bin/env python
"""
Deepseek 测试用例生成工具启动脚本
运行这个脚本来启动GUI启动器
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入启动器主模块
    from main_launcher import main

    if __name__ == '__main__':
        main()

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保以下文件存在:")
    print("  - main_launcher.py")
    print("  - deepseek_test_generator_gui_enhanced.py")
    print("\n如果缺少依赖包，请运行: pip install -r requirements.txt")
    input("\n按Enter键退出...")