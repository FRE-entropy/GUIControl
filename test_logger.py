#!/usr/bin/env python3
"""
测试日志功能是否正常工作
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger

def test_logger():
    """测试日志功能"""
    print("开始测试日志功能...")
    
    # 测试不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条信息日志")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    
    # 测试带变量的日志
    test_var = "测试变量"
    logger.info(f"带变量的日志: {test_var}")
    
    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except Exception as e:
        logger.error(f"捕获到异常: {e}")
    
    print("日志功能测试完成！")
    print("请检查控制台输出和日志文件是否正常生成。")

if __name__ == "__main__":
    test_logger()