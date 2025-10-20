-- 5E对战平台数据库表结构设计（优化版）
-- 基于实际API返回数据结构设计

-- 创建数据库
CREATE DATABASE IF NOT EXISTS cs_match_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cs_match_data;

-- 比赛基本信息表
CREATE TABLE IF NOT EXISTS matches (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    match_id VARCHAR(100) UNIQUE NOT NULL COMMENT '比赛ID',
    match_code VARCHAR(100) NOT NULL COMMENT '比赛代码',
    
    -- 基本信息
    game_mode INT NOT NULL COMMENT '游戏模式',
    game_name VARCHAR(50) COMMENT '游戏名称',
    map_name VARCHAR(50) NOT NULL COMMENT '地图名称',
    map_desc VARCHAR(100) COMMENT '地图描述',
    
    -- 时间信息
    start_time BIGINT NOT NULL COMMENT '开始时间戳',
    end_time BIGINT COMMENT '结束时间戳',
    
    -- 比分信息
    round_total INT NOT NULL COMMENT '总回合数',
    group1_all_score INT NOT NULL COMMENT '队伍1总得分',
    group2_all_score INT NOT NULL COMMENT '队伍2总得分',
    group1_fh_score INT DEFAULT 0 COMMENT '队伍1上半场得分',
    group1_sh_score INT DEFAULT 0 COMMENT '队伍1下半场得分',
    group2_fh_score INT DEFAULT 0 COMMENT '队伍2上半场得分',
    group2_sh_score INT DEFAULT 0 COMMENT '队伍2下半场得分',
    
    -- 队伍信息
    group1_fh_role INT DEFAULT 0 COMMENT '队伍1上半场角色(1=CT,0=T)',
    group2_fh_role INT DEFAULT 0 COMMENT '队伍2上半场角色(1=CT,0=T)',
    group1_sh_role INT DEFAULT 0 COMMENT '队伍1下半场角色',
    group2_sh_role INT DEFAULT 0 COMMENT '队伍2下半场角色',
    group1_uids TEXT COMMENT '队伍1玩家UID列表',
    group2_uids TEXT COMMENT '队伍2玩家UID列表',
    
    -- 胜负信息
    match_winner INT COMMENT '获胜队伍(1或2)',
    knife_winner INT COMMENT '刀局获胜者',
    knife_winner_role INT COMMENT '刀局获胜者角色',
    
    -- ELO信息
    group1_origin_elo INT DEFAULT 0 COMMENT '队伍1原始ELO',
    group1_change_elo INT DEFAULT 0 COMMENT '队伍1ELO变化',
    group2_origin_elo INT DEFAULT 0 COMMENT '队伍2原始ELO',
    group2_change_elo INT DEFAULT 0 COMMENT '队伍2ELO变化',
    
    -- 服务器信息
    demo_url TEXT COMMENT 'Demo下载链接',
    location VARCHAR(50) COMMENT '服务器位置',
    location_full VARCHAR(100) COMMENT '完整服务器位置',
    server_ip VARCHAR(50) COMMENT '服务器IP',
    server_port VARCHAR(10) COMMENT '服务器端口',
    
    -- 赛季信息
    season VARCHAR(20) COMMENT '赛季',
    year INT COMMENT '年份',
    match_mode INT COMMENT '比赛模式',
    
    -- 荣誉信息
    mvp_uid BIGINT COMMENT 'MVP玩家UID',
    most_kill_uid BIGINT COMMENT '最多击杀玩家UID',
    most_assist_uid BIGINT COMMENT '最多助攻玩家UID',
    most_awp_uid BIGINT COMMENT '最多AWP击杀玩家UID',
    most_headshot_uid BIGINT COMMENT '最多爆头玩家UID',
    most_first_kill_uid BIGINT COMMENT '最多首杀玩家UID',
    most_1v2_uid BIGINT COMMENT '最多1v2玩家UID',
    most_jump_uid BIGINT COMMENT '最多跳跃玩家UID',
    most_end_uid BIGINT COMMENT '最多残局玩家UID',
    
    -- 其他信息
    status INT DEFAULT 1 COMMENT '状态',
    waiver INT DEFAULT 0 COMMENT '弃权',
    cs_type INT DEFAULT 0 COMMENT 'CS类型',
    priority_show_type INT DEFAULT 0 COMMENT '优先显示类型',
    pug10m_show_type INT DEFAULT 0 COMMENT 'PUG10分钟显示类型',
    credit_match_status INT DEFAULT 0 COMMENT '信用比赛状态',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_match_id (match_id),
    INDEX idx_start_time (start_time),
    INDEX idx_map_name (map_name),
    INDEX idx_game_mode (game_mode),
    INDEX idx_season (season),
    INDEX idx_year (year)
) ENGINE=InnoDB COMMENT='比赛基本信息表';

-- 玩家基本信息表
CREATE TABLE IF NOT EXISTS players (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uid BIGINT UNIQUE NOT NULL COMMENT '玩家UID',
    steam_id VARCHAR(50) UNIQUE COMMENT 'Steam ID',
    username VARCHAR(100) COMMENT '用户名',
    nickname VARCHAR(100) COMMENT '昵称',
    uuid VARCHAR(100) COMMENT 'UUID',
    email VARCHAR(100) COMMENT '邮箱',
    area VARCHAR(10) COMMENT '区号',
    mobile VARCHAR(20) COMMENT '手机号',
    
    -- 个人资料
    domain VARCHAR(100) COMMENT '域名',
    avatar_url TEXT COMMENT '头像URL',
    avatar_audit_status INT DEFAULT 0 COMMENT '头像审核状态',
    rgb_avatar_url TEXT COMMENT 'RGB头像URL',
    photo_url TEXT COMMENT '照片URL',
    gender INT DEFAULT 0 COMMENT '性别',
    birthday BIGINT DEFAULT 0 COMMENT '生日时间戳',
    country_id VARCHAR(10) COMMENT '国家ID',
    region_id VARCHAR(20) COMMENT '地区ID',
    city_id VARCHAR(20) COMMENT '城市ID',
    language VARCHAR(50) COMMENT '语言',
    
    -- 平台信息
    platform_level INT DEFAULT 0 COMMENT '平台等级',
    platform_exp BIGINT DEFAULT 0 COMMENT '平台经验',
    
    -- 信用信息
    credit INT DEFAULT 0 COMMENT '信用分',
    credit_level INT DEFAULT 0 COMMENT '信用等级',
    credit_score BIGINT DEFAULT 0 COMMENT '信用积分',
    credit_status INT DEFAULT 0 COMMENT '信用状态',
    
    -- 认证信息
    certify_status INT DEFAULT 0 COMMENT '认证状态',
    certify_age INT DEFAULT 0 COMMENT '认证年龄',
    
    -- 状态信息
    user_status INT DEFAULT 0 COMMENT '用户状态',
    new_user INT DEFAULT 0 COMMENT '是否新用户',
    anticheat_type INT DEFAULT 0 COMMENT '反作弊类型',
    anticheat_status VARCHAR(10) DEFAULT '0' COMMENT '反作弊状态',
    
    -- 时间信息
    user_created_at BIGINT COMMENT '用户创建时间戳',
    user_updated_at BIGINT COMMENT '用户更新时间戳',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_uid (uid),
    INDEX idx_steam_id (steam_id),
    INDEX idx_username (username)
) ENGINE=InnoDB COMMENT='玩家基本信息表';

-- 比赛玩家数据表（主要数据）
CREATE TABLE IF NOT EXISTS match_player_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    match_id VARCHAR(100) NOT NULL COMMENT '比赛ID',
    uid BIGINT NOT NULL COMMENT '玩家UID',
    steam_id VARCHAR(50) NOT NULL COMMENT 'Steam ID',
    team_id INT NOT NULL COMMENT '队伍ID(1或2)',
    
    -- 基础战斗数据
    kills INT DEFAULT 0 COMMENT '击杀数',
    deaths INT DEFAULT 0 COMMENT '死亡数',
    assists INT DEFAULT 0 COMMENT '助攻数',
    adr DECIMAL(8,2) DEFAULT 0 COMMENT '平均每回合伤害',
    rating DECIMAL(6,3) DEFAULT 0 COMMENT 'Rating评分',
    rating2 DECIMAL(6,3) DEFAULT 0 COMMENT 'Rating2.0评分',
    kast DECIMAL(4,3) DEFAULT 0 COMMENT 'KAST评分',
    rws DECIMAL(8,2) DEFAULT 0 COMMENT 'RWS评分',
    
    -- 击杀详情
    kill_1 INT DEFAULT 0 COMMENT '1杀回合数',
    kill_2 INT DEFAULT 0 COMMENT '2杀回合数',
    kill_3 INT DEFAULT 0 COMMENT '3杀回合数',
    kill_4 INT DEFAULT 0 COMMENT '4杀回合数',
    kill_5 INT DEFAULT 0 COMMENT '5杀回合数',
    headshot INT DEFAULT 0 COMMENT '爆头数',
    per_headshot DECIMAL(4,3) DEFAULT 0 COMMENT '爆头率',
    
    -- AWP数据
    awp_kill INT DEFAULT 0 COMMENT 'AWP击杀数',
    awp_kill_ct INT DEFAULT 0 COMMENT 'CT方AWP击杀数',
    awp_kill_t INT DEFAULT 0 COMMENT 'T方AWP击杀数',
    
    -- 首杀数据
    first_kill INT DEFAULT 0 COMMENT '首杀数',
    first_death INT DEFAULT 0 COMMENT '首死数',
    
    -- 残局数据
    end_1v1 INT DEFAULT 0 COMMENT '1v1残局数',
    end_1v2 INT DEFAULT 0 COMMENT '1v2残局数',
    end_1v3 INT DEFAULT 0 COMMENT '1v3残局数',
    end_1v4 INT DEFAULT 0 COMMENT '1v4残局数',
    end_1v5 INT DEFAULT 0 COMMENT '1v5残局数',
    
    -- 道具数据
    flash_enemy INT DEFAULT 0 COMMENT '致盲敌人次数',
    flash_enemy_time INT DEFAULT 0 COMMENT '致盲敌人时长',
    flash_team INT DEFAULT 0 COMMENT '致盲队友次数',
    flash_team_time INT DEFAULT 0 COMMENT '致盲队友时长',
    flash_time INT DEFAULT 0 COMMENT '总致盲时长',
    throw_harm INT DEFAULT 0 COMMENT '投掷物伤害',
    throw_harm_enemy INT DEFAULT 0 COMMENT '对敌投掷物伤害',
    
    -- 炸弹相关
    planted_bomb INT DEFAULT 0 COMMENT '安包数',
    defused_bomb INT DEFAULT 0 COMMENT '拆包数',
    explode_bomb INT DEFAULT 0 COMMENT '爆炸数',
    
    -- 其他数据
    jump_total INT DEFAULT 0 COMMENT '跳跃次数',
    team_kill INT DEFAULT 0 COMMENT '误杀队友数',
    benefit_kill INT DEFAULT 0 COMMENT '补枪击杀数',
    revenge_kill INT DEFAULT 0 COMMENT '复仇击杀数',
    assisted_kill INT DEFAULT 0 COMMENT '被助攻击杀数',
    perfect_kill INT DEFAULT 0 COMMENT '完美击杀数',
    hold_total INT DEFAULT 0 COMMENT '持有总数',
    
    -- 助攻详情
    many_assists_cnt1 INT DEFAULT 0 COMMENT '1助攻回合数',
    many_assists_cnt2 INT DEFAULT 0 COMMENT '2助攻回合数',
    many_assists_cnt3 INT DEFAULT 0 COMMENT '3助攻回合数',
    many_assists_cnt4 INT DEFAULT 0 COMMENT '4助攻回合数',
    many_assists_cnt5 INT DEFAULT 0 COMMENT '5助攻回合数',
    
    -- 荣誉标记
    is_mvp BOOLEAN DEFAULT FALSE COMMENT '是否MVP',
    is_svp BOOLEAN DEFAULT FALSE COMMENT '是否SVP',
    is_most_kill BOOLEAN DEFAULT FALSE COMMENT '是否最多击杀',
    is_most_assist BOOLEAN DEFAULT FALSE COMMENT '是否最多助攻',
    is_most_awp BOOLEAN DEFAULT FALSE COMMENT '是否最多AWP击杀',
    is_most_headshot BOOLEAN DEFAULT FALSE COMMENT '是否最多爆头',
    is_most_first_kill BOOLEAN DEFAULT FALSE COMMENT '是否最多首杀',
    is_most_1v2 BOOLEAN DEFAULT FALSE COMMENT '是否最多1v2',
    is_most_jump BOOLEAN DEFAULT FALSE COMMENT '是否最多跳跃',
    is_most_end BOOLEAN DEFAULT FALSE COMMENT '是否最多残局',
    is_highlight BOOLEAN DEFAULT FALSE COMMENT '是否高光',
    
    -- 胜负和等级变化
    is_win BOOLEAN DEFAULT FALSE COMMENT '是否获胜',
    is_tie BOOLEAN DEFAULT FALSE COMMENT '是否平局',
    change_elo DECIMAL(8,2) DEFAULT 0 COMMENT 'ELO变化',
    origin_elo DECIMAL(8,2) DEFAULT 0 COMMENT '原始ELO',
    
    -- 等级信息
    level_id INT DEFAULT 0 COMMENT '等级ID',
    origin_level_id INT DEFAULT 0 COMMENT '原始等级ID',
    star_num INT DEFAULT 0 COMMENT '星数',
    origin_star_num INT DEFAULT 0 COMMENT '原始星数',
    change_rank INT DEFAULT 0 COMMENT '段位变化',
    origin_rank INT DEFAULT 0 COMMENT '原始段位',
    
    -- 比赛相关
    match_mode INT COMMENT '比赛模式',
    match_team_id INT DEFAULT 0 COMMENT '比赛队伍ID',
    match_time BIGINT COMMENT '比赛时间戳',
    day VARCHAR(10) COMMENT '比赛日期',
    season VARCHAR(20) COMMENT '赛季',
    year INT COMMENT '年份',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_match_player (match_id, uid),
    INDEX idx_match_id (match_id),
    INDEX idx_uid (uid),
    INDEX idx_steam_id (steam_id),
    INDEX idx_team_id (team_id),
    INDEX idx_rating (rating),
    INDEX idx_kills (kills),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
    FOREIGN KEY (uid) REFERENCES players(uid) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='比赛玩家数据表';

-- VIP Plus 扩展数据表
CREATE TABLE IF NOT EXISTS match_player_vip_stats (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    match_id VARCHAR(100) NOT NULL COMMENT '比赛ID',
    steam_id VARCHAR(50) NOT NULL COMMENT 'Steam ID',
    uid BIGINT COMMENT '玩家UID',
    
    -- VIP Plus 特有数据
    fd_ct INT DEFAULT 0 COMMENT 'CT方首杀死亡数',
    fd_t INT DEFAULT 0 COMMENT 'T方首杀死亡数',
    kast DECIMAL(4,3) DEFAULT 0 COMMENT 'KAST评分',
    awp_kill INT DEFAULT 0 COMMENT 'AWP击杀数',
    awp_kill_ct INT DEFAULT 0 COMMENT 'CT方AWP击杀数',
    awp_kill_t INT DEFAULT 0 COMMENT 'T方AWP击杀数',
    damage_stats INT DEFAULT 0 COMMENT '伤害统计',
    damage_receive INT DEFAULT 0 COMMENT '受到伤害',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_match_steam (match_id, steam_id),
    INDEX idx_match_id (match_id),
    INDEX idx_steam_id (steam_id),
    INDEX idx_uid (uid),
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='VIP Plus扩展数据表';

-- 数据采集日志表
CREATE TABLE IF NOT EXISTS data_collection_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    match_id VARCHAR(100) NOT NULL COMMENT '比赛ID',
    api_type ENUM('match_detail', 'vip_plus') NOT NULL COMMENT 'API类型',
    status ENUM('pending', 'success', 'failed', 'skipped') DEFAULT 'pending' COMMENT '采集状态',
    error_message TEXT COMMENT '错误信息',
    response_data JSON COMMENT '响应数据',
    request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '请求时间',
    response_time TIMESTAMP NULL COMMENT '响应时间',
    
    INDEX idx_match_id (match_id),
    INDEX idx_status (status),
    INDEX idx_api_type (api_type),
    INDEX idx_request_time (request_time)
) ENGINE=InnoDB COMMENT='数据采集日志表';

-- 创建视图：完整的玩家比赛数据
CREATE OR REPLACE VIEW player_match_complete_stats AS
SELECT 
    mps.*,
    mpv.fd_ct as vip_fd_ct,
    mpv.fd_t as vip_fd_t,
    mpv.kast as vip_kast,
    mpv.awp_kill as vip_awp_kill,
    mpv.awp_kill_ct as vip_awp_kill_ct,
    mpv.awp_kill_t as vip_awp_kill_t,
    mpv.damage_stats as vip_damage_stats,
    mpv.damage_receive as vip_damage_receive,
    p.username,
    p.nickname,
    p.platform_level,
    m.map_name,
    m.start_time,
    m.match_winner
FROM match_player_stats mps
LEFT JOIN match_player_vip_stats mpv ON mps.match_id = mpv.match_id AND mps.steam_id = mpv.steam_id
LEFT JOIN players p ON mps.uid = p.uid
LEFT JOIN matches m ON mps.match_id = m.match_id;

-- ========================================
-- 自定义比赛模块相关表
-- ========================================

-- 自定义比赛表
CREATE TABLE IF NOT EXISTS custom_tournaments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(200) NOT NULL COMMENT '比赛名称',
    description TEXT COMMENT '比赛描述',
    
    -- 时间信息
    start_time BIGINT NOT NULL COMMENT '比赛开始时间戳',
    end_time BIGINT NOT NULL COMMENT '比赛结束时间戳',
    
    -- 状态信息
    status ENUM('draft', 'active', 'completed', 'cancelled') DEFAULT 'draft' COMMENT '比赛状态',
    
    -- 创建者信息
    creator_uid BIGINT NOT NULL COMMENT '创建者UID',
    
    -- 统计信息
    total_matches INT DEFAULT 0 COMMENT '总比赛场数',
    completed_matches INT DEFAULT 0 COMMENT '已完成比赛场数',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_creator_uid (creator_uid),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_name (name),
    FOREIGN KEY (creator_uid) REFERENCES players(uid) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='自定义比赛表';

-- 自定义比赛队伍表
CREATE TABLE IF NOT EXISTS custom_tournament_teams (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tournament_id BIGINT NOT NULL COMMENT '比赛ID',
    team_name VARCHAR(100) NOT NULL COMMENT '队伍名称',
    
    -- 队员信息（存储UID列表，JSON格式）
    player_uids JSON NOT NULL COMMENT '队员UID列表',
    
    -- 队长信息
    captain_uid BIGINT COMMENT '队长UID',
    
    -- 统计信息
    wins INT DEFAULT 0 COMMENT '胜场数',
    losses INT DEFAULT 0 COMMENT '负场数',
    total_rounds_won INT DEFAULT 0 COMMENT '总赢得回合数',
    total_rounds_lost INT DEFAULT 0 COMMENT '总失败回合数',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_tournament_id (tournament_id),
    INDEX idx_captain_uid (captain_uid),
    INDEX idx_team_name (team_name),
    FOREIGN KEY (tournament_id) REFERENCES custom_tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (captain_uid) REFERENCES players(uid) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='自定义比赛队伍表';

-- 自定义比赛关联matches表
CREATE TABLE IF NOT EXISTS custom_tournament_matches (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tournament_id BIGINT NOT NULL COMMENT '比赛ID',
    match_id VARCHAR(100) NOT NULL COMMENT '关联的比赛ID',
    
    -- 队伍信息
    team1_id BIGINT COMMENT '队伍1 ID',
    team2_id BIGINT COMMENT '队伍2 ID',
    
    -- 比赛阶段信息
    round_name VARCHAR(100) COMMENT '比赛轮次名称（如：小组赛、半决赛等）',
    match_order INT DEFAULT 0 COMMENT '比赛顺序',
    
    -- 比赛结果
    winner_team_id BIGINT COMMENT '获胜队伍ID',
    
    -- 关联时间
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '关联时间',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uk_tournament_match (tournament_id, match_id),
    INDEX idx_tournament_id (tournament_id),
    INDEX idx_match_id (match_id),
    INDEX idx_team1_id (team1_id),
    INDEX idx_team2_id (team2_id),
    INDEX idx_winner_team_id (winner_team_id),
    FOREIGN KEY (tournament_id) REFERENCES custom_tournaments(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
    FOREIGN KEY (team1_id) REFERENCES custom_tournament_teams(id) ON DELETE SET NULL,
    FOREIGN KEY (team2_id) REFERENCES custom_tournament_teams(id) ON DELETE SET NULL,
    FOREIGN KEY (winner_team_id) REFERENCES custom_tournament_teams(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='自定义比赛关联matches表';

-- 创建视图：自定义比赛完整信息
CREATE OR REPLACE VIEW custom_tournament_complete_view AS
SELECT 
    ct.*,
    p.username as creator_username,
    COUNT(DISTINCT ctt.id) as team_count,
    COUNT(DISTINCT ctm.id) as match_count
FROM custom_tournaments ct
LEFT JOIN players p ON ct.creator_uid = p.uid
LEFT JOIN custom_tournament_teams ctt ON ct.id = ctt.tournament_id
LEFT JOIN custom_tournament_matches ctm ON ct.id = ctm.tournament_id
GROUP BY ct.id;

-- 创建视图：自定义比赛队伍详细信息
CREATE OR REPLACE VIEW custom_tournament_team_details AS
SELECT 
    ctt.*,
    ct.name as tournament_name,
    ct.status as tournament_status,
    p.username as captain_username
FROM custom_tournament_teams ctt
LEFT JOIN custom_tournaments ct ON ctt.tournament_id = ct.id
LEFT JOIN players p ON ctt.captain_uid = p.uid;