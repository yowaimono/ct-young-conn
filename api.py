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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

USER_HOME = os.path.expanduser("~")
AUTH_DIR = os.path.join(USER_HOME, ".portalauth")
DEFAULT_AUTH_FILE = os.path.join(AUTH_DIR, "auth.data")

# 确保目录存在
if not os.path.exists(AUTH_DIR):
    os.makedirs(AUTH_DIR)

# 确保文件存在
if not os.path.exists(DEFAULT_AUTH_FILE):
    with open(DEFAULT_AUTH_FILE, "wb") as f:
        # 创建一个空文件
        pass




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
        
        self.load_username()
        self.load_password()
        
        self.load_params_from_binary()
    def get_info(self):
        return {"username":self.username,"password":self.password}


    def set_info(self,username: str, password: str):
        logging.info(f"set username: {username},password: {password}")
        self.username = username
        self.password = password
        self.save_username()
        self.save_password()
        

    def _extract_params_from_redirect(self, response) -> Optional[Dict[str, str]]:
        """从重定向响应中提取参数"""
        try:
            location = response.headers.get("Location", "")
            if not location:
                print("未找到重定向URL，可能已经登录。")
                return None

            params = {
                "wlanuserip": re.search(r"wlanuserip=([^&]+)", location).group(1),
                "wlanacname": re.search(r"wlanacname=([^&]+)", location).group(1),
                "wlanacip": re.search(r"wlanacip=([^&]+)", location).group(1),
                "usermac": re.search(r"usermac=([^&]+)", location).group(1),
            }
            return params
        except Exception as e:
            print(f"提取参数失败: {e}")
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
            print(f"request url: {url}")
            response = self.session.get(url,proxies = {'http': None, 'https': None})  # Use the session to send the request
            if response.status_code == 200 and "code[051]" in response.text and action == "登录":
                print("密码错误")
                return 4
            elif response.status_code == 200:
                
                print(f"{action}请求成功！")
                print("响应内容:", response.text)
                return 0
            else:
                print(f"{action}请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"请求发生错误: {e}")

    def _serialize_to_binary(self):
        filename = self.auth_file
        
        """将用户信息和参数序列化到二进制文件"""
        if not self.params:
            print("没有可保存的参数。")
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
        print(f"数据已保存到 {filename}")

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
            print(f"数据已从 {filename} 加载")
            return True
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"读取文件失败: {e}")
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
                    print(params);
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
                    print("重定向响应中缺少 Location 头。")
                    # return None
            else:
                print(f"未收到重定向响应，状态码: {response.status_code}")
                # return None

        except requests.exceptions.RequestException as e:
            print(f"请求发生错误: {e}")
            # return None
        except Exception as e:
            print(f"提取参数失败: {e}")
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
                    print("无法提取参数，可能已经登录。")
                    return 2

                # 构建登录URL
                login_url = self._build_login_url()
                print("登录URL:", login_url)

                # 发送登录请求
                result = self._send_request(login_url, "登录")
                
                if result:
                    return result

                # 登录成功后保存数据到文件
                self._serialize_to_binary()

                return 0  # login successfull
            elif response.status_code == 502:
                print("请关闭代理软件(VPN)")
                return 1  # proxy error
            
            else:
                print("也许已经登陆过了")

        except Exception as e:
            print(f"初始请求发生错误: {e}")
            return 3

    def logout(self):
        """注销方法"""
        # 尝试从文件加载参数
        
        try:
            if not self.params and not self._deserialize_from_binary():
                print("未找到参数，请先登录。")
                return 2 # 建议断开等一会儿重连

            # 构建注销URL
            logout_url = self._build_logout_url()
            print("注销URL:", logout_url)

            # 发送注销请求
            self._send_request(logout_url, "注销")
            
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
            print(f"已成功连接到 WiFi: {ssid}")
        except subprocess.CalledProcessError as e:
            print(f"连接失败: {e}")

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
            print("已断开连接")
        except subprocess.CalledProcessError as e:
            print(f"断开失败: {e}")


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

    def save_username(self):
        filename = self.auth_file
        """将用户名保存到二进制文件"""
        try:
            with open(filename, "rb+") as f:  # 以读写模式打开，文件不存在则创建
                # 读取文件内容，如果文件为空则初始化为空字节串
                content = f.read()
                if not content:
                    content = b'\0' * 128 + b'\0' * 256  # 初始化为128字节的用户信息 + 256字节的参数信息

                # 将用户名编码为字节串
                username_bytes = self.username.encode("utf-8")

                # 确保用户名不超过64字节，如果超过则截断
                username_bytes = username_bytes[:64]

                # 使用struct.pack将用户名打包为固定长度的字节串
                packed_username = struct.pack("!64s", username_bytes)

                # 将文件指针移动到文件开头
                f.seek(0)

                # 写入用户名
                f.write(packed_username)

                # 写入剩余的用户信息（密码）
                f.write(content[64:128])

                # 写入参数信息
                f.write(content[128:])

            print(f"用户名已保存到 {filename}")

        except Exception as e:
            print(f"保存用户名失败: {e}")

    def load_username(self):
        filename = self.auth_file
        """从二进制文件加载用户名"""
        try:
            with open(filename, "rb") as f:
                # 读取用户名块
                userinfo = f.read(64)  # 64字节
                username = struct.unpack("!64s", userinfo)[0]
                self.username = username.decode("utf-8").rstrip("\x00")
            print(f"用户名已从 {filename} 加载")
            return True
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"读取用户名失败: {e}")
            return False

    def save_password(self):
        filename = self.auth_file
        """将密码保存到二进制文件"""
        try:
            with open(filename, "rb+") as f:  # 以读写模式打开，文件不存在则创建
                # 读取文件内容，如果文件为空则初始化为空字节串
                content = f.read()
                if not content:
                    content = b'\0' * 128 + b'\0' * 256  # 初始化为128字节的用户信息 + 256字节的参数信息

                # 将密码编码为字节串
                password_bytes = self.password.encode("utf-8")

                # 确保密码不超过64字节，如果超过则截断
                password_bytes = password_bytes[:64]

                # 使用struct.pack将密码打包为固定长度的字节串
                packed_password = struct.pack("!64s", password_bytes)

                # 将文件指针移动到用户名之后的位置
                f.seek(64)

                # 写入密码
                f.write(packed_password)

                # 写入剩余的用户信息（用户名）
                f.seek(0)
                f.write(content[:64])

                # 写入参数信息
                f.seek(128)
                f.write(content[128:])

            print(f"密码已保存到 {filename}")

        except Exception as e:
            print(f"保存密码失败: {e}")

    def load_password(self):
        filename = self.auth_file
        """从二进制文件加载密码"""
        try:
            with open(filename, "rb") as f:
                # 读取密码块
                f.seek(64)
                password_info = f.read(64)  # 64字节
                password = struct.unpack("!64s", password_info)[0]
                self.password = password.decode("utf-8").rstrip("\x00")
            print(f"密码已从 {filename} 加载")
            return True
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"读取密码失败: {e}")
            return False

    def save_params_to_binary(self):
        filename = self.auth_file
        """将参数保存到二进制文件"""
        if not self.params:
            print("没有可保存的参数。")
            return

        try:
            with open(filename, "rb+") as f:  # 以读写模式打开，文件不存在则创建
                # 读取文件内容，如果文件为空则初始化为空字节串
                content = f.read()
                if not content:
                    content = b'\0' * 128 + b'\0' * 256  # 初始化为128字节的用户信息 + 256字节的参数信息

                # 将参数打包为二进制
                params = struct.pack(
                    "!64s64s64s64s",
                    self.params["wlanuserip"].encode("utf-8"),
                    self.params["wlanacname"].encode("utf-8"),
                    self.params["wlanacip"].encode("utf-8"),
                    self.params["usermac"].encode("utf-8"),
                )

                # 将文件指针移动到参数信息的位置
                f.seek(128)

                # 写入参数
                f.write(params)

                # 写入剩余的用户信息
                f.seek(0)
                f.write(content[:128])

            print(f"参数已保存到 {filename}")

        except Exception as e:
            print(f"保存参数失败: {e}")

    def load_params_from_binary(self):
        filename = self.auth_file
        """从二进制文件加载参数"""
        try:
            with open(filename, "rb") as f:
                # 读取参数块
                f.seek(128)
                params = f.read(256)  # 64s * 4 = 256字节
                wlanuserip, wlanacname, wlanacip, usermac = struct.unpack("!64s64s64s64s", params)
                self.params = {
                    "wlanuserip": wlanuserip.decode("utf-8").rstrip("\x00"),
                    "wlanacname": wlanacname.decode("utf-8").rstrip("\x00"),
                    "wlanacip": wlanacip.decode("utf-8").rstrip("\x00"),
                    "usermac": usermac.decode("utf-8").rstrip("\x00"),
                }
            print(f"参数已从 {filename} 加载")
            return True
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"读取参数失败: {e}")
            return False


    def connect_loop(self):
        while self.running:
            try:
                ssid = self.get_current_wifi_ssid()  # Replace with your actual function
                if ssid:
                    #logging.info(f"当前连接的 Wi-Fi 热点: {ssid}")
                    if ssid == self.target_ssid:
                        pass
                        #logging.info("已连接目标网络")
                        # self.login()  # Replace with your actual login function
                    else:
                       # logging.info("当前连接的非校园网，尝试连接{self.target_ssid}...")
                        self.connect_to_wifi(self.target_ssid)  # Replace with your actual function
                        self.login()
                        #logging.info(f"已尝试连接到目标网络：{self.target_ssid}")
                else:
                   # logging.info("未连接到任何 Wi-Fi 热点")
                    #logging.info(f"尝试连接到目标网络：{self.target_ssid}")
                    self.connect_to_wifi(self.target_ssid)  # Replace with your actual function
                    self.login()
                    #logging.info(f"已尝试连接到目标网络：{self.target_ssid}")
            except Exception as e:
                pass
                #logging.error(f"发生错误：{e}")
            time.sleep(self.check_interval)

    def start_task(self, ssid, interval):
        if self.running:
            logging.warning("Wi-Fi connector is already running. Stop it first.")
            return

        self.target_ssid = ssid
        self.check_interval = interval
        self.running = True
        self.thread = threading.Thread(target=self.connect_loop)
        self.thread.daemon = True
        self.thread.start()
        logging.info(f"Wi-Fi connector started in the background, connecting to {ssid} every {interval} seconds.")


    def stop_task(self):
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            logging.info("Wi-Fi connector stopped.")
            self.target_ssid = None  # Reset SSID and interval
            self.check_interval = None
            self.thread = None # Reset the thread
        else:
            logging.warning("Wi-Fi connector is not running.")
        
    
    def check_status(self):
        login_result = self.login()
        if login_result == 0:
            logging.info("登录成功，任务完成")
            self.status = 1 # 连接登陆成功
        elif login_result == 1:
            logging.error("代理错误，请关闭 VPN 或代理软件")
            self.status = 2 #连接登陆未完成
        elif login_result == 2:
            logging.info("已经登录，任务完成")
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
                    print(f"持久化文件中包含账号和密码: 用户名={username}, 密码={password}")
                    return True
                else:
                    print("持久化文件中没有有效的账号和密码。")
                    return False
        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
            return False
        except Exception as e:
            print(f"读取持久化文件失败: {e}")
            return False
    
    def clear_userinfo(self):
        filename = self.auth_file
        """从持久化文件中删除用户名和密码，保留参数信息"""
        try:
            with open(filename, "rb+") as f:
                # 读取整个文件内容
                content = f.read()

                # 如果文件为空，直接返回
                if not content:
                    print("文件为空，无需清理。")
                    return

                # 将用户名和密码部分替换为空字节
                # 用户名和密码共占用 128 字节（64s + 64s）
                empty_userinfo = b'\0' * 128

                # 将文件指针移动到开头
                f.seek(0)

                # 写入空用户名和密码
                f.write(empty_userinfo)

                # 写入剩余的参数信息
                f.write(content[128:])

                print(f"用户名和密码已从 {filename} 中删除，参数信息保留。")

            # 清空内存中的用户名和密码
            self.username = None
            self.password = None

        except FileNotFoundError:
            print(f"文件 {filename} 不存在")
        except Exception as e:
            print(f"清理用户信息失败: {e}")

    
    def is_first_login(self) -> bool:
        """判断是否是初次登录"""
        filename = self.auth_file
        try:
            with open(filename, "rb") as f:
                # 读取整个文件内容
                content = f.read()

                # 如果文件为空，认为是初次登录
                if not content:
                    return True

                # 读取参数段（假设参数段从第 128 字节开始）
                params = content[128:]

                # 如果参数段为空或全为默认值（例如全为 0），认为是初次登录
                if not params or all(byte == 0 for byte in params):
                    return True

                # 否则，认为不是初次登录
                return False

        except FileNotFoundError:
            # 如果文件不存在，认为是初次登录
            return True
        except Exception as e:
            print(f"判断初次登录失败: {e}")
            return True
            
if __name__ == "__main__":
    # 登录
    username ="2022102191"
    password = "040503"
    auth = PortalAuth()
    auth.set_info(username,password)
    result = auth.logout()
    
    print(result)
