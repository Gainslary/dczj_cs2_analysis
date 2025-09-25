import React, { useState, useEffect } from 'react';
import { leaderboardAPI, LeaderboardPlayer, StatType, LeaderboardFilters } from '../services/api';
import './Leaderboard.css';

const Leaderboard: React.FC = () => {
  const [players, setPlayers] = useState<LeaderboardPlayer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statTypes, setStatTypes] = useState<StatType[]>([]);
  const [filters, setFilters] = useState<LeaderboardFilters>({ maps: [], seasons: [] });
  
  // 筛选状态
  const [selectedStat, setSelectedStat] = useState('rating2');
  const [selectedMap, setSelectedMap] = useState('');
  
  // 玩家详情模态框状态
  const [selectedPlayer, setSelectedPlayer] = useState<LeaderboardPlayer | null>(null);
  const [showPlayerModal, setShowPlayerModal] = useState(false);

  // 加载初始数据
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [statsTypesData, filtersData] = await Promise.all([
          leaderboardAPI.getStatsTypes(),
          leaderboardAPI.getFilters()
        ]);
        setStatTypes(statsTypesData);
        setFilters(filtersData);
      } catch (err) {
        console.error('加载初始数据失败:', err);
        setError('加载初始数据失败');
      }
    };

    loadInitialData();
  }, []);

  // 加载排行榜数据
  const loadLeaderboard = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await leaderboardAPI.getLeaderboard(
        selectedStat,
        selectedMap
      );
      setPlayers(response.data);
    } catch (err) {
      console.error('加载排行榜失败:', err);
      setError('加载排行榜数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 当筛选条件改变时重新加载数据
  useEffect(() => {
    loadLeaderboard();
  }, [selectedStat, selectedMap]);

  // 获取统计值显示格式
  const formatStatValue = (value: number, statType: string): string => {
    switch (statType) {
      case 'rating2':
      case 'rating':
      case 'kast':
        return value.toFixed(3);
      case 'adr':
      case 'rws':
        return value.toFixed(2);
      case 'kd_ratio':
        return value.toFixed(2);
      case 'headshot_rate':
      case 'win_rate':
      case 'first_kill_rate':
      case 'first_death_rate':
        return (value * 100).toFixed(1) + '%';
      case 'avg_kills':
      case 'avg_assists':
      case 'avg_deaths':
      case 'avg_first_kill':
      case 'avg_first_death':
      case 'avg_awp_kills':
        return value.toFixed(2);
      case 'mvp_count':
        return Math.round(value).toString();
      default:
        return value.toFixed(2);
    }
  };

  // 获取排名颜色
  const getRankColor = (rank: number): string => {
    if (rank === 1) return '#FFD700'; // 金色
    if (rank === 2) return '#C0C0C0'; // 银色
    if (rank === 3) return '#CD7F32'; // 铜色
    if (rank <= 10) return '#4CAF50'; // 绿色
    return '#666'; // 默认灰色
  };

  // 处理玩家点击事件
  const handlePlayerClick = (player: LeaderboardPlayer) => {
    setSelectedPlayer(player);
    setShowPlayerModal(true);
  };

  // 关闭玩家详情模态框
  const closePlayerModal = () => {
    setShowPlayerModal(false);
    setSelectedPlayer(null);
  };



  // 格式化时间
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  if (loading && players.length === 0) {
    return (
      <div className="leaderboard-container">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  return (
    <div className="leaderboard-container">
      <div className="leaderboard-header">
        <h1>🏆 全玩家排行榜</h1>
        <p>基于历史比赛数据的综合排行榜</p>
      </div>

      {/* 筛选控件 */}
      <div className="filters-section">
        <div className="filter-group">
          <label>排行榜类型:</label>
          <select 
            value={selectedStat} 
            onChange={(e) => setSelectedStat(e.target.value)}
            className="filter-select"
          >
            {statTypes.map(stat => (
              <option key={stat.key} value={stat.key}>
                {stat.name} - {stat.description}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>地图筛选:</label>
          <select 
            value={selectedMap} 
            onChange={(e) => setSelectedMap(e.target.value)}
            className="filter-select"
          >
            <option value="">全部地图</option>
            {filters.maps.map(map => (
              <option key={map} value={map}>{map}</option>
            ))}
          </select>
        </div>



        <button onClick={loadLeaderboard} className="refresh-btn" disabled={loading}>
          {loading ? '刷新中...' : '刷新数据'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* 排行榜表格 */}
      <div className="leaderboard-table-container">
        <table className="leaderboard-table">
          <thead>
            <tr>
              <th className="rank-col">排名</th>
              <th className="player-col">玩家</th>
              <th className="matches-col">比赛</th>
              <th className="main-stat-col">主要数据</th>
              <th className="rating-col">Rating 2.0</th>
              <th className="kd-col">K/D</th>
              <th className="adr-col">ADR</th>
              <th className="winrate-col">胜率</th>
              <th className="mvp-col">MVP</th>
              <th className="kills-col">击杀</th>
              <th className="assists-col">助攻</th>
              <th className="deaths-col">死亡</th>
              <th className="headshot-col">爆头率</th>
              <th className="first-kill-col">首杀</th>
              <th className="first-death-col">首死</th>
              <th className="first-kill-rate-col">首杀率</th>
              <th className="first-death-rate-col">首死率</th>
              <th className="awp-col">AWP击杀</th>
              <th className="kast-col">KAST</th>
              <th className="rws-col">RWS</th>
              <th className="time-col">最后比赛</th>
            </tr>
          </thead>
          <tbody>
            {players.map((player) => (
              <tr 
                key={player.steam_id} 
                className="player-row clickable-row"
                onClick={() => handlePlayerClick(player)}
                title="点击查看详细统计"
              >
                <td className="rank-cell">
                  <span 
                    className="rank-number"
                    style={{ color: getRankColor(player.rank) }}
                  >
                    #{player.rank}
                  </span>
                </td>
                <td className="player-cell">
                  <div className="player-info">
                    <div className="player-name">
                      {player.nickname || player.username}
                    </div>
                    <div className="player-username">
                      {player.nickname && player.username !== player.nickname && (
                        <span>({player.username})</span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="matches-cell">
                  {player.total_matches}
                </td>
                <td className="stat-value-cell">
                  <span className="stat-value">
                    {formatStatValue(player.stat_value, selectedStat)}
                  </span>
                </td>
                <td className="rating-cell">
                  {player.stats.avg_rating2.toFixed(3)}
                </td>
                <td className="kd-cell">
                  {player.stats.kd_ratio.toFixed(2)}
                </td>
                <td className="adr-cell">
                  {player.stats.avg_adr.toFixed(1)}
                </td>
                <td className="winrate-cell">
                  {(player.stats.win_rate * 100).toFixed(1)}%
                </td>
                <td className="mvp-cell">
                  {player.stats.mvp_count}
                </td>
                <td className="kills-cell">
                  {player.stats.avg_kills.toFixed(2)}
                </td>
                <td className="assists-cell">
                  {player.stats.avg_assists.toFixed(2)}
                </td>
                <td className="deaths-cell">
                  {player.stats.avg_deaths.toFixed(2)}
                </td>
                <td className="headshot-cell">
                  {(player.stats.avg_headshot_rate * 100).toFixed(1)}%
                </td>
                <td className="first-kill-cell">
                  {player.stats.avg_first_kill.toFixed(2)}
                </td>
                <td className="first-death-cell">
                  {player.stats.avg_first_death.toFixed(2)}
                </td>
                <td className="first-kill-rate-cell">
                  {(player.stats.first_kill_rate * 100).toFixed(1)}%
                </td>
                <td className="first-death-rate-cell">
                  {(player.stats.first_death_rate * 100).toFixed(1)}%
                </td>
                <td className="awp-cell">
                  {player.stats.avg_awp_kills.toFixed(2)}
                </td>
                <td className="kast-cell">
                  {(player.stats.avg_kast * 100).toFixed(1)}%
                </td>
                <td className="rws-cell">
                  {player.stats.avg_rws.toFixed(1)}
                </td>
                <td className="time-cell">
                  {formatTime(player.last_match_time)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {players.length === 0 && !loading && (
        <div className="no-data">
          没有找到符合条件的玩家数据
        </div>
      )}

      {/* 统计信息 */}
      <div className="stats-summary">
        <p>显示 {players.length} 名玩家</p>
        {selectedMap && <p>地图: {selectedMap}</p>}
      </div>

      {/* 玩家详情模态框 */}
      {showPlayerModal && selectedPlayer && (
        <div className="modal-overlay" onClick={closePlayerModal}>
          <div className="player-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>玩家详细统计</h2>
              <button className="close-btn" onClick={closePlayerModal}>×</button>
            </div>
            <div className="modal-content">
              <div className="player-basic-info">
                <h3>{selectedPlayer.nickname || selectedPlayer.username}</h3>
                {selectedPlayer.nickname && selectedPlayer.username !== selectedPlayer.nickname && (
                  <p className="username">({selectedPlayer.username})</p>
                )}
                <p className="rank">排名: #{selectedPlayer.rank}</p>
                <p className="matches">总比赛场次: {selectedPlayer.total_matches}</p>
              </div>
              
              <div className="stats-grid">
                <div className="stat-group">
                  <h4>基础统计</h4>
                  <div className="stat-item">
                    <span className="stat-label">Rating 2.0:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_rating2.toFixed(3)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">Rating 1.0:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_rating.toFixed(3)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">K/D 比率:</span>
                    <span className="stat-value">{selectedPlayer.stats.kd_ratio.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">ADR:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_adr.toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">胜率:</span>
                    <span className="stat-value">{(selectedPlayer.stats.win_rate * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="stat-group">
                  <h4>场均数据</h4>
                  <div className="stat-item">
                    <span className="stat-label">场均击杀:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_kills.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">场均死亡:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_deaths.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">场均助攻:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_assists.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">爆头率:</span>
                    <span className="stat-value">{(selectedPlayer.stats.avg_headshot_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">场均AWP击杀:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_awp_kills.toFixed(2)}</span>
                  </div>
                </div>

                <div className="stat-group">
                  <h4>首杀/首死统计</h4>
                  <div className="stat-item">
                    <span className="stat-label">场均首杀:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_first_kill.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">场均首死:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_first_death.toFixed(2)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">首杀率:</span>
                    <span className="stat-value">{(selectedPlayer.stats.first_kill_rate * 100).toFixed(1)}%</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">首死率:</span>
                    <span className="stat-value">{(selectedPlayer.stats.first_death_rate * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="stat-group">
                  <h4>其他统计</h4>
                  <div className="stat-item">
                    <span className="stat-label">MVP次数:</span>
                    <span className="stat-value">{selectedPlayer.stats.mvp_count}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">KAST:</span>
                    <span className="stat-value">{(selectedPlayer.stats.avg_kast * 100).toFixed(1)}%</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">RWS:</span>
                    <span className="stat-value">{selectedPlayer.stats.avg_rws.toFixed(1)}</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">最后比赛:</span>
                    <span className="stat-value">{formatTime(selectedPlayer.last_match_time)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Leaderboard;