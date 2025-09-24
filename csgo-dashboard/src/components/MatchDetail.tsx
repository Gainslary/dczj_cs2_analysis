import React, { useState, useEffect } from 'react';
import { Modal, Table, Tag, Spin, message, Typography, Row, Col, Card } from 'antd';
import { matchesAPI, MatchDetailResponse, MatchPlayer } from '../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

interface MatchDetailProps {
  visible: boolean;
  matchId: string | null;
  onClose: () => void;
}

const MatchDetail: React.FC<MatchDetailProps> = ({ visible, matchId, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [matchDetail, setMatchDetail] = useState<MatchDetailResponse | null>(null);

  const fetchMatchDetail = async () => {
    if (!matchId) return;
    
    setLoading(true);
    try {
      const detail = await matchesAPI.getMatchDetail(matchId);
      setMatchDetail(detail);
    } catch (error) {
      message.error('获取比赛详情失败');
      console.error('Error fetching match detail:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && matchId) {
      fetchMatchDetail();
    }
  }, [visible, matchId]);

  const getTeamColor = (teamId: number) => {
    return teamId === 2 ? '#ff4d4f' : '#52c41a'; // T队红色，CT队绿色
  };

  const getTeamName = (teamId: number) => {
    return teamId === 2 ? 'T' : 'CT';
  };

  const columns = [
    {
      title: '玩家',
      dataIndex: 'nickname',
      key: 'nickname',
      render: (nickname: string, record: MatchPlayer) => (
        <div>
          <div style={{ fontWeight: 'bold' }}>{nickname || record.username}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            <Tag color={getTeamColor(record.team_id)}>
              {getTeamName(record.team_id)}
            </Tag>
            等级 {record.platform_level}
          </div>
        </div>
      ),
    },
    {
      title: 'K/D/A',
      key: 'kda',
      render: (record: MatchPlayer) => (
        <span>{record.kills}/{record.deaths}/{record.assists}</span>
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
      render: (rating: number) => rating.toFixed(2),
    },
    {
      title: 'Rating 2.0',
      dataIndex: 'rating2',
      key: 'rating2',
      render: (rating2: number) => rating2.toFixed(2),
    },
    {
      title: 'KAST%',
      dataIndex: 'kast',
      key: 'kast',
      render: (kast: number) => `${(kast * 100).toFixed(1)}%`,
    },
    {
          title: 'RWS',
          dataIndex: 'rws',
          key: 'rws',
          render: (rws: number | null) => rws ? rws.toFixed(1) : '-',
        },
    {
      title: '爆头率',
      key: 'headshot_rate',
      render: (record: MatchPlayer) => `${record.per_headshot.toFixed(1)}%`,
    },
    {
      title: '首杀/首死',
      key: 'first_kills',
      render: (record: MatchPlayer) => `${record.first_kill}/${record.first_death}`,
    },
    {
      title: 'AWP击杀',
      dataIndex: 'awp_kill',
      key: 'awp_kill',
    },
    {
      title: '荣誉',
      key: 'honors',
      render: (record: MatchPlayer) => (
        <div>
          {record.is_mvp && <Tag color="gold">MVP</Tag>}
          {record.is_svp && <Tag color="orange">SVP</Tag>}
        </div>
      ),
    },
  ];

  const formatTime = (timeStr: string) => {
    // 检查是否是时间戳格式（纯数字字符串）
    if (/^\d+$/.test(timeStr)) {
      // 如果是时间戳，转换为毫秒（JavaScript时间戳是毫秒）
      const timestamp = parseInt(timeStr) * 1000;
      return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss');
    }
    // 如果不是时间戳，按原来的方式处理
    return dayjs(timeStr).format('YYYY-MM-DD HH:mm:ss');
  };

  const getWinnerTeam = (winnerId: number) => {
    return winnerId === 2 ? 'T队' : 'CT队';
  };

  return (
    <Modal
      title="比赛详情"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1200}
      style={{ top: 20 }}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : matchDetail ? (
        <div>
          {/* 比赛基本信息 */}
          <Card style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Text strong>比赛ID:</Text>
                <br />
                <Text>{matchDetail.match_info.match_id}</Text>
              </Col>
              <Col span={6}>
                <Text strong>地图:</Text>
                <br />
                <Text>{matchDetail.match_info.map_name}</Text>
              </Col>
              <Col span={6}>
                <Text strong>开始时间:</Text>
                <br />
                <Text>{formatTime(matchDetail.match_info.start_time)}</Text>
              </Col>
              <Col span={6}>
                <Text strong>获胜方:</Text>
                <br />
                <Tag color={getTeamColor(matchDetail.match_info.match_winner)}>
                  {getWinnerTeam(matchDetail.match_info.match_winner)}
                </Tag>
              </Col>
            </Row>
          </Card>

          {/* 玩家数据表格 */}
          <Table
            columns={columns}
            dataSource={matchDetail.players}
            rowKey="steam_id"
            pagination={false}
            size="small"
            scroll={{ x: 1000 }}
            rowClassName={(record) => 
              record.is_win ? 'winner-row' : 'loser-row'
            }
          />

          <style>{`
            .winner-row {
              background-color: #f6ffed;
            }
            .loser-row {
              background-color: #fff2f0;
            }
          `}</style>
        </div>
      ) : null}
    </Modal>
  );
};

export default MatchDetail;