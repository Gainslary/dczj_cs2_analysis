import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Input,
  Select,
  Modal,
  Form,
  DatePicker,
  message,
  Card,
  Typography,
  Tooltip,
  Popconfirm,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  TrophyOutlined,
  TeamOutlined,
  CalendarOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import {
  CustomTournament,
  customTournamentsAPI,
  CreateCustomTournamentRequest
} from '../services/api';
import CustomTournamentDetail from './CustomTournamentDetail';
import CreateTournamentForm from './CreateTournamentForm';

const { Title } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface CustomTournamentsProps {}

const CustomTournaments: React.FC<CustomTournamentsProps> = () => {
  const [tournaments, setTournaments] = useState<CustomTournament[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filters, setFilters] = useState({
    status: '',
    search: '',
  });
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<CustomTournament | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'detail'>('list');
  const [selectedTournamentId, setSelectedTournamentId] = useState<number | null>(null);
  const [form] = Form.useForm();

  // 获取比赛列表
  const fetchTournaments = async (page = 1, pageSize = 10) => {
    setLoading(true);
    try {
      const response = await customTournamentsAPI.getTournaments(
        page,
        pageSize,
        filters.status,
        filters.search
      );
      
      if (response.success) {
        setTournaments(response.data);
        setPagination({
          current: page,
          pageSize,
          total: response.pagination.total,
        });
      }
    } catch (error) {
      console.error('获取比赛列表失败:', error);
      message.error('获取比赛列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTournaments();
  }, [filters]);

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

  // 删除比赛
  const handleDelete = async (tournament: CustomTournament) => {
    Modal.confirm({
      title: '删除自定义比赛确认',
      content: (
        <div>
          <p>确定要删除比赛 <strong>"{tournament.name}"</strong> 吗？</p>
          <div style={{ marginTop: 16, padding: 12, backgroundColor: '#fff2f0', borderRadius: 6 }}>
            <p style={{ margin: 0, color: '#cf1322' }}>
              <strong>⚠️ 警告：此操作不可撤销！</strong>
            </p>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: 20, color: '#cf1322' }}>
              <li>比赛数据将被永久删除</li>
              <li>所有相关队伍信息将被删除</li>
              <li>所有比赛关联将被删除</li>
              <li>排行榜数据将被清空</li>
            </ul>
          </div>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      width: 480,
      onOk: async () => {
        try {
          const response = await customTournamentsAPI.deleteTournament(tournament.id);
          if (response.success) {
            message.success('删除成功');
            fetchTournaments(pagination.current, pagination.pageSize);
          } else {
            message.error(response.error || '删除失败');
          }
        } catch (error: any) {
          console.error('删除比赛失败:', error);
          const errorMsg = error.response?.data?.error || '删除比赛失败';
          message.error(errorMsg);
        }
      }
    });
  };

  // 查看详情
  const handleViewDetail = (tournament: CustomTournament) => {
    setSelectedTournamentId(tournament.id);
    setViewMode('detail');
  };

  // 返回列表
  const handleBackToList = () => {
    setViewMode('list');
    setSelectedTournamentId(null);
    fetchTournaments(); // 刷新列表数据
  };

  // 创建成功回调
  const handleCreateSuccess = () => {
    setCreateModalVisible(false);
    fetchTournaments();
  };

  // 表格列定义
  const columns: ColumnsType<CustomTournament> = [
    {
      title: '比赛名称',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      ellipsis: true,
      render: (text: string, record: CustomTournament) => (
        <Tooltip title={text}>
          <Button type="link" onClick={() => handleViewDetail(record)}>
            {text}
          </Button>
        </Tooltip>
      ),
    },
    // 状态列已移除
    {
      title: '创建者',
      dataIndex: 'creator_username',
      key: 'creator_username',
      width: 120,
      render: (text: string, record: CustomTournament) => (
        text || record.creator_username || `UID: ${record.creator_uid}`
      ),
    },
    {
      title: '队伍数',
      dataIndex: 'team_count',
      key: 'team_count',
      width: 80,
      align: 'center',
      render: (count: number) => (
        <span>
          <TeamOutlined /> {count}
        </span>
      ),
    },
    {
      title: '比赛场数',
      dataIndex: 'match_count',
      key: 'match_count',
      width: 100,
      align: 'center',
      render: (count: number) => (
        <span>
          <TrophyOutlined /> {count}
        </span>
      ),
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 150,
      render: (timestamp: number) => formatTime(timestamp),
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 150,
      render: (timestamp: number) => formatTime(timestamp),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record: CustomTournament) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
            />
          </Tooltip>
          {/* 移除无效的编辑按钮 */}
          <Tooltip title="删除">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 如果是详情模式，显示详情组件
  if (viewMode === 'detail' && selectedTournamentId) {
    return (
      <CustomTournamentDetail
        tournamentId={selectedTournamentId}
        onBack={handleBackToList}
      />
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={2} style={{ margin: 0 }}>
                <TrophyOutlined /> 自定义比赛
              </Title>
            </Col>
            <Col>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={() => setCreateModalVisible(true)}
              >
                创建比赛
              </Button>
            </Col>
          </Row>
        </div>

        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Statistic
              title="总比赛数"
              value={pagination.total}
              prefix={<TrophyOutlined />}
            />
          </Col>
        </Row>

        {/* 筛选器 */}
        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={8}>
            <Search
              placeholder="搜索比赛名称"
              allowClear
              onSearch={(value) => setFilters(prev => ({ ...prev, search: value }))}
              style={{ width: '100%' }}
            />
          </Col>

        </Row>

        {/* 比赛列表表格 */}
        <Table
          columns={columns}
          dataSource={tournaments}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
            onChange: (page, pageSize) => {
              fetchTournaments(page, pageSize);
            },
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 创建比赛表单 */}
      <CreateTournamentForm
        visible={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* 比赛详情模态框 */}
      <Modal
        title="比赛详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedTournament && (
          <div>
            <Row gutter={16}>
              <Col span={12}>
                <p><strong>比赛名称:</strong> {selectedTournament.name}</p>
                <p><strong>创建者:</strong> {selectedTournament.creator_username || `UID: ${selectedTournament.creator_uid}`}</p>
              </Col>
              <Col span={12}>
                <p><strong>开始时间:</strong> {formatTime(selectedTournament.start_time)}</p>
                <p><strong>结束时间:</strong> {formatTime(selectedTournament.end_time)}</p>
                <p><strong>队伍数:</strong> {selectedTournament.team_count}</p>
              </Col>
            </Row>
            {selectedTournament.description && (
              <div>
                <p><strong>描述:</strong></p>
                <p>{selectedTournament.description}</p>
              </div>
            )}
            <Row gutter={16} style={{ marginTop: '16px' }}>
              <Col span={8}>
                <Statistic
                  title="关联场数"
                  value={selectedTournament.match_count}
                  prefix={<TrophyOutlined />}
                />
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default CustomTournaments;