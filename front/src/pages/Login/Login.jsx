import React, { useState, useEffect } from 'react';
import './Login.scss';
import { AiOutlineEye, AiOutlineEyeInvisible } from 'react-icons/ai';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const navigate = useNavigate();
    // 检查是否登录
    useEffect(() => {
        // 定义一个异步函数来检查登录状态
        const checkLogin = async () => {
            try {
                const is_login = await window.pywebview.api.is_login();
                if (is_login) {
                    const info = await window.pywebview.api.get_info();

                    console.log("info: ", info);
                    localStorage.setItem("username", info.username);
                    localStorage.setItem("password", info.password);

                    navigate("/home");
                }


            } catch (error) {
                console.error("检查登录状态失败:", error);
            }
        };

        // 调用异步函数
        checkLogin();
    }, [navigate]); // 依赖项中包含 navigate

    const [account, setAccount] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };


    const handleLogin = async () => {
        // 处理登录逻辑
        await window.pywebview.api.set_info(account, password);

        localStorage.setItem("username", account);
        localStorage.setItem("password", password);
        await window.pywebview.api.get_params();

        navigate("/home");

        console.log('Account:', account);
        console.log('Password:', password);
    };

    return (
        <div className="login-container">
            <div className="login-card">
                <h2 style={{ color: '#A4DBD6' }}>欢迎使用Min!</h2>
                <div className="input-group">
                    {/* <label htmlFor="account">Account:</label> */}
                    <input
                        type="text"
                        id="account"
                        placeholder="学号" // 添加提示文字
                        value={account}
                        onChange={(e) => setAccount(e.target.value)}
                    />
                </div>
                <div className="input-group">
                    {/* <label htmlFor="password">Password:</label> */}
                    <input
                        type={showPassword ? 'text' : 'password'}
                        id="password"
                        value={password}
                        placeholder="密码(6位)"
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>
                <button onClick={handleLogin}>进入</button>
            </div>
        </div >
    );
}

export default Login;