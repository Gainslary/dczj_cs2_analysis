import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, message, Spin, DatePicker, Select } from 'antd';
import { ReloadOutlined, EyeOutlined } from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import { matchesAPI, type MatchesFilters } from '../services/api';
import type { Match } from '../services/api';
import MatchDetail from './MatchDetail';

const { RangePicker } = DatePicker;
const { Option } = Select;

const MatchesDashboard: React.FC = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
  const [mapFilter, setMapFilter] = useState<string | undefined>(undefined);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => 
      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  });

  const fetchMatches = async (page: number = pagination.current, limit: number = pagination.pageSize) => {
    setLoading(true);
    try {
      // 构建筛选参数
      const filters: MatchesFilters = {};
      if (dateRange && dateRange[0] && dateRange[1]) {
        filters.startDate = dateRange[0].format('YYYY-MM-DD');
        filters.endDate = dateRange[1].format('YYYY-MM-DD');
      }
      if (mapFilter) {
        filters.mapName = mapFilter;
      }

      const response = await matchesAPI.getMatches(page, limit, filters);
      setMatches(response.matches);
      setPagination(prev => ({
        ...prev,
        current: response.pagination.page,
        total: response.pagination.total,
      }));
    } catch (error) {
      message.error('获取比赛数据失败');
      console.error('Error fetching matches:', error);
      setMatches([]);
      setPagination(prev => ({ ...prev, total: 0 }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatches();
  }, []);

  // 筛选条件变化时自动刷新
  useEffect(() => {
    if (pagination.current !== 1) {
      setPagination(prev => ({ ...prev, current: 1 }));
    }
    fetchMatches(1, pagination.pageSize);
  }, [dateRange, mapFilter]);

  const handleViewDetail = (matchId: string) => {
    setSelectedMatch(matchId);
  };

  const handleCloseDetail = () => {
    setSelectedMatch(null);
  };



  const getRatingColor = (rating: number) => {
    if (rating >= 1.2) return '#52c41a';
    if (rating >= 1.0) return '#faad14';
    return '#ff4d4f';
  };

  const columns = [
    {
      title: '比赛时间',
      dataIndex: 'match_time',
      key: 'match_time',
      render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
      sorter: (a: Match, b: Match) => dayjs(a.match_time).unix() - dayjs(b.match_time).unix(),
    },
    {
      title: '地图',
      dataIndex: 'map_name',
      key: 'map_name',
      filters: [
        { text: 'de_dust2', value: 'de_dust2' },
        { text: 'de_mirage', value: 'de_mirage' },
        { text: 'de_inferno', value: 'de_inferno' },
        { text: 'de_cache', value: 'de_cache' },
        { text: 'de_overpass', value: 'de_overpass' },
        { text: 'de_train', value: 'de_train' },
        { text: 'de_ancient', value: 'de_ancient' },
        { text: 'de_vertigo', value: 'de_vertigo' },
      ],
      onFilter: (value: any, record: Match) => record.map_name.includes(value),
    },

    {
      title: '比赛类型',
      dataIndex: 'score',
      key: 'score',
    },
    {
      title: '平均Rating',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: number) => (
        <span style={{ color: getRatingColor(rating), fontWeight: 'bold' }}>
          {rating.toFixed(2)}
        </span>
      ),
      sorter: (a: Match, b: Match) => a.rating - b.rating,
    },
    {
      title: '最高击杀',
      dataIndex: 'kills',
      key: 'kills',
      render: (kills: number) => kills || '-',
      sorter: (a: Match, b: Match) => a.kills - b.kills,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Match) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewDetail(record.match_id)}
        >
          详情
        </Button>
      ),
    },
  ];

  const stats = {
    totalMatches: pagination.total,
    wins: matches.filter(m => m.match_result === '胜利').length,
    losses: matches.filter(m => m.match_result === '失败').length,
    avgRating: matches.length > 0 
      ? (matches.reduce((sum, m) => sum + m.rating, 0) / matches.length).toFixed(2)
      : '0.00',
    maxKills: matches.length > 0
      ? Math.max(...matches.map(m => m.kills)).toString()
      : '0',
  };

  return (
    <div>
      <Card title="比赛统计" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
              {stats.totalMatches}
            </div>
            <div>总比赛数</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
              {stats.wins}
            </div>
            <div>胜利场次</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>
              {stats.losses}
            </div>
            <div>失败场次</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>
              {stats.avgRating}
            </div>
            <div>平均Rating</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
              {stats.maxKills}
            </div>
            <div>最高击杀</div>
          </div>
        </div>
      </Card>

      <Card 
        title="比赛列表" 
        extra={
          <Space>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [Dayjs, Dayjs] | null)}
              placeholder={['开始日期', '结束日期']}
            />
            <Select
              placeholder="选择地图"
              style={{ width: 120 }}
              value={mapFilter}
              onChange={setMapFilter}
              allowClear
            >
              <Option value="de_dust2">Dust2</Option>
              <Option value="de_mirage">Mirage</Option>
              <Option value="de_inferno">Inferno</Option>
              <Option value="de_cache">Cache</Option>
              <Option value="de_overpass">Overpass</Option>
            </Select>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={() => fetchMatches()}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={matches}
            rowKey="match_id"
            pagination={{
              ...pagination,
              onChange: (page, size) => {
                setPagination(prev => ({ ...prev, current: page, pageSize: size || prev.pageSize }));
                fetchMatches(page, size || pagination.pageSize);
              },
              onShowSizeChange: (current, size) => {
                setPagination(prev => ({ ...prev, current: 1, pageSize: size }));
                fetchMatches(1, size);
              },
            }}
            scroll={{ x: 1000 }}
          />
        </Spin>
      </Card>

      <MatchDetail
        visible={!!selectedMatch}
        matchId={selectedMatch}
        onClose={handleCloseDetail}
      />
    </div>
  );
};

export default MatchesDashboard;