import datetime
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
import logging.handlers

from app.logger import logger
from app.config import DEFAULT_AUTH_FILE
from app.storage import AuthStorage  # 导入 logging.handlers 模块

class PortalAuth:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.params: Optional[Dict[str, str]] = None
        self.auth_file = DEFAULT_AUTH_FILE
        
        
        self.session = requests.Session()  # Use a session for persistent connections
        self.session.adapters.DEFAULT_RETRIES = 5  # Set retries for the session
        self.session.proxies = {'http': None, 'https': None}  # Disable proxies
        self.session.headers.update({  # Set default headers for the session
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
            "Accept": "*/*",
            "Referer": "http://182.98.163.154:1500/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",  # Disable keep-alive
        })
        
    def __init__(self):
        self.username = None
        self.password = None
        self.params: Optional[Dict[str, str]] = None
        
        self.running = False
        self.thread = None
        self.target_ssid = None
        self.check_interval = None
        self.auth_file = DEFAULT_AUTH_FILE
        
        
        self.session = requests.Session()  # Use a session for persistent connections
        self.session.adapters.DEFAULT_RETRIES = 5  # Set retries for the session
        self.session.proxies = {'http': None, 'https': None}  # Disable proxies
        self.session.keep_alive = False
        self.session.headers.update({  # Set default headers for the session
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
            "Accept": "*/*",
            "Referer": "http://182.98.163.154:1500/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",  # Disable keep-alive
        })
        
        self.storage = AuthStorage()  # 存储操作代理
        
        # 初始化数据（保持旧版兼容）
        self.username = self.storage.load_username()
        self.password = self.storage.load_password()
        self.params = self.storage.load_params_from_binary()
        self.config = self.storage.load_config()
        
        
        
        if self.config['mode'] == 0:
            self.sched_login();
            self.sched_logout();
        elif self.config['mode']== 1:
            # 开启自动Keep
            self.start_task("CT-Young");
        
        
    def get_info(self):
        return {"username":self.username,"password":self.password}


    def set_info(self,username: str, password: str):
        logger.info(f"set username: {username},password: {password}")
        self.username = username
        self.password = password
        self.save_username()
        self.save_password()
        
        
    def save_username(self):
        """保持原有方法"""
        self.storage.save_username(self.username)

    def save_password(self):
        """保持原有方法"""
        self.storage.save_password(self.password)

    def save_params_to_binary(self):
        """保持原有方法"""
        if self.params:
            self.storage.save_params_to_binary(self.params)

    def load_params_from_binary(self) -> bool:
        """保持原有方法"""
        self.params = self.storage.load_params_from_binary()
        return bool(self.params)



    def set_config(self, cfg):
        """增强版配置更新"""
        valid_keys = ['mode', 'keep_start', 'keep_end', 
                    'schedule_login', 'schedule_logout', 'check_interval']
        update_config = {k: v for k, v in cfg.items() if k in valid_keys}
        logger.info(f"set config: {update_config}")
        self.config.update(update_config)
        self.storage.save_config(self.config)
        
        # reload 
        self.config = self.storage.load_config()
        
        if self.config['mode'] == 0:
            self.sched_login();
            self.sched_logout();
            self.stop_task()
        elif self.config['mode']== 1:
            # 开启自动Keep
            self.start_task("CT-Young");


    def _extract_params_from_redirect(self, response) -> Optional[Dict[str, str]]:
        """从重定向响应中提取参数"""
        try:
            location = response.headers.get("Location", "")
            if not location:
                logger.info("未找到重定向URL，可能已经登录。")
                return None

            params = {
                "wlanuserip": re.search(r"wlanuserip=([^&]+)", location).group(1),
                "wlanacname": re.search(r"wlanacname=([^&]+)", location).group(1),
                "wlanacip": re.search(r"wlanacip=([^&]+)", location).group(1),
                "usermac": re.search(r"usermac=([^&]+)", location).group(1),
            }
            return params
        except Exception as e:
            logger.error(f"提取参数失败: {e}")
            return None

    def _build_login_url(self) -> str:
        """构建登录URL"""
        base_url = "http://182.98.163.154:801/eportal/portal/login"
        login_params = {
            "callback": "dr1003",
            "login_method": "1",
            "user_account": self.username,
            "user_password": self.password,
            "wlan_user_ip": self.params["wlanuserip"],
            "wlan_user_ipv6": "",
            "wlan_user_mac": self.params["usermac"],
            "wlan_ac_ip": self.params["wlanacip"],
            "wlan_ac_name": self.params["wlanacname"],
            "jsVersion": "4.2.1",
            "terminal_type": "1",
            "lang": "zh-cn",
            "v": "1225",
        }
        return f"{base_url}?{'&'.join([f'{k}={v}' for k, v in login_params.items()])}"

    def _build_logout_url(self) -> str:
        """构建注销URL"""
        base_url = "http://182.98.163.154:801/eportal/portal/logout"
        logout_params = {
            "callback": "dr1004",
            "login_method": "1",
            "user_account": "drcom",
            "user_password": "123",
            "ac_logout": "0",
            "register_mode": "0",
            "wlan_user_ip": self.params["wlanuserip"],
            "wlan_user_ipv6": "",
            "wlan_vlan_id": "0",
            "wlan_user_mac": self.params["usermac"],
            "wlan_ac_ip": self.params["wlanacip"],
            "wlan_ac_name": self.params["wlanacname"],
            "jsVersion": "4.2.1",
            "v": "3441",
            "lang": "zh",
        }
        return f"{base_url}?{'&'.join([f'{k}={v}' for k, v in logout_params.items()])}"

    def _send_request(self, url: str, action: str):
        """发送请求"""
        try:
            logger.info(f"request url: {url}")
            response = self.session.get(url,proxies = {'http': None, 'https': None})  # Use the session to send the request
            if response.status_code == 200 and "code[051]" in response.text and action == "登录":
                logger.info("密码错误")
                return 4
            elif response.status_code == 200 and "注销失败" in response.text and action == "注销":
                logger.info(f"{action}发送成功！")
                logger.info("响应内容:", response.text)
                return 3;
            elif response.status_code == 200:
                
                logger.info(f"{action}发送成功！")
                logger.info("响应内容:", response.text)
                return 0
            else:
                logger.info(f"{action}请求失败，状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"请求发生错误: {e}")

    def _serialize_to_binary(self):
        filename = self.auth_file
        
        """将用户信息和参数序列化到二进制文件"""
        if not self.params:
            logger.info("没有可保存的参数。")
            return

        # 将用户信息和参数打包为二进制
        userinfo = struct.pack("!64s64s", self.username.encode("utf-8"), self.password.encode("utf-8"))
        params = struct.pack(
            "!64s64s64s64s",
            self.params["wlanuserip"].encode("utf-8"),
            self.params["wlanacname"].encode("utf-8"),
            self.params["wlanacip"].encode("utf-8"),
            self.params["usermac"].encode("utf-8"),
        )

        # 写入文件
        with open(filename, "wb") as f:
            f.write(userinfo)
            f.write(params)
        logger.info(f"数据已保存到 {filename}")

    def _deserialize_from_binary(self) -> bool:
        filename = self.auth_file
        """从二进制文件读取用户信息和参数"""
        try:
            with open(filename, "rb") as f:
                # 读取用户信息块
                userinfo = f.read(128)  # 64s + 64s = 128字节
                username, password = struct.unpack("!64s64s", userinfo)
                self.username = username.decode("utf-8").rstrip("\x00")
                self.password = password.decode("utf-8").rstrip("\x00")

                # 读取参数块
                params = f.read(256)  # 64s * 4 = 256字节
                wlanuserip, wlanacname, wlanacip, usermac = struct.unpack("!64s64s64s64s", params)
                self.params = {
                    "wlanuserip": wlanuserip.decode("utf-8").rstrip("\x00"),
                    "wlanacname": wlanacname.decode("utf-8").rstrip("\x00"),
                    "wlanacip": wlanacip.decode("utf-8").rstrip("\x00"),
                    "usermac": usermac.decode("utf-8").rstrip("\x00"),
                }
            logger.info(f"数据已从 {filename} 加载")
            return True
        except FileNotFoundError:
            logger.info(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            return False
        
        
    def get_params(self):
        self.connect_to_wifi("CMCC-5G") # 先连移动
        time.sleep(3)
        initial_url = "http://www.msftconnecttest.com/redirect"
        try:
            # 发送 GET 请求，禁止自动重定向
            headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36"
            }
            response = requests.get(initial_url, headers=headers, proxies= {'http': None, 'https': None}, allow_redirects=False)

            # 检查是否重定向
            if response.status_code == 302 or response.status_code == 301:
                location = response.headers.get("Location")
                if location:
                    # 解析重定向 URL 并提取参数
                    parsed_url = urlparse(location)
                    query_params = parse_qs(parsed_url.query)

                    # 将列表值转换为单个字符串值 (如果需要)
                    params = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in query_params.items()}
                    logger.info(params);
                    # return params
                    params = {
                        "wlanuserip": re.search(r"wlanuserip=([^&]+)", location).group(1),
                        "wlanacname": re.search(r"wlanacname=([^&]+)", location).group(1),
                        "wlanacip": re.search(r"wlanacip=([^&]+)", location).group(1),
                        "usermac": re.search(r"wlanparameter=([^&]+)", location).group(1),
                    }
                    
                    self.params = params
                    
                    self.save_params_to_binary()
                    self.connect_to_wifi("CT-Young")
                    time.sleep(1)

                else:
                    logger.info("重定向响应中缺少 Location 头。")
                    # return None
            else:
                logger.info(f"未收到重定向响应，状态码: {response.status_code}")
                # return None

        except requests.exceptions.RequestException as e:
            logger.error(f"请求发生错误: {e}")
            # return None
        except Exception as e:
            logger.error(f"提取参数失败: {e}")
            # return None

            

    def login(self):
        self.connect_to_wifi("CT-Young")
        time.sleep(1)
        return self.do_login()
        
    

    def do_login(self):
        """登录方法"""

        # self.load_username()
        # self.load_password()

        # 发送初始请求以获取重定向参数
        initial_url = "http://www.msftconnecttest.com/redirect"
        try:
            response = self.session.get(initial_url,proxies = {'http': None, 'https': None}, allow_redirects=False)  # Use session
            # print(response.text)
            if response.status_code == 302:
                self.params = self._extract_params_from_redirect(response)
                if not self.params:
                    logger.info("无法提取参数，可能已经登录。")
                    return 2

                # 构建登录URL
                login_url = self._build_login_url()
                logger.info("登录URL:", login_url)

                # 发送登录请求
                result = self._send_request(login_url, "登录")
                
                if result:
                    return result

                # 登录成功后保存数据到文件
                self._serialize_to_binary()

                return 0  # login successfull
            elif response.status_code == 502:
                logger.info("请关闭代理软件(VPN)")
                return 1  # proxy error
            
            else:
                logger.info("也许已经登陆过了")

        except Exception as e:
            logger.error(f"初始请求发生错误: {e}")
            return 3

    def logout(self):
        """注销方法"""
        # 尝试从文件加载参数
        
        try:
            if not self.params and not self._deserialize_from_binary():
                logger.info("未找到参数，请先登录。")
                return 2 # 建议断开等一会儿重连

            # 构建注销URL
            logout_url = self._build_logout_url()
            logger.info("注销URL:", logout_url)

            # 发送注销请求
            res =  self._send_request(logout_url, "注销")
            
            if res == 3: 
                return 3
            
            
            return 0 # 注销成功
        except:
            return 1 # 错误


    def connect_to_wifi(self, ssid):
        """连接到指定的 WiFi 网络"""
        try:
            # 设置启动信息，隐藏窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # 断开当前连接
            subprocess.run(
                ["netsh", "wlan", "disconnect"],
                check=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 连接到指定的开放 WiFi
            subprocess.run(
                ["netsh", "wlan", "connect", f"name={ssid}"],
                check=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info(f"已成功连接到 WiFi: {ssid}")
        except subprocess.CalledProcessError as e:
            logger.error(f"连接失败: {e}")

    def disc(self):
        try:
            # 设置启动信息，隐藏窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # 断开当前连接
            subprocess.run(
                ["netsh", "wlan", "disconnect"],
                check=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("已断开连接")
        except subprocess.CalledProcessError as e:
            logger.error(f"断开失败: {e}")


    def get_current_wifi_ssid(self):
        """获取当前连接的 WiFi 网络的 SSID"""
        # 设置启动信息，隐藏窗口
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        # 执行 netsh 命令获取 Wi-Fi 接口信息，并显式指定编码为 utf-8
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",  # 忽略无法解码的字符
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏窗口
        )

        # 检查命令是否成功执行
        if result.returncode != 0:
            raise Exception("Failed to execute netsh command")

        # 使用正则表达式匹配 SSID
        ssid_pattern = r"SSID\s*:\s*(.+)"
        match = re.search(ssid_pattern, result.stdout)

        # 如果匹配到 SSID，返回结果
        if match:
            return match.group(1).strip()
        else:
            return None
        
    def is_connected(self):
        """判断是否连接到正确的网络"""
        curr_ssid  = self.get_current_wifi_ssid()
        if curr_ssid == "CT-Young":
            return True
        return False

    def connect_loop(self):
        while self.running:
            try:
                # 检查是否在保持时间段内
                current_time = time.localtime()
                current_hour = current_time.tm_hour
                current_min = current_time.tm_min
                
                # 计算当前时间分钟数
                current_minutes = current_hour * 60 + current_min
                keep_start_min = self.config['keep_start'][0] * 60 + self.config['keep_start'][1]
                keep_end_min = self.config['keep_end'][0] * 60 + self.config['keep_end'][1]
                
                # 时间段外处理
                if not (keep_start_min <= current_minutes < keep_end_min):
                    logger.info(f"当前时间 {current_hour}:{current_min:02d} 不在保持时段内")
                    time.sleep(self.check_interval * 5)  # 非活跃时段延长检查间隔
                    continue
                    
                # 正常连接检查流程
                ssid = self.get_current_wifi_ssid()
                if ssid:
                    logger.info(f"当前Wi-Fi: {ssid}")
                    if ssid == self.target_ssid:
                        self.login()
                    else:
                        logger.info(f"尝试连接目标网络: {self.target_ssid}")
                        self.connect_to_wifi(self.target_ssid)
                        time.sleep(3)  # 等待连接稳定
                        self.login()
                else:
                    logger.info("未连接任何Wi-Fi，尝试连接...")
                    self.connect_to_wifi(self.target_ssid)
                    time.sleep(3)
                    self.login()
                    
            except Exception as e:
                logger.error(f"连接循环错误: {e}")
                time.sleep(10)  # 出错后等待10秒
                
            time.sleep(self.check_interval)
 
            
    def start_task(self, ssid):
        if self.running:
            logger.warning("Wi-Fi connector is already running. Stop it first.")
            return

        self.target_ssid = ssid
        self.check_interval = self.config['check_interval']
        self.running = True
        self.thread = threading.Thread(target=self.connect_loop)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Wi-Fi connector started in the background, connecting to {ssid} every {self.check_interval} seconds.")

    def sched_login(self):
        """定时上线"""
        def login_task():
            while self.config['mode'] == 0:
                now = datetime.datetime.now()
                login_time = now.replace(hour=self.config['schedule_login'][0], minute=self.config['schedule_login'][1], second=0, microsecond=0)
                
                # 如果当前时间已经超过了今天的登录时间，则设置为明天的登录时间
                if now > login_time:
                    login_time += datetime.timedelta(days=1)
                
                wait_time = (login_time - now).total_seconds()
                logger.info(f"等待 {wait_time} 秒后执行定时登录...")
                
                # 如果等待时间小于检查间隔，直接执行任务
                if wait_time <= self.config['check_interval']:
                    logger.info("执行定时登录...")
                    self.login()
                    # 任务执行后，等待到下一个周期
                    time.sleep(self.config['check_interval'])
                else:
                    # 否则，等待到接近目标时间
                    time.sleep(min(wait_time, self.config['check_interval']))

        if self.config['mode'] == 0:
            self.running = True
            threading.Thread(target=login_task, daemon=True).start()
            logger.info("定时登录任务已启动。")
        else:
            logger.info("当前模式不允许定时登录。")


    def get_config(self) -> dict:
        return self.config

    def sched_logout(self):
        """定时下线"""
        def logout_task():
            while self.config['mode'] == 0:
                now = datetime.datetime.now()
                logout_time = now.replace(hour=self.config['schedule_logout'][0], minute=self.config['schedule_logout'][1], second=0, microsecond=0)
                
                # 如果当前时间已经超过了今天的登出时间，则设置为明天的登出时间
                if now > logout_time:
                    logout_time += datetime.timedelta(days=1)
                
                wait_time = (logout_time - now).total_seconds()
                logger.info(f"等待 {wait_time} 秒后执行定时登出...")
                
                # 如果等待时间小于检查间隔，直接执行任务
                if wait_time <= self.config['check_interval']:
                    logger.info("执行定时登出...")
                    self.logout()
                    # 任务执行后，等待到下一个周期
                    time.sleep(self.config['check_interval'])
                else:
                    # 否则，等待到接近目标时间
                    time.sleep(min(wait_time, self.config['check_interval']))


        if self.config['mode'] == 0:
            self.running = True
            threading.Thread(target=logout_task, daemon=True).start()
            logger.info("定时登出任务已启动。")
        else:
            logger.info("当前模式不允许定时登出。")
            

    def stop_task(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logger.info("Wi-Fi connector stopped.")
            self.target_ssid = None  # Reset SSID and interval
            self.check_interval = None
            self.thread = None # Reset the thread
        else:
            logger.warning("Wi-Fi connector is not running.")
        
    
    def check_status(self):
        login_result = self.login()
        if login_result == 0:
            logger.info("登录成功，任务完成")
            self.status = 1 # 连接登陆成功
        elif login_result == 1:
            logger.error("代理错误，请关闭 VPN 或代理软件")
            self.status = 2 #连接登陆未完成
        elif login_result == 2:
            logger.info("已经登录，任务完成")
            self.status = 3 # 连接并登录
            
    def is_login(self) -> bool:
        filename = self.auth_file
        """检查持久化文件中是否包含账号和密码"""
        try:
            with open(filename, "rb") as f:
                # 读取用户信息块
                userinfo = f.read(128)  # 64s + 64s = 128字节
                username, password = struct.unpack("!64s64s", userinfo)
                username = username.decode("utf-8").rstrip("\x00")
                password = password.decode("utf-8").rstrip("\x00")

                # 检查用户名和密码是否为空
                if username and password:
                    logger.info(f"持久化文件中包含账号和密码: 用户名={username}, 密码={password}")
                    return True
                else:
                    logger.info("持久化文件中没有有效的账号和密码。")
                    return False
        except FileNotFoundError:
            logger.info(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            logger.error(f"读取持久化文件失败: {e}")
            return False
    
    def clear_userinfo(self):
        """兼容旧版方法"""
        self.username = ""
        self.password = ""
        self.storage.save_username("")
        self.storage.save_password("")
    
    def is_first_login(self) -> bool:
        """兼容旧版判断逻辑"""
        return not (self.username and self.password)
            
if __name__ == "__main__":
    # 登录
    username ="2022102191"
    password = "040503"
    auth = PortalAuth()