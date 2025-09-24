import axios from 'axios';

// 根据环境设置API基础URL
const getBaseURL = () => {
  // 开发环境
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:5001/api';
  }
  
  // 生产环境 - 使用相对路径，通过nginx代理
  return '/api';
};

// 创建axios实例
const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.config?.url, error.message);
    return Promise.reject(error);
  }
);

// API接口定义
export interface Player {
  steam_id: string;
  username: string;
  nickname: string;
  platform_level: number;
  avatar_url: string;
  total_matches: number;
}

export interface SearchPlayersResponse {
  players: Player[];
  total: number;
  search_term: string;
}

// 后端返回的原始比赛数据结构
export interface RawMatch {
  match_id: string;
  start_time: number;
  map_name: string;
  match_winner: number;
  avg_rating: number;
  max_kills: number;
  player_count: number;
}

// 后端返回的比赛列表响应结构
export interface RawMatchesResponse {
  matches: RawMatch[];
  pagination?: {
    limit: number;
    page: number;
    pages: number;
    total: number;
  };
}

// 前端使用的比赛列表响应结构
export interface MatchesResponse {
  matches: Match[];
  pagination: {
    limit: number;
    page: number;
    pages: number;
    total: number;
  };
}

// 前端使用的比赛数据结构（转换后）
export interface Match {
  match_id: string;
  match_time: string;
  map_name: string;
  match_result: string;
  score: string;
  kd_ratio: number;
  adr: number;
  rating: number;
  kills: number;
  deaths: number;
  assists: number;
}

// 后端返回的原始玩家统计数据结构
export interface RawPlayerStats {
  player_info: {
    nickname: string | null;
    username: string;
    steam_id: string;
    platform_level: number | null;
  };
  match_summary: {
    total_matches: number;
    wins: number;
    losses: number;
    ties: number;
    win_rate: number;
  };
  performance_stats: {
    avg_rating: number;
    avg_rating2: number;
    kd_ratio: string;
    kda_ratio: string;
    avg_adr: number;
    avg_kast: number;
    avg_headshot_rate: number;
  };
  combat_stats: {
    total_kills: string;
    total_deaths: string;
    total_assists: string;
    total_headshots: string;
    total_first_kills: string;
    total_first_deaths: string;
    first_kill_rate: string;
  };
  multikill_stats: {
    total_1k: string;
    total_2k: string;
    total_3k: string;
    total_4k: string;
    total_5k: string;
  };
  clutch_stats: {
    total_1v1: string;
    total_1v2: string;
    total_1v3: string;
    total_1v4: number;
    total_1v5: number;
  };
  awp_stats: {
    total_awp_kills: string;
    awp_kills_ct: number;
    awp_kills_t: number;
  };
  elo_stats: {
    avg_elo: number;
    max_elo: number;
    min_elo: number;
    total_elo_change: number;
  };
  honors: {
    mvp_count: number;
    svp_count: number;
  };
}

// 前端使用的标准化玩家统计数据结构
export interface PlayerStats {
  nickname: string;
  total_matches: number;
  wins: number;
  losses: number;
  ties: number;
  win_rate: number;
  avg_rating: number;
  avg_rating2: number;
  kd_ratio: number;
  kda_ratio: number;
  avg_adr: number;
  avg_kast: number;
  total_kills: number;
  total_deaths: number;
  total_assists: number;
  total_headshots: number;
  headshot_rate: number;
  first_kill_rate: number;
  total_1k: number;
  total_2k: number;
  total_3k: number;
  total_4k: number;
  total_5k: number;
  total_1v1: number;
  total_1v2: number;
  total_1v3: number;
  total_awp_kills: number;
  mvp_count: number;
  svp_count: number;
}

// 后端返回的原始比赛数据结构
export interface RawPlayerMatch {
  match_id: string;
  map_name: string;
  start_time: number;  // 时间戳
  kills: number;
  deaths: number;
  assists: number;
  adr: number;
  rating: number;
  kd_ratio: number;
  match_result: string;
  is_mvp: boolean;
  is_svp: boolean;
}

// 后端返回的玩家比赛记录响应结构
export interface PlayerMatchesResponse {
  matches: RawPlayerMatch[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// 前端使用的玩家比赛记录响应结构
export interface PlayerMatchesResult {
  matches: PlayerMatch[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// 前端使用的标准化比赛数据结构
export interface PlayerMatch {
  match_id: string;
  match_time: string;
  map_name: string;
  match_result: string;
  kills: number;
  deaths: number;
  assists: number;
  rating: number;
  adr: number;
  kd_ratio: number;
  is_mvp?: boolean;
  is_svp?: boolean;
}

// 比赛详情中的玩家数据
export interface MatchPlayer {
  username: string;
  nickname: string;
  steam_id: string;
  team_id: number;
  platform_level: number;
  kills: number;
  deaths: number;
  assists: number;
  adr: number;
  rating: number;
  rating2: number;
  kast: number;
  rws: number | null;
  headshot: number;
  per_headshot: number;
  first_kill: number;
  first_death: number;
  awp_kill: number;
  is_mvp: boolean;
  is_svp: boolean;
  is_win: boolean;
}

// 比赛基本信息
export interface MatchInfo {
  match_id: string;
  map_name: string;
  start_time: string;
  match_winner: number;
}

// 比赛详情响应
export interface MatchDetailResponse {
  match_info: MatchInfo;
  players: MatchPlayer[];
  player_count: number;
}

// API方法
// 数据转换函数
const convertRawMatchToMatch = (rawMatch: RawMatch): Match => {
  return {
    match_id: rawMatch.match_id,
    match_time: new Date(rawMatch.start_time * 1000).toISOString(), // 转换时间戳为ISO字符串
    map_name: rawMatch.map_name,
    match_result: rawMatch.match_winner === 1 ? '胜利' : rawMatch.match_winner === 2 ? '失败' : '平局',
    score: `${rawMatch.player_count}人比赛`, // 暂时用玩家数量作为比分信息
    kd_ratio: 0, // 后端没有提供个人K/D数据，设为0
    adr: 0, // 后端没有提供个人ADR数据，设为0
    rating: rawMatch.avg_rating,
    kills: rawMatch.max_kills, // 使用最高击杀数作为击杀数
    deaths: 0, // 后端没有提供个人死亡数据，设为0
    assists: 0, // 后端没有提供个人助攻数据，设为0
  };
};

// 转换函数：将后端返回的原始玩家统计数据转换为前端标准格式
const convertRawPlayerStatsToPlayerStats = (rawStats: RawPlayerStats): PlayerStats => {
  return {
    nickname: rawStats.player_info.nickname || rawStats.player_info.username,
    total_matches: rawStats.match_summary.total_matches,
    wins: rawStats.match_summary.wins,
    losses: rawStats.match_summary.losses,
    ties: rawStats.match_summary.ties,
    win_rate: rawStats.match_summary.win_rate,
    avg_rating: rawStats.performance_stats.avg_rating,
    avg_rating2: rawStats.performance_stats.avg_rating2,
    kd_ratio: parseFloat(rawStats.performance_stats.kd_ratio),
    kda_ratio: parseFloat(rawStats.performance_stats.kda_ratio),
    avg_adr: rawStats.performance_stats.avg_adr,
    avg_kast: rawStats.performance_stats.avg_kast,
    total_kills: parseInt(rawStats.combat_stats.total_kills),
    total_deaths: parseInt(rawStats.combat_stats.total_deaths),
    total_assists: parseInt(rawStats.combat_stats.total_assists),
    total_headshots: parseInt(rawStats.combat_stats.total_headshots),
    headshot_rate: rawStats.performance_stats.avg_headshot_rate,
    first_kill_rate: parseFloat(rawStats.combat_stats.first_kill_rate),
    total_1k: parseInt(rawStats.multikill_stats.total_1k),
    total_2k: parseInt(rawStats.multikill_stats.total_2k),
    total_3k: parseInt(rawStats.multikill_stats.total_3k),
    total_4k: parseInt(rawStats.multikill_stats.total_4k),
    total_5k: parseInt(rawStats.multikill_stats.total_5k),
    total_1v1: parseInt(rawStats.clutch_stats.total_1v1),
    total_1v2: parseInt(rawStats.clutch_stats.total_1v2),
    total_1v3: parseInt(rawStats.clutch_stats.total_1v3),
    total_awp_kills: parseInt(rawStats.awp_stats.total_awp_kills),
    mvp_count: rawStats.honors.mvp_count,
    svp_count: rawStats.honors.svp_count,
  };
};

// 将后端返回的原始比赛数据转换为前端标准格式
const convertRawPlayerMatchToPlayerMatch = (rawMatch: RawPlayerMatch): PlayerMatch => {
  return {
    match_id: rawMatch.match_id,
    match_time: new Date(rawMatch.start_time * 1000).toISOString(), // 将时间戳转换为ISO字符串
    map_name: rawMatch.map_name,
    match_result: rawMatch.match_result,
    kills: rawMatch.kills,
    deaths: rawMatch.deaths,
    assists: rawMatch.assists,
    rating: rawMatch.rating,
    adr: rawMatch.adr,
    kd_ratio: rawMatch.kd_ratio,
    is_mvp: rawMatch.is_mvp,
    is_svp: rawMatch.is_svp,
  };
};

export interface MatchesFilters {
  startDate?: string;
  endDate?: string;
  mapName?: string;
}

export const matchesAPI = {
  // 获取比赛列表（支持分页和筛选）
  getMatches: async (page: number = 1, limit: number = 20, filters?: MatchesFilters): Promise<MatchesResponse> => {
    let url = `/matches?page=${page}&limit=${limit}`;
    
    if (filters) {
      if (filters.startDate) {
        url += `&start_date=${filters.startDate}`;
      }
      if (filters.endDate) {
        url += `&end_date=${filters.endDate}`;
      }
      if (filters.mapName) {
        url += `&map_name=${filters.mapName}`;
      }
    }
    
    const response = await api.get(url);
    const data = response.data;
    
    // 检查返回的数据结构
    if (data && typeof data === 'object' && 'matches' in data && Array.isArray(data.matches)) {
      // 转换比赛数据格式
      const rawResponse = data as RawMatchesResponse;
      const convertedMatches = rawResponse.matches.map(convertRawMatchToMatch);
      return {
        matches: convertedMatches,
        pagination: rawResponse.pagination || {
          page: 1,
          limit: 20,
          total: convertedMatches.length,
          pages: 1
        }
      };
    } else if (Array.isArray(data)) {
      // 如果直接返回数组（兼容旧格式）
      const convertedMatches = (data as RawMatch[]).map(convertRawMatchToMatch);
      return {
        matches: convertedMatches,
        pagination: {
          page: 1,
          limit: data.length,
          total: data.length,
          pages: 1
        }
      };
    } else {
      console.error('Unexpected data structure from /matches API:', data);
      return {
        matches: [],
        pagination: {
          page: 1,
          limit: 20,
          total: 0,
          pages: 0
        }
      };
    }
  },

  // 获取比赛详情
  getMatchDetail: async (matchId: string): Promise<MatchDetailResponse> => {
    try {
      const response = await api.get<MatchDetailResponse>(`/match/${matchId}/players`);
      console.log('Match detail response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching match detail:', error);
      throw error;
    }
  },
};

// 排行榜相关接口定义
export interface LeaderboardPlayer {
  rank: number;
  username: string;
  nickname: string;
  platform_level: number;
  steam_id: string;
  total_matches: number;
  stat_value: number;
  stats: {
    avg_rating2: number;
    avg_rating: number;
    avg_adr: number;
    kd_ratio: number;
    total_kills: number;
    total_deaths: number;
    total_assists: number;
    avg_headshot_rate: number;
    total_first_kills: number;
    total_first_deaths: number;
    first_kill_rate: number;
    first_death_rate: number;
    total_awp_kills: number;
    mvp_count: number;
    win_rate: number;
    avg_kast: number;
    avg_rws: number;
  };
  last_match_time: number;
}

export interface LeaderboardResponse {
  success: boolean;
  data: LeaderboardPlayer[];
  meta: {
    stat_type: string;
    total_players: number;
    map_filter: string;
    season_filter: string;
    min_matches: number;
    limit: number;
  };
}

export interface StatType {
  key: string;
  name: string;
  description: string;
}

export interface LeaderboardFilters {
  maps: string[];
  seasons: string[];
}

export const playersAPI = {
  // 搜索玩家
  searchPlayers: async (nickname: string): Promise<Player[]> => {
    const response = await api.get<SearchPlayersResponse>(`/players/search?nickname=${encodeURIComponent(nickname)}`);
    return response.data.players;
  },

  // 获取玩家统计数据
  getPlayerStats: async (steamId: string): Promise<PlayerStats> => {
    const response = await api.get<RawPlayerStats>(`/player/${steamId}/stats`);
    return convertRawPlayerStatsToPlayerStats(response.data);
  },

  // 获取玩家比赛记录
  getPlayerMatches: async (steamId: string, page: number = 1, limit: number = 10): Promise<PlayerMatchesResult> => {
    const response = await api.get<PlayerMatchesResponse>(`/player/${steamId}/recent-matches?page=${page}&limit=${limit}`);
    
    const convertedMatches = response.data.matches.map(convertRawPlayerMatchToPlayerMatch);
    
    return {
      matches: convertedMatches,
      pagination: response.data.pagination
    };
  },
};

export const leaderboardAPI = {
  // 获取排行榜数据
  getLeaderboard: async (
    statType: string = 'rating2',
    mapFilter: string = ''
  ): Promise<LeaderboardResponse> => {
    const params = new URLSearchParams({
      stat: statType
    });
    
    if (mapFilter) params.append('map', mapFilter);
    
    const response = await api.get<LeaderboardResponse>(`/leaderboard?${params.toString()}`);
    return response.data;
  },

  // 获取可用的统计类型
  getStatsTypes: async (): Promise<StatType[]> => {
    const response = await api.get<{success: boolean; data: StatType[]}>('/leaderboard/stats-types');
    return response.data.data;
  },

  // 获取筛选选项
  getFilters: async (): Promise<LeaderboardFilters> => {
    const response = await api.get<{success: boolean; data: LeaderboardFilters}>('/leaderboard/filters');
    return response.data.data;
  },
};

export default api;