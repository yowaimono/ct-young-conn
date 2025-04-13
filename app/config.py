import requests
import re
import struct
from typing import Dict, Optional
import logging
import subprocess
import threading
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs
import time
import os


# 配置日志记录
USER_HOME = os.path.expanduser("~")
AUTH_DIR = os.path.join(USER_HOME, ".portalauth")
DEFAULT_AUTH_FILE = os.path.join(AUTH_DIR, "auth.data")
LOG_FILE = os.path.join(AUTH_DIR, "app.log")  # 定义日志文件路径
LOG_OUTPUT = "ALL"  # "FILE", "CONSOLE", 或 "ALL"


# 确保目录存在
if not os.path.exists(AUTH_DIR):
    os.makedirs(AUTH_DIR)

# 确保文件存在
if not os.path.exists(DEFAULT_AUTH_FILE):
    with open(DEFAULT_AUTH_FILE, "wb") as f:
        # 创建一个空文件
        pass

