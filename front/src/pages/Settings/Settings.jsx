import React, { useEffect, useState } from 'react';
import { TimePicker, InputNumber, Button, Switch, Space, Typography, Card, Modal, message, ConfigProvider } from 'antd';
import { ClockCircleOutlined, FieldTimeOutlined, SettingOutlined } from '@ant-design/icons';
import moment from 'moment';
import { MdArrowBackIos } from "react-icons/md";
import "./Settings.scss"
import { Navigate, useNavigate } from 'react-router-dom';
const { Title } = Typography;

const Settings = () => {
    const navigate = useNavigate();
    const [mode, setMode] = useState(false);
    const [keepStartTime, setKeepStartTime] = useState(moment('09:00', 'HH:mm'));
    const [keepEndTime, setKeepEndTime] = useState(moment('18:00', 'HH:mm'));
    const [keepInterval, setKeepInterval] = useState(60);
    const [scheduledOnlineTime, setScheduledOnlineTime] = useState(moment('08:00', 'HH:mm'));
    const [scheduledOfflineTime, setScheduledOfflineTime] = useState(moment('22:00', 'HH:mm'));
    const [isScheduledOnlineEnabled, setIsScheduledOnlineEnabled] = useState(false);
    const [isScheduledOfflineEnabled, setIsScheduledOfflineEnabled] = useState(false);
    const [confirmModalVisible, setConfirmModalVisible] = useState(false); // State for the confirmation modal
    const [api, contextHolder] = message.useMessage(); // Use message.useMessage() hook
    const [configData, setConfigData] = useState(null);


    useEffect(() => {
        const fetchConfig = async () => {
            try {

                const config = JSON.parse(localStorage.getItem("config"));

                console.log("local config:", config);
                setConfigData(config);


                // Update state based on the fetched config
                setMode(config.mode === 1);
                setKeepStartTime(moment(`${config.keep_start[0]}:${config.keep_start[1]}`, 'HH:mm'));
                setKeepEndTime(moment(`${config.keep_end[0]}:${config.keep_end[1]}`, 'HH:mm'));
                setKeepInterval(config.check_interval);
                setScheduledOnlineTime(moment(`${config.schedule_login[0]}:${config.schedule_login[1]}`, 'HH:mm'));
                setScheduledOfflineTime(moment(`${config.schedule_logout[0]}:${config.schedule_logout[1]}`, 'HH:mm'));

                if (config.schedule_login) {
                    setIsScheduledOfflineEnabled(true);
                }

                if (config.schedule_logout) {
                    setIsScheduledOnlineEnabled(true);
                }


            } catch (error) {
                console.error("Error fetching config:", error);
            }
        };

        fetchConfig();
    }, []);


    const handleKeepStartTimeChange = (time) => {
        setKeepStartTime(time);
    };

    const handleKeepEndTimeChange = (time) => {
        setKeepEndTime(time);
    };

    const handleKeepIntervalChange = (value) => {
        setKeepInterval(value);
    };

    const handleScheduledOnlineTimeChange = (time) => {
        setScheduledOnlineTime(time);
    };

    const handleScheduledOfflineTimeChange = (time) => {
        setScheduledOfflineTime(time);
    };

    const handleScheduledOnlineToggle = (checked) => {
        setIsScheduledOnlineEnabled(checked);
    };

    const handleScheduledOfflineToggle = (checked) => {
        setIsScheduledOfflineEnabled(checked);
    };

    const handleBack = async () => {
        navigate("/home");
    }

    const handleMode = async () => {
        console.log("Mode");
    }

    const showConfirmModal = () => {
        setConfirmModalVisible(true);
    };

    const handleCancelSave = () => {
        setConfirmModalVisible(false);
    };

    const handleConfirmSave = async () => {
        setConfirmModalVisible(false);

        // Prepare the configuration data
        const configData = {
            mode: mode ? 1 : 0, // Convert boolean to 1 or 0
            keep_start: [keepStartTime.hour(), keepStartTime.minute()],
            keep_end: [keepEndTime.hour(), keepEndTime.minute()],
            check_interval: keepInterval,
            schedule_login: [scheduledOnlineTime.hour(), scheduledOnlineTime.minute()],
            schedule_logout: [scheduledOfflineTime.hour(), scheduledOfflineTime.minute()],
        };



        console.log("Saving config:", configData);

        // Call the pywebview function to save the configuration
        try {
            if (window.pywebview && window.pywebview.api && window.pywebview.api.set_config) {
                await window.pywebview.api.set_config(configData);
                api.success('保存成功!');
            } else {
                console.error("pywebview function 'set_config' is not available.");
                api.error('保存失败: pywebview 函数不可用!');
            }
        } catch (error) {
            console.error("Error saving settings:", error);
            api.error('保存失败!'); // Display error message if saving fails
        }
    };

    return (
        <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
            {contextHolder} {/* Render the context holder */}
            <div className='back' onClick={handleBack}>
                <MdArrowBackIos />
            </div>

            <Space direction="vertical" size="middle" style={{ display: 'flex', width: '100%', alignItems: 'center' }}>
                <div style={{ color: "white" }}>
                    <ClockCircleOutlined style={{ marginRight: 8 }} />
                    Keep时间段
                </div>
                <Space>
                    <TimePicker
                        value={keepStartTime} // Use value instead of defaultValue
                        format="HH:mm"
                        onChange={handleKeepStartTimeChange}
                        style={{ width: 120 }}
                    />

                    <TimePicker
                        value={keepEndTime} // Use value instead of defaultValue
                        format="HH:mm"
                        onChange={handleKeepEndTimeChange}
                        style={{ width: 120 }}
                    />
                </Space>

                <div style={{ color: "white" }}>
                    <FieldTimeOutlined style={{ marginRight: 8 }} />
                    Keep 检测间隔
                </div>
                <InputNumber
                    min={1}
                    value={keepInterval} // Use value instead of defaultValue
                    onChange={handleKeepIntervalChange}
                    style={{ width: '100%' }}
                />

                <div style={{ color: "white" }}>
                    <SettingOutlined style={{ marginRight: 8 }} />
                    定时上线
                </div>
                <Space>
                    <TimePicker
                        value={scheduledOnlineTime} // Use value instead of defaultValue
                        format="HH:mm"
                        onChange={handleScheduledOnlineTimeChange}
                        style={{ width: 120 }}
                        disabled={!isScheduledOnlineEnabled}
                    />
                    <Switch
                        style={{
                            backgroundColor: isScheduledOnlineEnabled ? '#0F9184' : '#7BA4A0', // Set background color based on state
                        }}
                        checked={isScheduledOnlineEnabled}
                        onChange={handleScheduledOnlineToggle}
                    />
                </Space>

                <div style={{ color: "white" }}>
                    <SettingOutlined style={{ marginRight: 8 }} />
                    定时下线
                </div>
                <Space>
                    <TimePicker
                        value={scheduledOfflineTime} // Use value instead of defaultValue
                        format="HH:mm"
                        onChange={handleScheduledOfflineTimeChange}
                        style={{ width: 120 }}
                        disabled={!isScheduledOfflineEnabled}
                    />
                    <Switch
                        style={{
                            backgroundColor: isScheduledOfflineEnabled ? '#0F9184' : '#7BA4A0', // Set background color based on state
                        }}
                        checked={isScheduledOfflineEnabled}
                        onChange={handleScheduledOfflineToggle}
                    />
                </Space>

                <div style={{ color: 'white' }}>
                    自动开启Keep
                </div>
                <Switch
                    style={{ marginLeft: 10, backgroundColor: mode ? '#0F9184' : '#7BA4A0', }}
                    checked={mode}
                    onChange={(checked) => setMode(checked)}
                />
                <Button type="primary" style={{ backgroundColor: '#0F9184', borderColor: '#a4dbd6' }} onClick={showConfirmModal}>
                    保存设置
                </Button>
            </Space>

            <Modal
                title="确认保存?"
                visible={confirmModalVisible}
                onOk={handleConfirmSave}
                onCancel={handleCancelSave}
                okText="确认"
                cancelText="取消"
            >
                <p>您确定要保存这些设置吗?</p>
            </Modal>
        </div >
    );
};

export default Settings;
