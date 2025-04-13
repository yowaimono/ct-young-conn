import os
import struct

from app.logger import logger
from app.api import DEFAULT_AUTH_FILE




class AuthStorage:
    """二进制文件存储操作类（保持与旧版兼容）"""
    def __init__(self, filename: str = DEFAULT_AUTH_FILE):
        self.filename = filename
        self._init_file()

    #region 文件初始化
    def _init_file(self):
        """初始化空文件（兼容旧版结构）"""
        if not os.path.exists(self.filename):
            with open(self.filename, "wb") as f:
                # 旧版结构：用户信息(128) + 网络参数(256) + 配置(128)
                f.write(b'\0' * (128 + 256 + 128))
    #endregion

    #region 用户信息操作（兼容旧方法）
    def save_username(self, username: str):
        """单独保存用户名（兼容旧版）"""
        self._save_user_part(offset=0, data=username.encode('utf-8'))

    def load_username(self) -> str:
        """单独加载用户名（兼容旧版）"""
        return self._load_user_part(offset=0).rstrip('\0')

    def save_password(self, password: str):
        """单独保存密码（兼容旧版）"""
        self._save_user_part(offset=64, data=password.encode('utf-8'))

    def load_password(self) -> str:
        """单独加载密码（兼容旧版）"""
        return self._load_user_part(offset=64).rstrip('\0')

    def _save_user_part(self, offset: int, data: bytes):
        """通用用户信息保存"""
        try:
            with open(self.filename, "r+b") as f:
                f.seek(offset)
                f.write(data.ljust(64, b'\0'))  # 保持64字节长度
        except Exception as e:
            logger.error(f"用户信息保存失败: {e}")

    def _load_user_part(self, offset: int) -> str:
        """通用用户信息读取"""
        try:
            with open(self.filename, "rb") as f:
                f.seek(offset)
                return f.read(64).decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"用户信息读取失败: {e}")
            return ""
    #endregion

    #region 网络参数操作（保持旧方法名）
    def save_params_to_binary(self, params: dict):
        """保存网络参数（兼容旧版）"""
        try:
            with open(self.filename, "r+b") as f:
                f.seek(128)  # 参数段偏移
                packed = struct.pack(
                    "!64s64s64s64s",
                    params['wlanuserip'].encode('utf-8').ljust(64, b'\0'),
                    params['wlanacname'].encode('utf-8').ljust(64, b'\0'),
                    params['wlanacip'].encode('utf-8').ljust(64, b'\0'),
                    params['usermac'].encode('utf-8').ljust(64, b'\0')
                )
                f.write(packed)
        except Exception as e:
            logger.error(f"参数保存失败: {e}")

    def load_params_from_binary(self) -> dict:
        """加载网络参数（兼容旧版）"""
        try:
            with open(self.filename, "rb") as f:
                f.seek(128)
                data = f.read(256)
                params = struct.unpack("!64s64s64s64s", data)
                return {
                    'wlanuserip': params[0].decode('utf-8').rstrip('\0'),
                    'wlanacname': params[1].decode('utf-8').rstrip('\0'),
                    'wlanacip': params[2].decode('utf-8').rstrip('\0'),
                    'usermac': params[3].decode('utf-8').rstrip('\0')
                }
        except Exception as e:
            logger.error(f"参数加载失败: {e}")
            return {}
    #endregion

    #region 新版配置操作（兼容旧方法）
    def save_config(self, config: dict):
        """保存配置参数（新版）"""
        try:
            with open(self.filename, "r+b") as f:
                f.seek(384)  # 配置段偏移
                packed = struct.pack(
                    "!BHHHHI",
                    config['mode'],
                    config['keep_start'][0] * 60 + config['keep_start'][1],
                    config['keep_end'][0] * 60 + config['keep_end'][1],
                    config['schedule_login'][0] * 60 + config['schedule_login'][1],
                    config['schedule_logout'][0] * 60 + config['schedule_logout'][1],
                    config['check_interval']
                )
                f.write(packed.ljust(128, b'\0'))  # 填充剩余空间
                
                logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    def load_config(self) -> dict:
        """加载配置参数（新版）"""
        default_config = {
            'mode': 0,
            'keep_start': (8, 0),
            'keep_end': (23, 0),
            'schedule_login': (7, 0),
            'schedule_logout': (23, 30),
            'check_interval': 300
        }
        
        
        try:
            with open(self.filename, "rb") as f:
                f.seek(384)
                data = f.read(13)  # 基础配置占12字节
                if len(data) < 12:
                    return default_config
                
                values = struct.unpack("!BHHHHI", data)
                
                config =  {
                    'mode': values[0],
                    'keep_start': (values[1] // 60, values[1] % 60),
                    'keep_end': (values[2] // 60, values[2] % 60),
                    'schedule_login': (values[3] // 60, values[3] % 60),
                    'schedule_logout': (values[4] // 60, values[4] % 60),
                    'check_interval': values[5]
                }
                
                logger.info(f"加载成功: {config}")
                return config
                
                
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            return default_config