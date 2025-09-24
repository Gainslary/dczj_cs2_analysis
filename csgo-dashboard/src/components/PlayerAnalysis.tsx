import React, { useState } from 'react';
import { Card, Input, Button, Select, Table, message, Spin, Row, Col, Statistic, Progress } from 'antd';
import { SearchOutlined, UserOutlined, TrophyOutlined, AimOutlined } from '@ant-design/icons';
import { playersAPI, PlayerStats, PlayerMatch, Player, PlayerMatchesResult } from '../services/api';

const { Option } = Select;

const PlayerAnalysis: React.FC = () => {
  const [nickname, setNickname] = useState('');
  const [selectedPlayer, setSelectedPlayer] = useState('');
  const [playerStats, setPlayerStats] = useState<PlayerStats | null>(null);
  const [playerMatches, setPlayerMatches] = useState<PlayerMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [availablePlayers, setAvailablePlayers] = useState<Player[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showTotal: (total: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  });

  const searchPlayers = async () => {
    if (!nickname.trim()) {
      message.warning('请输入玩家昵称');
      return;
    }

    setSearchLoading(true);
    try {
      const players = await playersAPI.searchPlayers(nickname);
      // 确保players是数组
      const playersArray = Array.isArray(players) ? players : [];
      setAvailablePlayers(playersArray);
      
      if (playersArray.length === 0) {
        message.info('未找到匹配的玩家');
      } else {
        message.success(`找到 ${playersArray.length} 个匹配的玩家`);
      }
    } catch (error) {
      message.error('搜索玩家失败');
      console.error('Error searching players:', error);
      setAvailablePlayers([]); // 出错时设置为空数组
    } finally {
      setSearchLoading(false);
    }
  };

  const analyzePlayer = async () => {
    if (!selectedPlayer) {
      message.warning('请选择要分析的玩家');
      return;
    }

    setLoading(true);
    try {
      // 获取玩家统计数据
      const stats = await playersAPI.getPlayerStats(selectedPlayer);
      setPlayerStats(stats);

      // 获取玩家比赛记录（第一页）
      await loadPlayerMatches(1, pagination.pageSize);

      message.success('玩家数据分析完成');
    } catch (error) {
      message.error('获取玩家数据失败');
      console.error('Error analyzing player:', error);
      setPlayerMatches([]); // 出错时设置为空数组
      setPagination(prev => ({ ...prev, total: 0 }));
    } finally {
      setLoading(false);
    }
  };

  const loadPlayerMatches = async (page: number, pageSize: number) => {
    if (!selectedPlayer) return;

    setLoading(true);
    try {
      // 获取玩家比赛记录（带分页）
      const matchesResult = await playersAPI.getPlayerMatches(selectedPlayer, page, pageSize);
      setPlayerMatches(matchesResult.matches);
      
      // 更新分页信息
      setPagination(prev => ({
        ...prev,
        current: matchesResult.pagination.page,
        pageSize: matchesResult.pagination.limit,
        total: matchesResult.pagination.total,
      }));
    } catch (error) {
      message.error('获取比赛记录失败');
      console.error('Error loading player matches:', error);
      setPlayerMatches([]);
      setPagination(prev => ({ ...prev, total: 0 }));
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (page: number, pageSize?: number) => {
    const newPageSize = pageSize || pagination.pageSize;
    loadPlayerMatches(page, newPageSize);
  };

  const getPerformanceColor = (value: number, type: 'rating' | 'winrate' | 'kd') => {
    switch (type) {
      case 'rating':
        if (value >= 1.2) return '#52c41a';
        if (value >= 1.0) return '#faad14';
        return '#ff4d4f';
      case 'winrate':
        if (value >= 60) return '#52c41a';
        if (value >= 50) return '#faad14';
        return '#ff4d4f';
      case 'kd':
        if (value >= 1.2) return '#52c41a';
        if (value >= 1.0) return '#faad14';
        return '#ff4d4f';
      default:
        return '#1890ff';
    }
  };

  const matchColumns = [
    {
      title: '比赛时间',
      dataIndex: 'match_time',
      key: 'match_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
    {
      title: '地图',
      dataIndex: 'map_name',
      key: 'map_name',
    },
    {
      title: '结果',
      dataIndex: 'match_result',
      key: 'match_result',
      render: (result: string) => {
        const resultMap: { [key: string]: { text: string; color: string } } = {
          'win': { text: '胜利', color: '#52c41a' },
          'loss': { text: '失败', color: '#ff4d4f' },
          'tie': { text: '平局', color: '#faad14' }
        };
        const resultInfo = resultMap[result] || { text: result, color: '#ccc' };
        return (
          <span style={{ 
            color: resultInfo.color,
            fontWeight: 'bold'
          }}>
            {resultInfo.text}
          </span>
        );
      },
    },
    {
      title: 'K/D/A',
      key: 'kda',
      render: (record: PlayerMatch) => `${record.kills}/${record.deaths}/${record.assists}`,
    },
    {
      title: 'K/D',
      dataIndex: 'kd_ratio',
      key: 'kd_ratio',
      render: (ratio: number) => (
        <span style={{ color: getPerformanceColor(ratio, 'kd') }}>
          {ratio.toFixed(2)}
        </span>
      ),
    },
    {
      title: 'ADR',
      dataIndex: 'adr',
      key: 'adr',
      render: (adr: number) => adr.toFixed(1),
    },
    {
      title: 'Rating',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: number) => (
        <span style={{ 
          color: getPerformanceColor(rating, 'rating'),
          fontWeight: 'bold'
        }}>
          {rating.toFixed(2)}
        </span>
      ),
    },
    {
      title: '荣誉',
      key: 'honors',
      render: (record: PlayerMatch) => (
        <div>
          {record.is_mvp && <span style={{ color: '#ffd700', fontWeight: 'bold', marginRight: 4 }}>MVP</span>}
          {record.is_svp && <span style={{ color: '#ff7f50', fontWeight: 'bold' }}>SVP</span>}
          {!record.is_mvp && !record.is_svp && <span style={{ color: '#ccc' }}>-</span>}
        </div>
      ),
    },
  ];

  return (
    <div>
      <Card title="玩家搜索" style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Input
              placeholder="输入玩家昵称进行搜索"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              onPressEnter={searchPlayers}
              prefix={<UserOutlined />}
            />
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={searchPlayers}
              loading={searchLoading}
            >
              搜索玩家
            </Button>
          </Col>
        </Row>

        {availablePlayers.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Row gutter={16} align="middle">
              <Col flex="auto">
                <Select
                  placeholder="选择要分析的玩家"
                  style={{ width: '100%' }}
                  value={selectedPlayer}
                  onChange={setSelectedPlayer}
                  showSearch
                  filterOption={(input, option) =>
                    option?.children?.toString().toLowerCase().includes(input.toLowerCase()) ?? false
                  }
                >
                  {availablePlayers.map(player => (
                    <Option key={player.steam_id} value={player.steam_id}>
                      {player.nickname} ({player.total_matches} 场比赛)
                    </Option>
                  ))}
                </Select>
              </Col>
              <Col>
                <Button
                  type="primary"
                  icon={<AimOutlined />}
                  onClick={analyzePlayer}
                  loading={loading}
                  disabled={!selectedPlayer}
                >
                  分析玩家
                </Button>
              </Col>
            </Row>
          </div>
        )}
      </Card>

      {playerStats && (
        <Card title={`${playerStats.nickname} - 数据统计`} style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="总比赛数"
                value={playerStats.total_matches}
                prefix={<TrophyOutlined />}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="胜率"
                value={playerStats.win_rate}
                suffix="%"
                valueStyle={{ color: getPerformanceColor(playerStats.win_rate, 'winrate') }}
              />
              <Progress
                percent={playerStats.win_rate}
                strokeColor={getPerformanceColor(playerStats.win_rate, 'winrate')}
                showInfo={false}
                size="small"
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="平均Rating"
                value={playerStats.avg_rating}
                precision={2}
                valueStyle={{ color: getPerformanceColor(playerStats.avg_rating, 'rating') }}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="K/D比"
                value={playerStats.kd_ratio}
                precision={2}
                valueStyle={{ color: getPerformanceColor(playerStats.kd_ratio, 'kd') }}
              />
            </Col>
          </Row>

          <Row gutter={16} style={{ marginTop: 16 }}>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="平均ADR"
                value={playerStats.avg_adr}
                precision={1}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="爆头率"
                value={(playerStats.headshot_rate * 100)}
                suffix="%"
                precision={1}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="总击杀"
                value={playerStats.total_kills}
              />
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Statistic
                title="MVP次数"
                value={playerStats.mvp_count}
                valueStyle={{ 
                  color: playerStats.mvp_count > 0 ? '#52c41a' : '#faad14'
                }}
              />
            </Col>
          </Row>
        </Card>
      )}

      {(playerMatches.length > 0 || pagination.total > 0) && (
        <Card title="最近比赛记录">
          <Spin spinning={loading}>
            <Table
              columns={matchColumns}
              dataSource={playerMatches}
              rowKey="match_id"
              pagination={{
                ...pagination,
                onChange: handleTableChange,
                onShowSizeChange: handleTableChange,
              }}
              scroll={{ x: 800 }}
            />
          </Spin>
        </Card>
      )}
    </div>
  );
};

export default PlayerAnalysis;