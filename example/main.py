import requests
import re
import getpass

class PortalAuth:
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.params = None

    def _extract_params_from_redirect(self, response):
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

    def _build_login_url(self):
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

    def _build_logout_url(self):
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

    def _send_request(self, url, action):
        """发送请求"""
        headers = {
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.70 Safari/537.36",
            "Accept": "*/*",
            "Referer": "http://182.98.163.154:1500/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(f"{action}请求成功！")
                print("响应内容:", response.text)
            else:
                print(f"{action}请求失败，状态码: {response.status_code}")
        except Exception as e:
            print(f"请求发生错误: {e}")

    def login(self):
        """登录方法"""


        # 发送初始请求以获取重定向参数
        initial_url = "http://www.msftconnecttest.com/redirect"
        try:
            response = requests.get(initial_url, allow_redirects=False)
            if response.status_code == 302:
                self.params = self._extract_params_from_redirect(response)
                if not self.params:
                    print("无法提取参数，可能已经登录。")
                    return

                # 构建登录URL
                login_url = self._build_login_url()
                print("登录URL:", login_url)
            
                # 发送登录请求
                self._send_request(login_url, "登录")
            elif response.status_code == 502:
                print("请关闭代理软件(VPN)")
            else:
                print("未收到重定向响应，可能已经登录。")
        except Exception as e:
            print(f"初始请求发生错误: {e}")

    def logout(self):
        """注销方法"""
        if not self.params:
            print("未找到参数，请先登录。")
            return

        # 构建注销URL
        logout_url = self._build_logout_url()
        print("注销URL:", logout_url)

        # 发送注销请求
        self._send_request(logout_url, "注销")


# 示例用法
if __name__ == "__main__":
    
    # 登录
    username = ""
    password = ""
    auth = PortalAuth(username,password)

    auth.login()
    