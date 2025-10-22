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
  Tabs,
  Statistic,
  List,
  Avatar,
  Divider,
  Collapse,
  Badge,
  Popconfirm
} from 'antd';
import {
  TeamOutlined,
  TrophyOutlined,
  LinkOutlined,
  DisconnectOutlined,
  UserOutlined,
  SearchOutlined,
  CaretDownOutlined,
  CaretRightOutlined,
  StarOutlined
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

const { Text } = Typography;
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
  const [linkingMatches, setLinkingMatches] = useState(false);

  const [editTeamModalVisible, setEditTeamModalVisible] = useState(false);
  const [editingTeam, setEditingTeam] = useState<CustomTournamentTeam | null>(null);
  const [editTeamName, setEditTeamName] = useState<string>('');
  const [editTeamCaptainUid, setEditTeamCaptainUid] = useState<number | undefined>(undefined);
  const [form] = Form.useForm();
  const [playerUsernameMap, setPlayerUsernameMap] = useState<Record<number, string>>({});

  // 加载状态组件
  const LoadingIndicator: React.FC = () => (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <Badge status={playersLoading ? "processing" : "default"} text={playersLoading ? "正在加载玩家数据..." : "等待加载玩家数据..."} />
    </div>
  );

  // 队员信息展示组件
  const TeamPlayersList: React.FC<{ team: CustomTournamentTeam; players: Player[]; isCaptain: (uid: number) => boolean }> = ({ team, players, isCaptain }) => {
    const playersByRole = {
      captain: players.filter(p => isCaptain(p.uid)),
      members: players.filter(p => !isCaptain(p.uid))
    };

    return (
      <div style={{ background: '#fafafa', borderRadius: 8, padding: '16px', margin: '8px 0' }}>
        <div style={{ marginBottom: 12 }}>
          <Badge
            count={players.length}
            style={{ backgroundColor: '#52c41a' }}
            title="队员总数"
          >
            <Text strong style={{ fontSize: 14 }}>
              <TeamOutlined /> {team.team_name} - 队员名单
            </Text>
          </Badge>
        </div>

        {/* 队长 */}
        {playersByRole.captain.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 8,
              color: '#fa8c16',
              fontSize: 14,
              fontWeight: 'bold'
            }}>
              <StarOutlined style={{ marginRight: 8, color: '#faad14', fontSize: 16 }} />
              队长
            </div>
            <Row gutter={[8, 8]}>
              {playersByRole.captain.map(player => (
                <Col key={player.uid} xs={24} sm={12} md={8}>
                  <Card
                    size="small"
                    hoverable
                    style={{
                      border: '2px solid #faad14',
                      background: 'linear-gradient(135deg, #fff7e6 0%, #ffffff 100%)',
                      boxShadow: '0 2px 8px rgba(250, 173, 20, 0.2)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar
                          size="small"
                          icon={<UserOutlined />}
                          style={{
                            backgroundColor: '#faad14',
                            marginRight: 8,
                            border: '2px solid #fff'
                          }}
                        />
                        <div>
                          <div style={{ fontWeight: 'bold', fontSize: 13, color: '#d46b08' }}>
                            {player.username}
                          </div>
                          <div style={{ fontSize: 11, color: '#8c6e1f' }}>
                            UID: {player.uid} · {player.total_matches || 0}场比赛
                          </div>
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <Badge
                          count={player.platform_level}
                          style={{
                            backgroundColor: '#52c41a',
                            fontSize: 10,
                            height: 16,
                            lineHeight: '16px',
                            boxShadow: '0 0 0 1px #fff'
                          }}
                        />
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {/* 普通队员 */}
        {playersByRole.members.length > 0 && (
          <div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 8,
              color: '#1890ff',
              fontSize: 14,
              fontWeight: 'bold'
            }}>
              <UserOutlined style={{ marginRight: 8 }} />
              队员 ({playersByRole.members.length})
            </div>
            <Row gutter={[8, 8]}>
              {playersByRole.members.map(player => (
                <Col key={player.uid} xs={24} sm={12} md={8}>
                  <Card
                    size="small"
                    hoverable
                    style={{
                      border: '1px solid #d9d9d9',
                      background: '#ffffff',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center' }}>
                        <Avatar
                          size="small"
                          icon={<UserOutlined />}
                          style={{
                            backgroundColor: '#1890ff',
                            marginRight: 8
                          }}
                        />
                        <div>
                          <div style={{ fontWeight: 500, fontSize: 13, color: '#1890ff' }}>
                            {player.username}
                          </div>
                          <div style={{ fontSize: 11, color: '#666' }}>
                            UID: {player.uid} · {player.total_matches || 0}场比赛
                          </div>
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <Badge
                          count={player.platform_level}
                          style={{
                            backgroundColor: '#1890ff',
                            fontSize: 10,
                            height: 16,
                            lineHeight: '16px'
                          }}
                        />
                      </div>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        {players.length === 0 && (
          <div style={{
            textAlign: 'center',
            color: '#999',
            padding: '20px 0',
            fontStyle: 'italic'
          }}>
            <UserOutlined style={{ marginRight: 8, fontSize: 16 }} />
            该队伍暂无队员
          </div>
        )}
      </div>
    );
  };

  // 新增：队伍统计与排行榜相关状态
  const [teamStats, setTeamStats] = useState<CustomTournamentTeamStatsItem[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardPlayer[]>([]);
  const [leaderboardStatType, setLeaderboardStatType] = useState<string>('rating2');
  const [leaderboardMapFilter, setLeaderboardMapFilter] = useState<string>('');
  const [statTypes, setStatTypes] = useState<StatType[]>([]);
  const [availableMaps, setAvailableMaps] = useState<string[]>([]);
  const [expandedTeams, setExpandedTeams] = useState<Set<number>>(new Set());
  const [playerUidMap, setPlayerUidMap] = useState<Record<number, Player>>({});
  const [playersLoading, setPlayersLoading] = useState(false);

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
    preloadAllPlayers(); // 预加载玩家数据（包含username映射）

    // 清除重复的fetchTournamentDetail调用
  }, [tournamentId]);

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



// 添加玩家数据预加载日志
  useEffect(() => {
    if (Object.keys(playerUidMap).length > 0) {
      console.log(`✅ 玩家数据预加载完成，共 ${Object.keys(playerUidMap).length} 个玩家`);
    }
  }, [playerUidMap]);

  // 切换统计类型或地图过滤时刷新排行榜
  useEffect(() => {
    if (tournamentId) { // 确保tournamentId存在才调用
      fetchLeaderboard();
    }
  }, [tournamentId, leaderboardStatType, leaderboardMapFilter]);

  
  // 格式化时间
  const formatTime = (timestamp: number) => {
    return dayjs(timestamp * 1000).format('YYYY-MM-DD HH:mm');
  };

  // 预加载所有玩家数据并创建UID映射（合并原来的两个函数）
  const preloadAllPlayers = async () => {
    // 防止重复调用
    if (playersLoading || Object.keys(playerUidMap).length > 0) {
      console.log('玩家数据已在加载中或已完成，跳过重复调用');
      return;
    }

    setPlayersLoading(true);
    try {
      console.log('开始预加载玩家数据...');
      const players = await playersAPI.searchPlayers('');
      if (players && players.length > 0) {
        // 创建UID到Player的映射
        const uidMap: Record<number, Player> = {};
        // 创建UID到username的映射
        const usernameMap: Record<number, string> = {};

        players.forEach(player => {
          if (player.uid) {
            uidMap[player.uid] = player;
            usernameMap[player.uid] = player.username || String(player.uid);
          }
        });

        setPlayerUidMap(uidMap);
        setPlayerUsernameMap(usernameMap);
        console.log(`✅ 预加载完成，共 ${players.length} 个玩家数据`);
      }
    } catch (error) {
      console.error('❌ 预加载玩家数据失败:', error);
      message.error('预加载玩家数据失败，请刷新页面重试');
    } finally {
      setPlayersLoading(false);
    }
  };

  // 根据UID获取队员信息（使用预加载的映射）
  const getTeamPlayers = (team: CustomTournamentTeam): Player[] => {
    const player_uids = team.player_uids || [];
    if (player_uids.length === 0) {
      return [];
    }

    return player_uids.map(uid => {
      const player = playerUidMap[uid];
      if (player) {
        return player;
      }
      // 如果找不到玩家，返回默认信息
      return {
        uid,
        username: `UID: ${uid}`,
        platform_level: 0,
        steam_id: '',
        total_matches: 0
      } as Player;
    });
  };

  // 切换队伍展开状态
  const toggleTeamExpansion = (team: CustomTournamentTeam) => {
    const newExpanded = new Set(expandedTeams);

    if (newExpanded.has(team.id)) {
      newExpanded.delete(team.id);
      setExpandedTeams(newExpanded);
    } else {
      newExpanded.add(team.id);
      setExpandedTeams(newExpanded);
    }
  };



  // 关联比赛
  const handleLinkMatches = async () => {
    // 防抖：如果正在处理中，直接返回
    if (linkingMatches) {
      return;
    }

    if (selectedMatches.length === 0) {
      message.warning('请选择要关联的比赛');
      return;
    }

    setLinkingMatches(true);
    try {
      const failedMatches: string[] = [];
      for (const matchId of selectedMatches) {
        try {
          await customTournamentsAPI.linkMatch(tournamentId,   {
            match_id: matchId,
            match_order: 0,
          });
        } catch (error: any) {
          const errorMsg = error.response?.data?.error || `比赛${matchId}关联失败`;
          failedMatches.push(errorMsg);
        }
      }

      if (failedMatches.length === 0) {
        message.success(`成功关联 ${selectedMatches.length} 场比赛`);
      } else {
        const successCount = selectedMatches.length - failedMatches.length;
        message.warning(
          <div>
            <div>成功关联 {successCount} 场比赛，{failedMatches.length} 场失败</div>
            <div style={{ fontSize: '12px', marginTop: '8px', color: '#ff4d4f' }}>
              {failedMatches[0]}
            </div>
          </div>
        );
      }

      setLinkMatchModalVisible(false);
      setSelectedMatches([]);
      fetchTournamentDetail();
      fetchTeamStats();
      fetchLeaderboard();
    } catch (error) {
      console.error('关联比赛失败:', error);
      message.error('关联比赛失败，请稍后重试');
    } finally {
      setLinkingMatches(false);
    }
  };

  // 取消关联比赛
  const handleUnlinkMatch = async (linkId: number) => {
    try {
      const res = await customTournamentsAPI.unlinkMatch(tournamentId, linkId);

      message.success(res.message || '取消关联成功');
      fetchTournamentDetail();
      fetchTeamStats();
      fetchLeaderboard();
    } catch (error: any) {
      console.error('取消关联失败:', error);
      const errorMsg = error.response?.data?.error || '取消关联失败';
      message.error(errorMsg);
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

    // 前端验证
    if (name.length > 50) {
      message.error('队伍名称最多50字符');
      return;
    }
    if (/[<>'"&]/.test(name)) {
      message.error('队伍名称包含非法字符');
      return;
    }

    try {
      const response = await customTournamentsAPI.updateTeam(
        tournamentId,
        editingTeam.id,
        { team_name: name, captain_uid: typeof editTeamCaptainUid === 'number' ? editTeamCaptainUid : null }
      );
      if (response.success) {
        message.success('队伍信息已更新');
        setEditTeamModalVisible(false);
        setEditingTeam(null);
        setEditTeamName('');
        setEditTeamCaptainUid(undefined);
        fetchTournamentDetail();
      } else {
        message.error(response.error || '更新队伍失败');
      }
    } catch (error: any) {
      console.error('更新队伍失败:', error);
      const errorMsg = error.response?.data?.error || '更新队伍失败';
      message.error(errorMsg);
    }
  };

  // 判断是否为队长
  const isCaptain = (team: CustomTournamentTeam, playerUid: number) => {
    return team.captain_uid === playerUid;
  };

  // 队伍表格列定义
  const teamColumns: ColumnsType<CustomTournamentTeam> = [
    {
      title: '队伍名称',
      dataIndex: 'team_name',
      key: 'team_name',
      render: (text: string, record: CustomTournamentTeam) => (
        <div
          style={{
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            color: '#1890ff',
            fontWeight: 500
          }}
          onClick={() => toggleTeamExpansion(record)}
        >
          {expandedTeams.has(record.id) ?
            <CaretDownOutlined style={{ marginRight: 8 }} /> :
            <CaretRightOutlined style={{ marginRight: 8 }} />
          }
          <TeamOutlined style={{ marginRight: 6 }} />
          {text}
          <Text style={{ marginLeft: 8, color: '#999', fontSize: 12, fontWeight: 'normal' }}>
            点击查看队员 ({record.player_uids?.length || 0})
          </Text>
        </div>
      ),
    },
    {
      title: '队长',
      dataIndex: 'captain_username',
      key: 'captain_username',
      render: (_: string, record: CustomTournamentTeam) => {
        const captain = record.captain_uid;
        const captainInfo = captain ? playerUidMap[captain] : null;

        return (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {captainInfo ? (
              <>
                <Avatar
                  size="small"
                  icon={<UserOutlined />}
                  style={{ backgroundColor: '#faad14', marginRight: 8 }}
                />
                <span>
                  {captainInfo.username}
                  <Badge
                    count={captainInfo.platform_level}
                    style={{
                      backgroundColor: '#52c41a',
                      fontSize: 10,
                      height: 16,
                      lineHeight: '16px',
                      marginLeft: 8
                    }}
                  />
                </span>
              </>
            ) : (
              <span style={{ color: '#999' }}>
                未设置
                {captain && <Text style={{ fontSize: 12 }}> (UID: {captain})</Text>}
              </span>
            )}
          </div>
        );
      },
    },
    {
      title: '队员数量',
      dataIndex: 'player_uids',
      key: 'player_count',
      render: (uids: number[]) => {
        const loadedCount = uids ? uids.filter(uid => playerUidMap[uid]).length : 0;
        const totalCount = uids ? uids.length : 0;

        return (
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <UserOutlined style={{ marginRight: 8 }} />
            <span>{totalCount}</span>
            {loadedCount > 0 && loadedCount < totalCount && (
              <Tooltip title={`已匹配 ${loadedCount}/${totalCount} 名队员信息`}>
                <Badge
                  status="warning"
                  style={{ marginLeft: 8 }}
                />
              </Tooltip>
            )}
            {loadedCount === totalCount && totalCount > 0 && (
              <Tooltip title={`已匹配所有队员信息`}>
                <Badge
                  status="success"
                  style={{ marginLeft: 8 }}
                />
              </Tooltip>
            )}
          </div>
        );
      },
    },
    {
      title: '胜负记录',
      key: 'record',
      render: (_, record: CustomTournamentTeam) => {
        const stats = teamStats.find(s => s.team_id === record.id);
        const wins = stats?.wins ?? 0;
        const losses = stats?.losses ?? 0;
        const matches = stats?.matches_played ?? (wins + losses);
        const winRate = matches > 0 ? (wins / matches * 100).toFixed(1) : 0;

        return (
          <div>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ color: '#52c41a', fontWeight: 'bold', marginRight: 12 }}>
                {wins}胜
              </span>
              <span style={{ color: '#ff4d4f', fontWeight: 'bold', marginRight: 12 }}>
                {losses}负
              </span>
              <span style={{ color: '#1890ff', fontSize: 12 }}>
                ({matches}场)
              </span>
            </div>
            <div style={{ fontSize: 12, color: '#666', marginTop: 2 }}>
              胜率: {winRate}%
            </div>
          </div>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record: CustomTournamentTeam) => (
        <Button type="text" size="small" onClick={() => openEditTeamModal(record)}>
          编辑
        </Button>
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
          title="取消关联比赛"
          description="确定要取消关联这场比赛吗？系统将智能处理相关队伍：若队伍仍被其他比赛使用则保留，否则自动清除。"
          onConfirm={() => handleUnlinkMatch(record.id)}
          okText="确认取消关联"
          cancelText="取消"
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
    {
      title: '状态',
      key: 'status',
      width: 80,
      render: (_, record: AvailableMatch) => {
        const isLinked = record.is_linked === 1;
        return isLinked ? (
          <Tag color="green">已关联</Tag>
        ) : (
          <Tag color="default">未关联</Tag>
        );
      },
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
              {/* 队伍管理说明 */}
              <div>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  💡 点击队伍名称查看队员详情
                </Text>
                <Text type="secondary" style={{ fontSize: 12, marginLeft: 16 }}>
                  📝 队伍通过关联比赛自动生成，移除未使用的队伍请解除对应比赛关联
                </Text>
              </div>
              {Object.keys(playerUidMap).length === 0 && (
                <Text type="warning" style={{ fontSize: 12, display: 'block', marginTop: 8 }}>
                  ⚠️ 正在加载玩家数据...
                </Text>
              )}
            </div>

            {Object.keys(playerUidMap).length > 0 ? (
              <Table
                columns={teamColumns}
                dataSource={tournament?.teams || []}
                rowKey="id"
                pagination={false}
                size="small"
                expandable={{
                  expandedRowKeys: Array.from(expandedTeams),
                  onExpand: (_, record) => {
                    toggleTeamExpansion(record);
                  },
                  expandedRowRender: (record: CustomTournamentTeam) => {
                    const players = getTeamPlayers(record);

                    return (
                      <div style={{ margin: 0 }}>
                        <TeamPlayersList
                          team={record}
                          players={players}
                          isCaptain={(uid) => isCaptain(record, uid)}
                        />
                      </div>
                    );
                  },
                  rowExpandable: (record) => {
                    return (record.player_uids && record.player_uids.length > 0) || false;
                  }
                }}
              />
            ) : (
              <div style={{ padding: '40px 0', textAlign: 'center' }}>
                <LoadingIndicator />
                <div style={{ marginTop: 16, color: '#666', fontSize: 14 }}>
                  正在预加载所有玩家数据，请稍候...
                </div>
              </div>
            )}
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
        confirmLoading={linkingMatches}
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
            getCheckboxProps: (record: AvailableMatch) => ({
              disabled: record.is_linked === 1,
            }),
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