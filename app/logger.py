import logging
import logging.handlers
import sys

from app.config import LOG_FILE, LOG_OUTPUT  # 导入 logging.handlers 模块

# 配置日志记录器
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 设置日志级别
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')  # 设置日志格式

# 创建 handlers
handlers = []

if LOG_OUTPUT in ("FILE", "ALL"):
    # 创建 RotatingFileHandler，实现日志文件分割
    rotating_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,  # 日志文件路径
        maxBytes=5 * 1024 * 1024,  # 每个文件最大 5MB
        backupCount=5,  # 保留最近的 5 个文件
        encoding='utf-8'  # 设置编码
    )
    rotating_handler.setFormatter(formatter)  # 设置日志格式
    handlers.append(rotating_handler)

if LOG_OUTPUT in ("CONSOLE", "ALL"):
    # 创建 StreamHandler，输出到控制台
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

# 将 handlers 添加到 logger
for handler in handlers:
    logger.addHandler(handler)
