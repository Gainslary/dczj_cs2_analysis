import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import { TrophyOutlined, UserOutlined, CrownOutlined } from '@ant-design/icons';
import MatchesDashboard from './components/MatchesDashboard';
import PlayerAnalysis from './components/PlayerAnalysis';
import Leaderboard from './components/Leaderboard';
import './App.css';

const { Header, Content } = Layout;
const { Title } = Typography;

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 设置页面标题
  useEffect(() => {
    document.title = '大畜之家cs对局分析平台';
  }, []);
  
  // 根据当前路径确定选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.includes('/players')) return 'players';
    if (path.includes('/leaderboard')) return 'leaderboard';
    return 'matches';
  };

  const menuItems = [
    {
      key: 'matches',
      icon: <TrophyOutlined />,
      label: '比赛列表',
    },
    {
      key: 'players',
      icon: <UserOutlined />,
      label: '玩家分析',
    },
    {
      key: 'leaderboard',
      icon: <CrownOutlined />,
      label: '排行榜',
    },
  ];

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="header-content">
          <Title level={3} className="app-title">
            大畜之家 CS2 数据分析平台
          </Title>
          <Menu
            theme="light"
            mode="horizontal"
            selectedKeys={[getSelectedKey()]}
            items={menuItems}
            onClick={({ key }) => {
              if (key === 'matches') navigate('/matches');
              else if (key === 'players') navigate('/players');
              else if (key === 'leaderboard') navigate('/leaderboard');
            }}
            className="app-menu"
          />
        </div>
      </Header>
      <Content className="app-content">
        <Routes>
          <Route path="/" element={<Navigate to="/matches" replace />} />
          <Route 
            path="/matches" 
            element={<MatchesDashboard />} 
          />
          <Route 
            path="/players" 
            element={<PlayerAnalysis />} 
          />
          <Route 
            path="/leaderboard" 
            element={<Leaderboard />} 
          />
        </Routes>
      </Content>
    </Layout>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
