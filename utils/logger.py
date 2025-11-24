"""
日志配置模块
使用loguru进行统一的日志管理
"""

import sys
from loguru import logger

# 配置loguru日志
logger.remove()  # 移除默认的处理器

# 添加控制台输出（INFO级别及以上）
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO",
    colorize=True
)

# 添加文件输出（DEBUG级别及以上，每天轮转，保留7天）
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG"
)

# 添加错误日志文件（只记录ERROR级别）
logger.add(
    "logs/error.log",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR"
)

# 导出logger实例
__all__ = ['logger']