import sys
import os
import webview
from app.api import PortalAuth

def start_react():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    frontend_path = os.path.join(base_path, 'front', 'dist', 'index.html')
    
    api = PortalAuth()
    webview.create_window(
        "CT-Young Keep",
        frontend_path,
        js_api=api,
        width=450,
        height=650
    )
    webview.start(gui='qt', icon=os.path.join(base_path, 'img', 'ct.ico'))

if __name__ == '__main__':
    
    import os

    # 修改DNS设置
    os.system('netsh interface ip set dns name="Wi-Fi" source=static addr=8.8.8.8')

    start_react()
    

    