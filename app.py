import webview
import threading
import time
from api import PortalAuth


def start_react():

    
    api = PortalAuth()
    webview.create_window("CT-Young Keep","http://localhost:5173/", js_api=api,width=400,height=500)
    webview.start(gui='qt',debug=True,icon="/img/M.png")

if __name__ == '__main__':
    
    
    
    start_react()