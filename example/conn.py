import subprocess

def connect_to_wifi(ssid):
    try:
        # 断开当前连接
        subprocess.run(["netsh", "wlan", "disconnect"], check=True)

        # 连接到指定的开放 WiFi
        subprocess.run(["netsh", "wlan", "connect", f"name={ssid}"], check=True)
        print(f"已成功连接到 WiFi: {ssid}")
    except subprocess.CalledProcessError as e:
        print(f"连接失败: {e}")



import subprocess
import platform

def get_current_wifi():
    system = platform.system()
    try:
        if system == "Windows":
            # Windows
            result = subprocess.run(
                ["netsh", "wlan", "show", "interfaces"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            print(result)
            for line in result.splitlines():
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":")[1].strip()
        elif system == "Darwin":
            # macOS
            result = subprocess.run(
                ["networksetup", "-getairportnetwork", "en0"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            if "Current Wi-Fi Network:" in result:
                return result.split(":")[1].strip()
        elif system == "Linux":
            # Linux
            result = subprocess.run(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            for line in result.splitlines():
                if "yes" in line:
                    return line.split(":")[1].strip()
        else:
            print(f"不支持的操作系统: {system}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"获取 WiFi 信息失败: {e}")
        return None
    except Exception as e:
        print(f"发生未知错误: {e}")
        return None


    
if __name__ == "__main__":
    # ssid = "CT-Young"
    # connect_to_wifi(ssid)
    
    ssid = get_current_wifi()
    print(ssid)

