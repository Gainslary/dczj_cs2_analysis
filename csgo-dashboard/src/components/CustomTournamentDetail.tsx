import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Typography,
  Tag,
  Button,
  Table,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tooltip,
  Popconfirm,
  Tabs,
  Statistic,
  List,
  Avatar,
  Divider
} from 'antd';
import {
  TeamOutlined,
  TrophyOutlined,
  PlusOutlined,
  DeleteOutlined,
  LinkOutlined,
  DisconnectOutlined,
  UserOutlined,
  CalendarOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  CustomTournamentDetail,
  CustomTournamentTeam,
  CustomTournamentMatch,
  AvailableMatch,
  customTournamentsAPI,
  playersAPI,
  Player,
  LeaderboardPlayer,
  CustomTournamentTeamStatsItem,
  leaderboardAPI,
  StatType,
  TournamentLeaderboardResponse
} from '../services/api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Search } = Input;

interface CustomTournamentDetailProps {
  tournamentId: number;
  onBack: () => void;
}

const CustomTournamentDetailComponent: React.FC<CustomTournamentDetailProps> = ({
  tournamentId,
  onBack
}) => {
  const [tournament, setTournament] = useState<CustomTournamentDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [linkMatchModalVisible, setLinkMatchModalVisible] = useState(false);
  const [availableMatches, setAvailableMatches] = useState<AvailableMatch[]>([]);
  const [availableMatchesLoading, setAvailableMatchesLoading] = useState(false);
  const [selectedMatches, setSelectedMatches] = useState<string[]>([]);
  const [searchPlayers, setSearchPlayers] = useState<Player[]>([]);
  const [editTeamModalVisible, setEditTeamModalVisible] = useState(false);
  const [editingTeam, setEditingTeam] = useState<CustomTournamentTeam | null>(null);
  const [editTeamName, setEditTeamName] = useState<string>('');
  const [editTeamCaptainUid, setEditTeamCaptainUid] = useState<number | undefined>(undefined);
  const [form] = Form.useForm();
  const [playerUsernameMap, setPlayerUsernameMap] = useState<Record<number, string>>({});

  // 新增：队伍统计与排行榜相关状态
  const [teamStats, setTeamStats] = useState<CustomTournamentTeamStatsItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardPlayer[]>([]);
  const [leaderboardStatType, setLeaderboardStatType] = useState<string>('rating2');
  const [leaderboardMapFilter, setLeaderboardMapFilter] = useState<string>('');
  const [statTypes, setStatTypes] = useState<StatType[]>([]);
  const [availableMaps, setAvailableMaps] = useState<string[]>([]);

  // 获取比赛详情
  const fetchTournamentDetail = async () => {
    setLoading(true);
    try {
      const response = await customTournamentsAPI.getTournamentDetail(tournamentId);
      if (response.success) {
        setTournament(response.data);
      }
    } catch (error) {
      console.error('获取比赛详情失败:', error);
      message.error('获取比赛详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 新增：获取队伍统计
  const fetchTeamStats = async () => {
    try {
      const res = await customTournamentsAPI.getTeamStats(tournamentId);
      if (res.success) {
        setTeamStats(res.data);
      }
    } catch (error) {
      console.error('获取队伍统计失败:', error);
      message.error('获取队伍统计失败');
    }
  };

  // 新增：获取排行榜统计类型与地图过滤选项
  const fetchStatTypesAndFilters = async () => {
    try {
      const [types, filters] = await Promise.all([
        leaderboardAPI.getStatsTypes(),
        leaderboardAPI.getFilters()
      ]);
      setStatTypes(types);
      setAvailableMaps(filters.maps || []);
    } catch (error) {
      console.warn('获取排行榜选项失败，使用默认值', error);
      setStatTypes([
        { key: 'rating2', name: 'Rating2', description: '' },
        { key: 'kd_ratio', name: 'K/D', description: '' },
        { key: 'avg_kills', name: '平均击杀', description: '' },
        { key: 'avg_assists', name: '平均助攻', description: '' },
        { key: 'avg_deaths', name: '平均死亡', description: '' },
      ]);
    }
  };

  // 新增：获取比赛范围排行榜
  const fetchLeaderboard = async () => {
    try {
      const res: TournamentLeaderboardResponse = await customTournamentsAPI.getTournamentLeaderboard(
        tournamentId,
        leaderboardStatType,
        leaderboardMapFilter
      );
      if (res.success) {
        setLeaderboard(res.data);
      }
    } catch (error) {
      console.error('获取排行榜失败:', error);
      message.error('获取排行榜失败');
    }
  };

  // 初始加载
  useEffect(() => {
    fetchTournamentDetail();
    fetchTeamStats();
    fetchStatTypesAndFilters();
  }, [tournamentId]);

  // 切换统计类型或地图过滤时刷新排行榜
  useEffect(() => {
    fetchLeaderboard();
  }, [tournamentId, leaderboardStatType, leaderboardMapFilter]);

  // 获取可用比赛列表
  const fetchAvailableMatches = async (search?: string) => {
    setAvailableMatchesLoading(true);
    try {
      const response = await customTournamentsAPI.getAvailableMatches(1, 50, search);
      if (response.success) {
        setAvailableMatches(response.data);
      }
    } catch (error) {
      console.error('获取可用比赛失败:', error);
      message.error('获取可用比赛失败');
    } finally {
      setAvailableMatchesLoading(false);
    }
  };

  // 搜索玩家
  const handleSearchPlayers = async (nickname: string) => {
    try {
      const players = await playersAPI.searchPlayers(nickname);
      setSearchPlayers(players);
    } catch (error) {
      console.error('搜索玩家失败:', error);
    }
  };

  useEffect(() => {
    fetchTournamentDetail();
  }, [tournamentId]);

  // 加载所有玩家以建立 uid->username 映射
  const loadAllPlayersUsernameMap = async () => {
    try {
      const allPlayers = await playersAPI.searchPlayers('');
      const map: Record<number, string> = {};
      (allPlayers || []).forEach((p) => {
        if (typeof p.uid === 'number') {
          map[p.uid] = p.username || String(p.uid);
        }
      });
      setPlayerUsernameMap(map);
    } catch (error) {
      console.error('加载玩家列表失败:', error);
    }
  };

  useEffect(() => {
    loadAllPlayersUsernameMap();
  }, []);

  // 状态标签颜色映射
  const getStatusColor = (status: string) => {
    const colorMap: Record<string, string> = {
      draft: 'default',
      active: 'processing',
      completed: 'success',
      cancelled: 'error',
    };
    return colorMap[status] || 'default';
  };

  // 状态文本映射
  const getStatusText = (status: string) => {
    const textMap: Record<string, string> = {
      draft: '草稿',
      active: '进行中',
      completed: '已完成',
      cancelled: '已取消',
    };
    return textMap[status] || status;
  };

  // 格式化时间
  const formatTime = (timestamp: number) => {
    return dayjs(timestamp * 1000).format('YYYY-MM-DD HH:mm');
  };

  // 关联比赛
  const handleLinkMatches = async () => {
    if (selectedMatches.length === 0) {
      message.warning('请选择要关联的比赛');
      return;
    }

    try {
      for (const matchId of selectedMatches) {
        await customTournamentsAPI.linkMatch(tournamentId, {
          match_id: matchId,
          match_order: 0,
        });
      }
      message.success('关联比赛成功');
      setLinkMatchModalVisible(false);
      setSelectedMatches([]);
      fetchTournamentDetail();
    } catch (error) {
      console.error('关联比赛失败:', error);
      message.error('关联比赛失败');
    }
  };

  // 取消关联比赛
  const handleUnlinkMatch = async (linkId: number) => {
    try {
      await customTournamentsAPI.unlinkMatch(tournamentId, linkId);
      message.success('取消关联成功');
      fetchTournamentDetail();
    } catch (error) {
      console.error('取消关联失败:', error);
      message.error('取消关联失败');
    }
  };

  // 删除队伍
  const handleDeleteTeam = async (teamId: number) => {
    try {
      const res = await customTournamentsAPI.deleteTeam(tournamentId, teamId);
      if (res.success) {
        message.success('删除队伍成功');
        fetchTournamentDetail();
      } else {
        message.error((res as any)?.message || '删除队伍失败');
      }
    } catch (error) {
      console.error('删除队伍失败:', error);
      message.error('删除队伍失败');
    }
  };

  // 打开编辑队伍弹窗
  const openEditTeamModal = (team: CustomTournamentTeam) => {
    setEditingTeam(team);
    setEditTeamName(team.team_name || '');
    setEditTeamCaptainUid(team.captain_uid ?? undefined);
    setEditTeamModalVisible(true);
  };

  // 保存队伍编辑
  const handleSaveEditTeam = async () => {
    if (!editingTeam) return;
    const name = (editTeamName || '').trim();
    if (!name) {
      message.warning('队伍名称不能为空');
      return;
    }
    try {
      await customTournamentsAPI.updateTeam(
        tournamentId,
        editingTeam.id,
        { team_name: name, captain_uid: typeof editTeamCaptainUid === 'number' ? editTeamCaptainUid : null }
      );
      message.success('队伍信息已更新');
      setEditTeamModalVisible(false);
      setEditingTeam(null);
      setEditTeamName('');
      setEditTeamCaptainUid(undefined);
      fetchTournamentDetail();
    } catch (error) {
      console.error('更新队伍失败:', error);
      message.error('更新队伍失败');
    }
  };

  // 队伍表格列定义
  const teamColumns: ColumnsType<CustomTournamentTeam> = [
    {
      title: '队伍名称',
      dataIndex: 'team_name',
      key: 'team_name',
      render: (text: string) => (
        <span>
          <TeamOutlined /> {text}
        </span>
      ),
    },
    {
      title: '队长',
      dataIndex: 'captain_username',
      key: 'captain_username',
      render: (text: string, record: CustomTournamentTeam) => (
        text || record.captain_username || '未设置'
      ),
    },
    {
      title: '队员数量',
      dataIndex: 'player_uids',
      key: 'player_count',
      render: (uids: number[]) => (
        <span>
          <UserOutlined /> {uids ? uids.length : 0}
        </span>
      ),
    },
    {
      title: '胜负记录',
      key: 'record',
      render: (_, record: CustomTournamentTeam) => {
        const stats = teamStats.find(s => s.team_id === record.id);
        const wins = stats?.wins ?? 0;
        const losses = stats?.losses ?? 0;
        const matches = stats?.matches_played ?? (wins + losses);
        return (
          <span>
            {wins}胜 {losses}负{typeof matches === 'number' ? `（${matches}场）` : ''}
          </span>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record: CustomTournamentTeam) => (
        <Space>
          <Button type="text" size="small" onClick={() => openEditTeamModal(record)}>
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个队伍吗？"
            onConfirm={() => {
              handleDeleteTeam(record.id);
            }}
          >
            <Button type="text" danger size="small">
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 比赛表格列定义
  const matchColumns: ColumnsType<CustomTournamentMatch> = [
    {
      title: '比赛ID',
      dataIndex: 'match_id',
      key: 'match_id',
      width: 120,
      ellipsis: true,
    },
    {
      title: '地图',
      dataIndex: 'map_name',
      key: 'map_name',
      width: 100,
    },
    {
      title: '比赛时间',
      dataIndex: 'match_start_time',
      key: 'match_start_time',
      width: 150,
      render: (timestamp: number) => timestamp ? formatTime(timestamp) : '-',
    },
    {
      title: '比分',
      key: 'score',
      width: 100,
      render: (_, record: CustomTournamentMatch) => (
        record.group1_all_score !== undefined && record.group2_all_score !== undefined
          ? `${record.group1_all_score} : ${record.group2_all_score}`
          : '-'
      ),
    },
    {
      title: '队伍对阵',
      key: 'teams',
      render: (_, record: CustomTournamentMatch) => (
        <span>
          {record.team1_name || '队伍1'} vs {record.team2_name || '队伍2'}
        </span>
      ),
    },
    {
      title: '轮次',
      dataIndex: 'round_name',
      key: 'round_name',
      width: 100,
      render: (text: string) => text || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record: CustomTournamentMatch) => (
        <Popconfirm
          title="确定要取消关联这场比赛吗？"
          onConfirm={() => handleUnlinkMatch(record.id)}
        >
          <Tooltip title="取消关联">
            <Button
              type="text"
              danger
              icon={<DisconnectOutlined />}
              size="small"
            />
          </Tooltip>
        </Popconfirm>
      ),
    },
  ];

  // 可用比赛表格列定义
  const availableMatchColumns: ColumnsType<AvailableMatch> = [
    {
      title: '比赛ID',
      dataIndex: 'match_id',
      key: 'match_id',
      ellipsis: true,
    },
    {
      title: '地图',
      dataIndex: 'map_name',
      key: 'map_name',
    },
    {
      title: '比赛时间',
      dataIndex: 'start_time',
      key: 'start_time',
      render: (timestamp: number) => formatTime(timestamp),
    },
    {
      title: '比分',
      key: 'score',
      render: (_, record: AvailableMatch) => (
        `${record.group1_all_score} : ${record.group2_all_score}`
      ),
    },
  ];

  if (!tournament) {
    return <div>加载中...</div>;
  }

  return (
    <div style={{ padding: '24px' }}>
      <Button onClick={onBack} style={{ marginBottom: '16px' }}>
        返回列表
      </Button>

      {/* 比赛基本信息 */}
      <Card title={tournament.name} style={{ marginBottom: '24px' }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="队伍数量"
              value={tournament.team_count}
              prefix={<TeamOutlined />}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="关联场数"
              value={tournament.match_count ?? tournament.matches.length}
              prefix={<TrophyOutlined />}
            />
          </Col>
        </Row>

        <Divider />

        <Row gutter={16}>
          <Col span={12}>
            <p><strong>创建者:</strong> {tournament.creator_username || `UID: ${tournament.creator_uid}`}</p>
            <p><strong>开始时间:</strong> {formatTime(tournament.start_time)}</p>
            <p><strong>结束时间:</strong> {formatTime(tournament.end_time)}</p>
          </Col>
          <Col span={12}>
            {tournament.description && (
              <div>
                <p><strong>描述:</strong></p>
                <p>{tournament.description}</p>
              </div>
            )}
          </Col>
        </Row>
      </Card>

      {/* 详细信息标签页 */}
      <Card>
        <Tabs defaultActiveKey="teams">
          <TabPane tab={`队伍 (${tournament?.teams.length || 0})`} key="teams">
            <div style={{ marginBottom: '16px' }}>
              {/* 移除添加队伍按钮，队伍由关联比赛自动生成 */}
            </div>
            <Table
              columns={teamColumns}
              dataSource={tournament?.teams || []}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </TabPane>

          <TabPane tab={`队伍统计`} key="team-stats">
            <Table
              columns={teamStatsColumns}
              dataSource={teamStats}
              rowKey={(row) => `${row.team_id}`}
              pagination={false}
              size="small"
            />
          </TabPane>

          <TabPane tab={`关联比赛 (${tournament?.matches.length || 0})`} key="matches">
            <div style={{ marginBottom: '16px' }}>
              <Button
                type="primary"
                icon={<LinkOutlined />}
                onClick={() => {
                  setLinkMatchModalVisible(true);
                  fetchAvailableMatches();
                }}
              >
                关联比赛
              </Button>
            </div>
            <Table
              columns={matchColumns}
              dataSource={tournament?.matches || []}
              rowKey="id"
              pagination={false}
              size="small"
              scroll={{ x: 800 }}
            />
          </TabPane>

          <TabPane tab={`排行榜`} key="leaderboard">
            <Space style={{ marginBottom: '16px' }}>
              <Select
                value={leaderboardStatType}
                onChange={(val) => setLeaderboardStatType(val)}
                options={statTypes.map((t) => ({ label: t.name, value: t.key }))}
                style={{ width: 180 }}
              />
              <Select
                allowClear
                placeholder="选择地图过滤"
                value={leaderboardMapFilter || undefined}
                onChange={(val) => setLeaderboardMapFilter(val || '')}
                options={availableMaps.map((m) => ({ label: m, value: m }))}
                style={{ width: 200 }}
              />
              <Button type="default" onClick={fetchLeaderboard} icon={<SearchOutlined />}>刷新</Button>
            </Space>
            <Table
              columns={leaderboardColumns}
              dataSource={leaderboard}
              rowKey={(row) => row.steam_id}
              pagination={{ pageSize: 10 }}
              size="small"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 编辑队伍模态框 */}
    <Modal
      title="编辑队伍"
      open={editTeamModalVisible}
      onCancel={() => {
        setEditTeamModalVisible(false);
        setEditingTeam(null);
        setEditTeamName('');
        setEditTeamCaptainUid(undefined);
      }}
      onOk={handleSaveEditTeam}
      okText="保存"
      cancelText="取消"
    >
      <Form layout="vertical">
        <Form.Item label="队伍名称" required>
          <Input
            placeholder="请输入队伍名称"
            value={editTeamName}
            onChange={(e) => setEditTeamName(e.target.value)}
          />
        </Form.Item>

        <Form.Item label="队长（从队伍玩家中选择）">
          <Select
            allowClear
            placeholder="请选择队长"
            value={editTeamCaptainUid}
            onChange={(val) => setEditTeamCaptainUid(val as number | undefined)}
            options={(editingTeam?.player_uids || []).map((uid) => ({ value: uid, label: playerUsernameMap[uid] || `UID: ${uid}` }))}
            optionFilterProp="label"
            showSearch
          />
        </Form.Item>
      </Form>
    </Modal>

    {/* 关联比赛模态框 */}
    <Modal
      title="关联比赛"
      open={linkMatchModalVisible}
      onCancel={() => {
          setLinkMatchModalVisible(false);
          setSelectedMatches([]);
        }}
        onOk={handleLinkMatches}
        width={800}
        okText="关联选中的比赛"
        cancelText="取消"
      >
        <div style={{ marginBottom: '16px' }}>
          <Search
            placeholder="搜索比赛ID或地图名称"
            allowClear
            onSearch={fetchAvailableMatches}
            style={{ width: '100%' }}
          />
        </div>
        <Table
          columns={availableMatchColumns}
          dataSource={availableMatches}
          rowKey="match_id"
          loading={availableMatchesLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: false,
          }}
          rowSelection={{
            selectedRowKeys: selectedMatches,
            onChange: (selectedRowKeys) => {
              setSelectedMatches(selectedRowKeys as string[]);
            },
          }}
          size="small"
        />
      </Modal>
    </div>
  );
};

export default CustomTournamentDetailComponent;

// 新增：队伍统计表格列
const teamStatsColumns: ColumnsType<CustomTournamentTeamStatsItem> = [
  { title: '队伍', dataIndex: 'team_name', key: 'team_name' },
  { title: '场次', dataIndex: 'matches_played', key: 'matches_played', align: 'right' },
  { title: '胜', dataIndex: 'wins', key: 'wins', align: 'right' },
  { title: '负', dataIndex: 'losses', key: 'losses', align: 'right' },
  { title: '胜率', dataIndex: 'win_rate', key: 'win_rate', align: 'right', render: (val: number) => `${Number(val).toFixed(2)}%` },
  { title: '总击杀', dataIndex: 'total_kills', key: 'total_kills', align: 'right' },
  { title: '总死亡', dataIndex: 'total_deaths', key: 'total_deaths', align: 'right' },
  { title: '总助攻', dataIndex: 'total_assists', key: 'total_assists', align: 'right' },
];

// 新增：排行榜表格列
const leaderboardColumns: ColumnsType<LeaderboardPlayer> = [
  { title: '排名', dataIndex: 'rank', key: 'rank', width: 80 },
  { title: '玩家', key: 'player', render: (_, row) => row.nickname || row.username },
  { title: '场次', dataIndex: 'total_matches', key: 'total_matches', align: 'right', width: 100 },
  { title: '统计值', dataIndex: 'stat_value', key: 'stat_value', align: 'right', width: 120 },
  { title: 'Rating2', key: 'avg_rating2', align: 'right', render: (_, row) => row.stats?.avg_rating2?.toFixed(3) },
  { title: 'K/D', key: 'kd_ratio', align: 'right', render: (_, row) => row.stats?.kd_ratio?.toFixed(2) },
  { title: '平均击杀', key: 'avg_kills', align: 'right', render: (_, row) => row.stats?.avg_kills?.toFixed(2) },
];