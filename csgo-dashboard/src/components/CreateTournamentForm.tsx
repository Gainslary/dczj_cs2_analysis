import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  DatePicker,
  Button,
  Space,
  Card,
  Row,
  Col,
  Select,
  Alert,
  message,
  Divider,
  Typography,
  Tag,
  List,
  Avatar,
  Tooltip,
  Popconfirm
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  UserOutlined,
  TeamOutlined,
  SearchOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import {
  CreateCustomTournamentRequest,
  customTournamentsAPI,
  playersAPI,
  Player
} from '../services/api';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

interface CreateTournamentFormProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

interface TeamData {
  id: string;
  team_name: string;
  player_uids: number[];
  captain_uid?: number;
  players: Player[];
}

const CreateTournamentForm: React.FC<CreateTournamentFormProps> = ({
  visible,
  onCancel,
  onSuccess
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [teams, setTeams] = useState<TeamData[]>([]);
  const [searchPlayers, setSearchPlayers] = useState<Player[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // 添加队伍
  const addTeam = () => {
    const newTeam: TeamData = {
      id: Date.now().toString(),
      team_name: '',
      player_uids: [],
      players: []
    };
    setTeams([...teams, newTeam]);
  };

  // 删除队伍
  const removeTeam = (teamId: string) => {
    setTeams(teams.filter(team => team.id !== teamId));
  };

  // 更新队伍名称
  const updateTeamName = (teamId: string, name: string) => {
    setTeams(teams.map(team => 
      team.id === teamId ? { ...team, team_name: name } : team
    ));
  };

  // 搜索玩家（仅在明确触发时调用，支持空输入列出全部）
  const handleSearchPlayers = async (nickname: string) => {
    setSearchLoading(true);
    try {
      const players = await playersAPI.searchPlayers(nickname || '');
      setSearchPlayers(players);
    } catch (error) {
      console.error('搜索玩家失败:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  // 添加玩家到队伍
  const addPlayerToTeam = (teamId: string, player: Player) => {
    setTeams(teams.map(team => {
      if (team.id === teamId) {
        // 检查玩家是否已经在队伍中
        if (team.player_uids.includes(player.uid)) {
          message.warning('该玩家已在队伍中');
          return team;
        }
        
        // 检查玩家是否在其他队伍中
        const isInOtherTeam = teams.some(t => 
          t.id !== teamId && t.player_uids.includes(player.uid)
        );
        if (isInOtherTeam) {
          message.warning('该玩家已在其他队伍中');
          return team;
        }

        return {
          ...team,
          player_uids: [...team.player_uids, player.uid],
          players: [...team.players, player]
        };
      }
      return team;
    }));
  };

  // 从队伍中移除玩家
  const removePlayerFromTeam = (teamId: string, playerUid: number) => {
    setTeams(teams.map(team => {
      if (team.id === teamId) {
        return {
          ...team,
          player_uids: team.player_uids.filter(uid => uid !== playerUid),
          players: team.players.filter(player => player.uid !== playerUid),
          captain_uid: team.captain_uid === playerUid ? undefined : team.captain_uid
        };
      }
      return team;
    }));
  };

  // 设置队长
  const setCaptain = (teamId: string, playerUid: number) => {
    setTeams(teams.map(team => 
      team.id === teamId ? { ...team, captain_uid: playerUid } : team
    ));
  };

  // 自定义验证规则
  const validateName = (_: any, value: string) => {
    if (!value || value.trim() === '') {
      return Promise.reject(new Error('比赛名称不能为空'));
    }
    if (value.length > 100) {
      return Promise.reject(new Error('比赛名称最多100字符'));
    }
    // 检查非法字符
    if (/[<>'"&]/.test(value)) {
      return Promise.reject(new Error('比赛名称包含非法字符'));
    }
    return Promise.resolve();
  };

  const validateTimeRange = (_: any, value: any) => {
    if (!value || !value[0] || !value[1]) {
      return Promise.reject(new Error('请选择比赛时间'));
    }

    const now = dayjs();
    const startTime = value[0];
    const endTime = value[1];

    if (startTime.isAfter(endTime)) {
      return Promise.reject(new Error('开始时间必须早于结束时间'));
    }

    // 检查开始时间不能早于24小时前
    const oneDayAgo = now.subtract(24, 'hour');
    if (startTime.isBefore(oneDayAgo)) {
      return Promise.reject(new Error('开始时间不能早于24小时前'));
    }

    return Promise.resolve();
  };

  const validateDescription = (_: any, value: string) => {
    if (value && value.length > 1000) {
      return Promise.reject(new Error('比赛描述最多1000字符'));
    }
    if (value && /[<>'"&]/.test(value)) {
      return Promise.reject(new Error('比赛描述包含非法字符'));
    }
    return Promise.resolve();
  };

  const validateCreator = (_: any, value: number) => {
    if (!value || value <= 0) {
      return Promise.reject(new Error('请选择有效的创建者'));
    }
    return Promise.resolve();
  };

  // 提交表单
  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const startTime = values.timeRange[0].unix();
      const endTime = values.timeRange[1].unix();
      const creatorUid = values.creator_uid;

      if (!creatorUid) {
        message.error('请先选择创建者');
        setLoading(false);
        return;
      }

      const createData: CreateCustomTournamentRequest = {
        name: values.name.trim(),
        description: values.description?.trim() || '',
        start_time: startTime,
        end_time: endTime,
        creator_uid: creatorUid,
        teams: []
      };

      const response = await customTournamentsAPI.createTournament(createData);
      if (response.success) {
        message.success('创建成功');
        handleCancel();
        onSuccess();
      } else {
        // 显示服务器返回的具体错误信息
        message.error(response.error || '创建比赛失败');
      }
    } catch (error: any) {
      console.error('创建比赛失败:', error);
      // 尝试从错误响应中获取详细错误信息
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error('创建比赛失败，请检查输入信息');
      }
    } finally {
      setLoading(false);
    }
  };

  // 取消操作
  const handleCancel = () => {
    form.resetFields();
    setTeams([]);
    setSearchPlayers([]);
    onCancel();
  };

  // 获取玩家选项
  const getPlayerOptions = () => {
    return searchPlayers.map(player => ({
      value: player.uid,
      label: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>
            <UserOutlined /> {player.username}
          </span>
        </div>
      ),
      player: player
    }));
  };

  return (
    <Modal
      title="创建自定义比赛"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        {/* 基本信息 */}
        <Card title="基本信息" size="small" style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="比赛名称"
                rules={[
                  { required: true, message: '请输入比赛名称' },
                  { validator: validateName }
                ]}
              >
                <Input placeholder="请输入比赛名称" showCount maxLength={100} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="timeRange"
                label="比赛时间"
                rules={[
                  { required: true, message: '请选择比赛时间' },
                  { validator: validateTimeRange }
                ]}
              >
                <RangePicker
                  showTime
                  format="YYYY-MM-DD HH:mm"
                  style={{ width: '100%' }}
                  placeholder={['开始时间', '结束时间']}
                />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="description"
            label="比赛描述"
            rules={[{ validator: validateDescription }]}
          >
            <TextArea
              placeholder="请输入比赛描述"
              rows={3}
              showCount
              maxLength={1000}
            />
          </Form.Item>
        </Card>

        {/* 创建者选择 & 队伍生成说明 */}
        <Card title={<span><UserOutlined /> 创建者与队伍</span>} size="small" style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="creator_uid"
                label="创建者"
                rules={[
                  { required: true, message: '请选择创建者' },
                  { validator: validateCreator }
                ]}
              >
                <Select
                  showSearch
                  placeholder="搜索并选择创建者"
                  filterOption={false}
                  onSearch={handleSearchPlayers}
                  options={getPlayerOptions()}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Alert
            message="队伍与队员将会在关联比赛时自动生成（按比赛两队玩家去重）"
            type="info"
            showIcon
          />
        </Card>

        {/* 操作按钮 */}
        <Form.Item>
          <Space>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
            >
              创建比赛
            </Button>
            <Button onClick={handleCancel}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default CreateTournamentForm;