import React, { useState, useEffect } from 'react';
import './Home.scss';

import { MdWifi, MdWifiOff } from 'react-icons/md';
import { Switch } from 'antd';
import { FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { FiSettings } from "react-icons/fi";
// 定义 Wi-Fi 状态枚举
const WifiStatus = {
    IDLE: 'IDLE', // 空闲状态
    CONNECTING: 'CONNECTING', // 正在连接
    CONNECTED: 'CONNECTED', // 已连接
    DISCONNECTING: 'DISCONNECTING', // 正在断开
    NOT_CT_YOUNG: 'NOT_CT_YOUNG', // 未连接到 CT-Young
    UNAUTHENTICATED: 'UNAUTHENTICATED', // 已连接但未认证
    LOGIN_FAILED: 'LOGIN_FAILED', // 登录失败
    LOGGED_IN: 'LOGGED_IN', // 已登录
    UNKNOWN_ERROR: 'UNKNOWN_ERROR', // 未知错误
    PASSWORD_ERROR: 'PASSWORD_ERROR', // 密码错误
    LOGOUT_SUCCESS: 'LOGOUT_SUCCESS', // 注销成功
    LOGOUT_FAILED: 'LOGOUT_FAILED', // 注销失败
    SERVER_BUSY: 'SERVER_BUSY', // 服务器繁忙
    INIT_ERROR: 'INIT_ERROR', // 初始化错误
    FIRST_LOGIN_WAIT: 'FIRST_LOGIN_WAIT', // 初次登录等待
    GET_WIFI_FAILED: 'GET_WIFI_FAILED', // 获取WIFI信息失败
};

function Home() {
    const [wifiStatus, setWifiStatus] = useState(WifiStatus.IDLE); // Wi-Fi 状态
    const [wifiKeepEnabled, setWifiKeepEnabled] = useState(false); // Wi-Fi Keep 开关
    const [currWifi, setCurrWifi] = useState(null); // 当前 Wi-Fi SSID
    const [isFirstLogin, setIsFirstLogin] = useState(false); // 是否初次登录
    const [countdown, setCountdown] = useState(300); // 初次登录倒计时
    const [isLoading, setIsLoading] = useState(false); // 操作加载状态
    const navigate = useNavigate();

    // 根据状态码获取提示信息
    const getStatusMessage = () => {
        switch (wifiStatus) {
            case WifiStatus.IDLE:
                return null;
            case WifiStatus.CONNECTING:
                return "正在连接...";
            case WifiStatus.CONNECTED:
                return null;
            case WifiStatus.DISCONNECTING:
                return "正在断开...";
            case WifiStatus.NOT_CT_YOUNG:
                return "注：当前未连接到CT-Young，点击登录连接";
            case WifiStatus.UNAUTHENTICATED:
                return "未认证，点击登录认证";
            case WifiStatus.LOGIN_FAILED:
                return "登录失败，请关闭代理软件";
            case WifiStatus.LOGGED_IN:
                return "已登录，无需重复登录";
            case WifiStatus.UNKNOWN_ERROR:
                return "未知错误";
            case WifiStatus.PASSWORD_ERROR:
                return "密码错误";
            case WifiStatus.LOGOUT_SUCCESS:
                return "已注销，请重新登录";
            case WifiStatus.LOGOUT_FAILED:
                return "注销失败，请重试";
            case WifiStatus.SERVER_BUSY:
                return "服务器繁忙，稍后重试";
            case WifiStatus.INIT_ERROR:
                return "初始化失败，请重试";
            case WifiStatus.FIRST_LOGIN_WAIT:
                return "初次登录需要等待5分钟...";
            case WifiStatus.GET_WIFI_FAILED:
                return "获取 Wi-Fi 状态失败，请检查网络";
            default:
                return "操作失败";
        }
    };

    // 处理登录结果的统一函数
    const handleLoginResult = (result) => {
        switch (result) {
            case 0:
                console.log("登录成功！");
                setWifiStatus(WifiStatus.CONNECTED);
                break;
            case 1:
                console.log("请尝试关闭VPN代理");
                setWifiStatus(WifiStatus.LOGIN_FAILED);
                break;
            case 2:
                console.log("已登录，无需重复登录");
                setWifiStatus(WifiStatus.LOGGED_IN);
                setTimeout(() => setWifiStatus(WifiStatus.IDLE), 3000);
                break;
            case 3:
                console.log("未知错误");
                setWifiStatus(WifiStatus.UNKNOWN_ERROR);
                break;
            case 4:
                console.log("密码错误");
                handleLogout();
                break;
            default:
                console.log("未处理的结果:", result);
                setWifiStatus(WifiStatus.UNKNOWN_ERROR);
        }
    };

    // 检查网络是否可用
    const checkNetworkAvailability = async () => {
        try {
            // 请求一个公共网页（如 Google）来检测网络连通性
            const response = await fetch('https://www.baidu.com', {
                method: 'HEAD', // 只请求头部，减少数据量
                mode: 'no-cors', // 避免跨域问题
                timeout: 5000, // 设置超时
            });
            return true; // 请求成功，网络可用
        } catch (error) {
            console.error("网络检测失败:", error);
            return false; // 请求失败，网络不可用
        }
    };


    useEffect(() => {
        const checkFirstLogin = async () => {
            try {
                const isFirst = await window.pywebview.api.is_first_login();
                if (isFirst) {
                    setIsFirstLogin(true);
                    await window.pywebview.api.disc();
                } else {
                    await handleLogin();
                }
            } catch (error) {
                console.error("Initial login check failed:", error);
                setWifiStatus(WifiStatus.INIT_ERROR);
            }
        };

        checkFirstLogin();

        const loadConfig = async () => {
            // 加载
            try {
                if (window.pywebview && window.pywebview.api && window.pywebview.api.get_config) {
                    const config = await window.pywebview.api.get_config();
                    console.log("Initial config:", config);
                    // 成功拿到
                    localStorage.setItem("config", JSON.stringify(config));


                    if (config.mode == 1) {
                        setWifiKeepEnabled(true);
                    }

                } else {
                    console.warn("pywebview function 'get_config' is not available. Using default values.");
                }
            } catch (error) {
                console.error("Error fetching config:", error);
            }

        }

        loadConfig();
    }, []);


    // 检查当前 Wi-Fi 状态
    useEffect(() => {
        const fetchCurrWifi = async () => {
            if (isLoading) return; // 正在操作时跳过检查
            try {
                const ssid = await window.pywebview.api.get_current_wifi_ssid();
                setCurrWifi(ssid);

                if (ssid !== "CT-Young") {
                    setWifiStatus(WifiStatus.NOT_CT_YOUNG);
                } else {
                    // 已连接到 CT-Young，检查网络是否可用
                    const isNetworkAvailable = await checkNetworkAvailability();
                    if (isNetworkAvailable) {
                        setWifiStatus(WifiStatus.CONNECTED); // 网络可用，清除提示
                    } else {
                        setWifiStatus(WifiStatus.UNAUTHENTICATED); // 网络不可用，提示未认证
                    }
                }
            } catch (error) {
                console.error("获取 Wi-Fi 状态失败:", error);
                setCurrWifi(null);
                setWifiStatus(WifiStatus.GET_WIFI_FAILED);
            }
        };

        fetchCurrWifi();

        const intervalId = setInterval(async () => {
            await fetchCurrWifi(); // 每次定时器触发时都调用 fetchCurrWifi

            // 检查是否需要自动登录
            if (wifiKeepEnabled && currWifi === "CT-Young" && wifiStatus === WifiStatus.UNAUTHENTICATED) {
                console.log("Wi-Fi Keep 开启且未认证，尝试自动登录...");
                await handleLogin();
            }
        }, 3000);

        return () => clearInterval(intervalId);
    }, [isLoading, wifiKeepEnabled, wifiStatus, currWifi]);

    // 初次登录倒计时
    useEffect(() => {
        let timer;
        if (isFirstLogin && countdown > 0) {
            setIsLoading(true);
            setWifiStatus(WifiStatus.FIRST_LOGIN_WAIT);
            timer = setInterval(() => {
                setCountdown((prev) => prev - 1);
            }, 1000);
        } else if (isFirstLogin && countdown === 0) {
            setIsFirstLogin(false);
            setCountdown(300);
            setIsLoading(false);
            handleLogin(); // 倒计时结束后自动登录
        }
        return () => clearInterval(timer);
    }, [isFirstLogin, countdown]);

    // Wi-Fi Keep 开关
    const handleWifiKeepToggle = async (checked) => {
        setWifiKeepEnabled(checked);
        try {
            if (checked) {
                await window.pywebview.api.start_task("CT-Young");
                console.log('Wi-Fi Keep 已启动');
            } else {
                await window.pywebview.api.stop_task();
                console.log('Wi-Fi Keep 已停止');
            }
        } catch (error) {
            console.error("启动/停止 Wi-Fi Keep 失败:", error);
            setWifiStatus(WifiStatus.UNKNOWN_ERROR);
        }
    };

    // 处理登录
    const handleLogin = async () => {
        setIsLoading(true);
        setWifiStatus(WifiStatus.CONNECTING);
        try {
            const result = await window.pywebview.api.login();
            console.log("登录结果：", result);
            handleLoginResult(result);
        } catch (error) {
            console.error("登录失败:", error);
            setWifiStatus(WifiStatus.LOGIN_FAILED);
        } finally {
            setIsLoading(false);
        }
    };

    // 处理注销
    const handleLogoutAction = async () => {
        setIsLoading(true);
        setWifiStatus(WifiStatus.DISCONNECTING);
        try {
            const flag = await window.pywebview.api.logout();
            switch (flag) {
                case 0:
                    console.log("注销成功！");
                    setWifiStatus(WifiStatus.LOGOUT_SUCCESS);
                    break;
                case 1:
                    console.log("请求发送失败");
                    setWifiStatus(WifiStatus.SERVER_BUSY);
                    break;
                case 2:
                    console.log("基础信息损坏，请退出重新登录");
                    setWifiStatus(WifiStatus.UNKNOWN_ERROR);
                    break;
                case 3:
                    console.log("注销失败");
                    setWifiStatus(WifiStatus.LOGOUT_FAILED);
                    setTimeout(() => setWifiStatus(WifiStatus.IDLE), 3000);
                    break;
                default:
                    console.log(flag);
                    setWifiStatus(WifiStatus.LOGOUT_FAILED);
            }
        } catch (error) {
            console.error("注销失败:", error);
            setWifiStatus(WifiStatus.LOGOUT_FAILED);
        } finally {
            setIsLoading(false);
        }
    };

    // 点击按钮的主操作
    const handlePortalAction = async () => {
        if (isLoading) return;

        if (wifiStatus === WifiStatus.CONNECTED && currWifi === "CT-Young") {
            // 已连接且网络可用，执行注销
            await handleLogoutAction();
        } else {
            // 未连接或未认证，执行登录
            try {
                const isFirst = await window.pywebview.api.is_first_login();
                if (isFirst) {
                    setIsFirstLogin(true);
                    await window.pywebview.api.disc();
                } else {
                    await handleLogin();
                }
            } catch (error) {
                console.error("初次登录检查或断开失败:", error);
                setWifiStatus(WifiStatus.INIT_ERROR);
                setIsFirstLogin(false);
                setIsLoading(false);
            }
        }
    };

    // 退出应用
    const handleLogout = async () => {
        console.log("退出");
        localStorage.clear();
        await window.pywebview.api.clear_userinfo();
        navigate("/login");
    };

    const handleSetting = async () => {
        console.log("设置");
        navigate("/settings");
    }

    const statusMessage = getStatusMessage();

    return (
        <div className="home-container">
            <div className="logout-icon" onClick={handleLogout}>
                <FiLogOut />
            </div>

            <div className="settings-icon" onClick={handleSetting}>
                <FiSettings />
            </div>
            <div className="home-card">
                <div className="wifi-icon-row">
                    {currWifi ? <MdWifi className="wifi-icon" /> : <MdWifiOff className="wifi-icon" />}
                </div>
                <div className="wifi-status-row">
                    <p>当前 Wi-Fi：{currWifi || '未连接'}</p>
                </div>
                <div className="wifi-keep-row">
                    <label className="wifi-keep-label">
                        Wi-Fi Keep:
                        <Switch
                            className="switch"
                            checked={wifiKeepEnabled}
                            onChange={handleWifiKeepToggle}
                            disabled={isLoading}
                        />
                    </label>
                </div>
                <div className="wifi-notice">
                    {statusMessage && <span>{statusMessage}</span>}
                </div>
                <div className="portal-action-row">
                    {isLoading ? (
                        <div className="loading-spinner-container">
                            {isFirstLogin ? (
                                <span>等待 {countdown}s</span>
                            ) : (
                                <div className="loading-spinner"></div>
                            )}
                        </div>
                    ) : (
                        <button onClick={handlePortalAction}>
                            {(wifiStatus === WifiStatus.CONNECTED && currWifi === "CT-Young") ? '注销' : '登录'}
                        </button>
                    )}
                </div>
            </div>
            <div className="copyright-text">
                Copyright © {new Date().getFullYear()} CT-Young. All Rights Reserved.
            </div>
        </div>
    );
}

export default Home;
