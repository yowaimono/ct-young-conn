import React, { useState, useEffect } from 'react';
import './Home.scss';
import { MdWifi, MdWifiOff } from 'react-icons/md';
import { Switch } from 'antd'; // 导入 Switch 组件
import { FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
function Home() {
    const [wifiStatus, setWifiStatus] = useState(null);
    const [wifiKeepEnabled, setWifiKeepEnabled] = useState(false);

    // 0 连接并登陆成功，1连接但是未登录，2未连接（连接的非CT-Young）
    const [currWifi, setCurrWifi] = useState(null);

    const navigate = useNavigate();

    useEffect(() => {
        const fetchCurrWifi = async () => {
            try {
                const ssid = await window.pywebview.api.get_current_wifi_ssid(); // 占位：模拟获取 Wi-Fi SSID
                setCurrWifi(ssid);
                const status = await window.pywebview.api.is_connected();

                if (!status) {
                    // 已连接
                    setWifiStatus("注：当前未连接到CT-Young,点击登录连接")
                }
            } catch (error) {
                console.error("获取 Wi-Fi 状态失败:", error);
                setCurrWifi(null); // 设置为未连接
                setWifiStatus("获取 Wi-Fi 状态失败，请检查网络");
            }
        };

        fetchCurrWifi();
        const intervalId = setInterval(fetchCurrWifi, 3000); // 每 3 秒更新一次 Wi-Fi 状态

        return () => clearInterval(intervalId);
    }, []);

    const handleWifiKeepToggle = async (checked) => {
        setWifiKeepEnabled(checked);
        try {
            if (checked) {

                // 默认五秒刷新
                await window.pywebview.api.start_task("CT-Young", 5);
                console.log('Wi-Fi Keep 已启动');
            } else {

                await window.pywebview.api.stop_task();
                console.log('Wi-Fi Keep 已停止');
            }
        } catch (error) {
            console.error("启动/停止 Wi-Fi Keep 失败:", error);
            // 可以添加错误提示给用户
        }
    };

    const handlePortalAction = async () => {
        try {
            if (wifiStatus === null) {

                await window.pywebview.api.logout();
                setWifiStatus("注：已注销，请重新登录")
                console.log("注销");
            } else {

                // window.pywebview.api.connect_to_wifi("CT-Young");

                const result = await window.pywebview.api.login();
                setWifiStatus(null);
                console.log("登录");
            }
        } catch (error) {
            console.error("登录/注销失败:", error);
            setWifiStatus("登录/注销失败，请重试");
        }
    };

    const handleLogout = async () => {
        // 处理退出逻辑，例如跳转到登录页面
        console.log("退出");
        localStorage.clear();
        await window.pywebview.api.clear_data();

        navigate("/login");
        // window.location.href = '/login'; // 示例：跳转到登录页面
    };



    return (
        <div className="home-container">
            <div className='logout-icon' onClick={handleLogout}><FiLogOut /></div>
            <div className="home-card">
                {/* <h2>Home Page</h2> */}
                <div className="wifi-icon-row">
                    {currWifi ? <MdWifi className="wifi-icon" /> : <MdWifiOff className="wifi-icon" />}
                </div>
                <div className="wifi-status-row">
                    <p>当前 Wi-Fi：{currWifi ? currWifi : '未连接'}</p>
                </div>
                <div className="wifi-keep-row">
                    <label className="wifi-keep-label">
                        Wi-Fi Keep:
                        <Switch className='switch' checked={wifiKeepEnabled} onChange={handleWifiKeepToggle} />
                    </label>
                </div>
                <div className='wifi-notice'>
                    <span>{wifiStatus ? wifiStatus : ""}</span>
                </div>
                <div className="portal-action-row">
                    <button onClick={handlePortalAction}>
                        {wifiStatus ? '登录' : '注销'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Home;
