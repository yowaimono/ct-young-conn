import React, { useState, useEffect } from 'react';
import './Home.scss';
import { MdWifi, MdWifiOff } from 'react-icons/md';
import { Switch, Spin } from 'antd'; // 导入 Spin 组件
import { FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';

function Home() {
    const [wifiStatus, setWifiStatus] = useState(null);
    const [wifiKeepEnabled, setWifiKeepEnabled] = useState(false);
    const [currWifi, setCurrWifi] = useState(null);
    const navigate = useNavigate();
    const [isFirstLogin, setIsFirstLogin] = useState(false);
    const [countdown, setCountdown] = useState(300);
    const [isButtonDisabled, setIsButtonDisabled] = useState(false);
    const [isInitialLoginInProgress, setIsInitialLoginInProgress] = useState(false); // 新增标志位

    useEffect(() => {
        if (isFirstLogin && countdown > 0) {
            setIsInitialLoginInProgress(true);
            const timer = setInterval(() => {
                setCountdown((prev) => prev - 1);
            }, 1000);
            return () => {
                clearInterval(timer);
                setIsInitialLoginInProgress(false);
            };
        } else if (countdown === 0) {
            setIsFirstLogin(false);
            setIsButtonDisabled(false);
            setCountdown(300);
            setIsInitialLoginInProgress(false);
            handleNormalLoginAfterInitialDelay();
        }
    }, [isFirstLogin, countdown]);

    // useEffect(() => {
    //     const fetchCurrWifi = async () => {
    //         if (isInitialLoginInProgress) return; // 如果正在初次登录，跳过
    //         try {
    //             const ssid = await window.pywebview.api.get_current_wifi_ssid();
    //             setCurrWifi(ssid);
    //             const status = await window.pywebview.api.is_connected();

    //             if (!status) {
    //                 setWifiStatus("注：当前未连接到CT-Young,点击登录连接");
    //             } else {
    //                 setWifiStatus(null); // 连接成功时清除提示
    //             }
    //         } catch (error) {
    //             console.error("获取 Wi-Fi 状态失败:", error);
    //             setCurrWifi(null);
    //             setWifiStatus("获取 Wi-Fi 状态失败，请检查网络");
    //         }
    //     };

    //     fetchCurrWifi();
    //     const intervalId = setInterval(fetchCurrWifi, 3000);

    //     return () => clearInterval(intervalId);
    // }, [isInitialLoginInProgress]); // 依赖项添加标志位

    const handleWifiKeepToggle = async (checked) => {
        setWifiKeepEnabled(checked);
        try {
            if (checked) {
                await window.pywebview.api.start_task("CT-Young", 5);
                console.log('Wi-Fi Keep 已启动');
            } else {
                await window.pywebview.api.stop_task();
                console.log('Wi-Fi Keep 已停止');
            }
        } catch (error) {
            console.error("启动/停止 Wi-Fi Keep 失败:", error);
        }
    };

    const handleNormalLoginAfterInitialDelay = async () => {
        try {
            const result = await window.pywebview.api.login();
            console.log("倒计时结束后登录结果：", result);
            switch (result) {
                case 0:
                    console.log("登录成功！");
                    setWifiStatus(null);
                    break;
                case 1:
                    console.log("请尝试关闭VPN代理");
                    setWifiStatus("登录失败，请关闭代理软件");
                    break;
                case 2:
                    console.log("已登录，无需重复登陆");
                    setWifiStatus("已登录，无需重登录");
                    setTimeout(() => {
                        setWifiStatus(null);
                    }, 3000);
                    break;
                case 3:
                    setWifiStatus("未知错误");
                    console.log("未知错误");
                    break;
                case 4:
                    console.log("密码错误");
                    await handleLogout();
                    break;
                default:
                    break;
            }
            console.log("登录");
        } catch (error) {
            console.error("倒计时结束后登录失败:", error);
            setWifiStatus("登录失败，请重试");
        }
    };

    const handlePortalAction = async () => {
        try {
            if (wifiStatus === null) {
                await window.pywebview.api.logout();
                setWifiStatus("注：已注销，请重新登录");
                console.log("注销");
            } else {
                const flag = await window.pywebview.api.is_first_login();

                if (flag) {
                    setIsFirstLogin(true);
                    setIsButtonDisabled(true);
                    try {
                        await window.pywebview.api.disc();
                        setWifiStatus("初次登录需要等待3分钟...");
                        setIsButtonDisabled(true);
                        setCountdown(300);
                    } catch (error) {
                        console.error("断开连接失败:", error);
                        setWifiStatus("初始化失败，请重试");
                        setIsFirstLogin(false);
                        setIsButtonDisabled(false);
                    }
                    return;
                }

                const result = await window.pywebview.api.login();
                console.log("登陆结果：", result);
                switch (result) {
                    case 0:
                        console.log("登录成功！");
                        setWifiStatus(null);
                        break;
                    case 1:
                        console.log("请尝试关闭VPN代理");
                        setWifiStatus("登录失败，请关闭代理软件");
                        break;
                    case 2:
                        console.log("已登录，无需重复登陆");
                        setWifiStatus("已登录，无需重登录");
                        setTimeout(() => {
                            setWifiStatus(null);
                        }, 3000);
                        break;
                    case 3:
                        setWifiStatus("未知错误");
                        console.log("未知错误");
                        break;
                    case 4:
                        console.log("密码错误");
                        await handleLogout();
                        break;
                    default:
                        break;
                }
                console.log("登录");
            }
        } catch (error) {
            console.error("登录/注销失败:", error);
            setWifiStatus("登录/注销失败，请重试");
        }
    };

    const handleLogout = async () => {
        console.log("退出");
        localStorage.clear();
        await window.pywebview.api.clear_userinfo();
        navigate("/login");
    };

    return (
        <div className="home-container">
            <div className='logout-icon' onClick={handleLogout}><FiLogOut /></div>
            <div className="home-card">
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
                    <button onClick={handlePortalAction} disabled={isButtonDisabled}>
                        {isButtonDisabled ? countdown : (wifiStatus ? '登录' : '注销')}
                    </button>
                </div>
            </div>
            <div className="copyright-text">
                Copyright © {new Date().getFullYear()} CT-Young. All Rights Reserved.
            </div>
        </div>
    );
}

export default Home;