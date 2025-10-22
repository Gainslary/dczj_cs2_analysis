#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import json
import os
from datetime import datetime, date
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # 允许跨域请求

class DateTimeEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理datetime和date对象"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

app.json_encoder = DateTimeEncoder

# 创建数据库连接池
try:
    DATABASE_CONFIG = {
        'host': os.getenv('DB_HOST', '106.14.121.148'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '9AkWaqCsrd12'),
        'database': os.getenv('DB_NAME', 'cs_match_data')
    }

    # 创建连接池
    connection_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="csgo_pool",
        pool_size=5,  # 连接池大小
        pool_reset_session=True,
        **DATABASE_CONFIG
    )
    logger.info("数据库连接池初始化成功")
except Exception as e:
    logger.error(f"数据库连接池初始化失败: {e}")
    connection_pool = None

def get_database_connection():
    """从连接池获取数据库连接"""
    try:
        if connection_pool:
            connection = connection_pool.get_connection()
            return connection
        else:
            # 备用方案：直接创建连接
            connection = mysql.connector.connect(**DATABASE_CONFIG)
            return connection
    except Error as e:
        logger.error(f"数据库连接错误: {e}")
        return None

def execute_query(query, params=None):
    """执行数据库查询"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    except Error as e:
        logger.error(f"查询执行错误: {e}")
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/players', methods=['GET'])
def get_players():
    """获取玩家数据"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', '')
        map_name = request.args.get('map', '')
        team_id = request.args.get('team', '')
        sort_by = request.args.get('sort', 'rating2')
        sort_order = request.args.get('order', 'DESC')
        
        # 构建基础查询
        base_query = """
        SELECT 
            username, nickname, platform_level, team_id, map_name, start_time, match_winner,
            kills, deaths, assists, adr, rating, rating2, kast, rws,
            headshot, per_headshot, first_kill, first_death, awp_kill,
            is_mvp, is_svp, is_win, steam_id, match_id,
            vip_fd_ct, vip_fd_t, vip_kast, vip_awp_kill, vip_awp_kill_ct, vip_awp_kill_t,
            vip_damage_stats, vip_damage_receive
        FROM player_match_complete_stats
        WHERE 1=1
        """
        
        params = []
        
        # 添加搜索条件
        if search:
            base_query += " AND (username LIKE %s OR nickname LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        if map_name:
            base_query += " AND map_name = %s"
            params.append(map_name)
        
        if team_id:
            base_query += " AND team_id = %s"
            params.append(int(team_id))
        
        # 添加排序
        valid_sort_fields = ['rating2', 'kills', 'adr', 'kast', 'deaths', 'assists']
        if sort_by in valid_sort_fields:
            base_query += f" ORDER BY {sort_by} {sort_order}"
        else:
            base_query += " ORDER BY rating2 DESC"
        
        # 获取总数（用于分页）
        count_query = """
        SELECT COUNT(*) as total
        FROM player_match_complete_stats
        WHERE 1=1
        """
        
        count_params = []
        
        # 添加相同的搜索条件
        if search:
            count_query += " AND (username LIKE %s OR nickname LIKE %s)"
            search_param = f"%{search}%"
            count_params.extend([search_param, search_param])
        
        if map_name:
            count_query += " AND map_name = %s"
            count_params.append(map_name)
        
        if team_id:
            count_query += " AND team_id = %s"
            count_params.append(int(team_id))
        
        total_result = execute_query(count_query, count_params)
        total_count = total_result[0]['total'] if total_result and len(total_result) > 0 else 0
        
        # 添加分页
        offset = (page - 1) * limit
        base_query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        # 执行查询
        players = execute_query(base_query, params)
        
        if players is None:
            return jsonify({'error': '数据库查询失败'}), 500
        
        # 处理数据格式
        for player in players:
            # 转换布尔值
            for field in ['is_mvp', 'is_svp', 'is_win']:
                if field in player and player[field] is not None:
                    player[field] = bool(player[field])
            
            # 转换数值类型
            for field in ['rating', 'rating2', 'kast', 'per_headshot', 'adr']:
                if field in player and player[field] is not None:
                    player[field] = float(player[field])
        
        return jsonify({
            'data': players,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取玩家数据错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计数据"""
    try:
        # 获取查询参数用于过滤
        search = request.args.get('search', '')
        map_name = request.args.get('map', '')
        team_id = request.args.get('team', '')
        
        # 构建查询条件
        where_conditions = ["1=1"]
        params = []
        
        if search:
            where_conditions.append("(username LIKE %s OR nickname LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        if map_name:
            where_conditions.append("map_name = %s")
            params.append(map_name)
        
        if team_id:
            where_conditions.append("team_id = %s")
            params.append(int(team_id))
        
        where_clause = " AND ".join(where_conditions)
        
        # 统计查询
        stats_query = f"""
        SELECT 
            COUNT(DISTINCT steam_id) as total_players,
            AVG(rating2) as avg_rating,
            AVG(adr) as avg_adr,
            MAX(kills) as max_kills,
            AVG(kast) as avg_kast,
            AVG(per_headshot) as avg_headshot_rate
        FROM player_match_complete_stats
        WHERE {where_clause}
        """
        
        stats = execute_query(stats_query, params)
        
        if not stats:
            return jsonify({'error': '统计数据查询失败'}), 500
        
        result = stats[0]
        
        # 格式化数据
        formatted_stats = {
            'total_players': result['total_players'] or 0,
            'avg_rating': round(float(result['avg_rating'] or 0), 2),
            'avg_adr': round(float(result['avg_adr'] or 0), 1),
            'max_kills': result['max_kills'] or 0,
            'avg_kast': round(float(result['avg_kast'] or 0), 3),
            'avg_headshot_rate': round(float(result['avg_headshot_rate'] or 0), 3)
        }
        
        return jsonify(formatted_stats)
        
    except Exception as e:
        logger.error(f"获取统计数据错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/maps', methods=['GET'])
def get_maps():
    """获取地图列表"""
    try:
        query = "SELECT DISTINCT map_name FROM player_match_complete_stats WHERE map_name IS NOT NULL ORDER BY map_name"
        maps = execute_query(query)
        
        if maps is None:
            return jsonify({'error': '地图数据查询失败'}), 500
        
        map_list = [map_item['map_name'] for map_item in maps]
        return jsonify(map_list)
        
    except Exception as e:
        logger.error(f"获取地图列表错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/players/search', methods=['GET'])
def search_players():
    start_time = time.time()  # 性能监控
    try:
        import urllib.parse

        nickname = request.args.get('nickname', '').strip()
        limit = min(int(request.args.get('limit', 20)), 50)  # 最多返回50个结果（仅用于有搜索词时）

        logger.info(f"玩家搜索请求: nickname='{nickname}', limit={limit}")
        
        # 确保正确解码URL编码的中文字符
        try:
            # 先尝试URL解码
            nickname = urllib.parse.unquote(nickname)
            # 如果是错误的UTF-8解释，尝试重新编码解码
            if '\\x' in repr(nickname):
                nickname = nickname.encode('latin1').decode('utf-8')
        except:
            pass  # 如果解码失败，使用原始字符串
        
        # 当未提供昵称时，返回全部玩家列表（优化性能，使用JOIN避免N+1查询）
        if not nickname:
            # 使用JOIN一次性查询所有必要数据，避免N+1查询问题
            all_players_query = """
            SELECT
                p.uid,
                p.steam_id,
                p.username,
                p.platform_level,
                COUNT(DISTINCT pmcs.match_id) as total_matches
            FROM players p
            LEFT JOIN player_match_complete_stats pmcs ON p.steam_id = pmcs.steam_id
            WHERE p.username IS NOT NULL
            GROUP BY p.uid, p.steam_id, p.username, p.platform_level
            ORDER BY p.platform_level DESC, p.username
            """
            connection = get_database_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(all_players_query)
            players = cursor.fetchall()
            cursor.close()
            connection.close()
        else:
            # 模糊查询玩家 - 使用JOIN优化，避免N+1查询问题
            search_query = """
            SELECT
                p.uid,
                p.steam_id,
                p.username,
                p.platform_level,
                COUNT(DISTINCT pmcs.match_id) as total_matches
            FROM players p
            LEFT JOIN player_match_complete_stats pmcs ON p.steam_id = pmcs.steam_id
            WHERE (p.username LIKE %s OR p.username LIKE %s)
            AND p.username IS NOT NULL
            GROUP BY p.uid, p.steam_id, p.username, p.platform_level
            LIMIT %s
            """

            # 准备两种搜索模式
            search_pattern = f"%{nickname}%"

            # 将中文字符转换为Unicode转义序列（使用正确的格式）
            unicode_escaped = ""
            for char in nickname:
                if ord(char) > 127:
                    unicode_escaped += f"\\u{ord(char):04x}"
                else:
                    unicode_escaped += char
            unicode_pattern = f"%{unicode_escaped}%"

            # 直接使用MySQL连接执行查询
            connection = get_database_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(search_query, (search_pattern, unicode_pattern, limit))
            players = cursor.fetchall()
            cursor.close()
            connection.close()

        if not players:
            return jsonify({
                'players': [],
                'total': 0,
                'message': '未找到匹配的玩家'
            })
        
        # 直接格式化返回数据，已经通过JOIN获得total_matches
        formatted_players = []
        for player in players:
            formatted_players.append({
                'uid': player['uid'],
                'steam_id': player['steam_id'],
                'username': player['username'],
                'platform_level': player.get('platform_level') or 0,
                'total_matches': player.get('total_matches') or 0  # 从JOIN结果中获取
            })
        
        # 性能监控
        elapsed_time = time.time() - start_time
        logger.info(f"玩家搜索完成: 返回{len(formatted_players)}个结果, 耗时{elapsed_time:.2f}秒")

        return jsonify({
            'players': formatted_players,
            'total': len(formatted_players),
            'search_term': nickname
        })

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"搜索玩家错误: {e}, 耗时{elapsed_time:.2f}秒")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/player/<steam_id>', methods=['GET'])
def get_player_detail(steam_id):
    """获取单个玩家详细信息"""
    try:
        query = """
        SELECT *
        FROM player_match_complete_stats
        WHERE steam_id = %s
        """
        
        player = execute_query(query, (steam_id,))
        
        if not player:
            return jsonify({'error': '玩家不存在'}), 404
        
        player_data = player[0]
        
        # 处理数据格式
        for field in ['is_mvp', 'is_svp', 'is_win']:
            if field in player_data and player_data[field] is not None:
                player_data[field] = bool(player_data[field])
        
        for field in ['rating', 'rating2', 'kast', 'per_headshot', 'adr']:
            if field in player_data and player_data[field] is not None:
                player_data[field] = float(player_data[field])
        
        return jsonify(player_data)
        
    except Exception as e:
        logger.error(f"获取玩家详情错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/player/<steam_id>/stats', methods=['GET'])
def get_player_stats(steam_id):
    """获取单个玩家的历史比赛数据聚合统计"""
    try:
        # 获取玩家基本信息
        player_info_query = """
        SELECT DISTINCT p.username, p.nickname, p.platform_level
        FROM players p
        WHERE p.steam_id = %s
        LIMIT 1
        """
        player_info = execute_query(player_info_query, (steam_id,))
        
        if not player_info:
            return jsonify({'error': '玩家不存在'}), 404
        
        # 获取玩家历史比赛统计数据
        stats_query = """
        SELECT 
            COUNT(*) as total_matches,
            SUM(CASE WHEN match_winner = 0 THEN 0 WHEN team_id = match_winner THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN match_winner = 0 THEN 0 WHEN team_id != match_winner THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN match_winner = 0 THEN 1 ELSE 0 END) as ties,
            
            -- 基础数据统计
            SUM(kills) as total_kills,
            SUM(deaths) as total_deaths,
            SUM(assists) as total_assists,
            AVG(adr) as avg_adr,
            AVG(rating) as avg_rating,
            AVG(rating2) as avg_rating2,
            AVG(kast) as avg_kast,
            AVG(per_headshot) as avg_headshot_rate,
            
            -- 击杀分布
            SUM(kill_1) as total_1k,
            SUM(kill_2) as total_2k,
            SUM(kill_3) as total_3k,
            SUM(kill_4) as total_4k,
            SUM(kill_5) as total_5k,
            SUM(headshot) as total_headshots,
            
            -- AWP数据
            SUM(awp_kill) as total_awp_kills,
            SUM(awp_kill_ct) as total_awp_kills_ct,
            SUM(awp_kill_t) as total_awp_kills_t,
            
            -- 首杀数据
            SUM(first_kill) as total_first_kills,
            SUM(first_death) as total_first_deaths,
            
            -- 残局数据
            SUM(end_1v1) as total_1v1,
            SUM(end_1v2) as total_1v2,
            SUM(end_1v3) as total_1v3,
            SUM(end_1v4) as total_1v4,
            SUM(end_1v5) as total_1v5,
            
            -- 荣誉统计
            SUM(CASE WHEN is_mvp = 1 THEN 1 ELSE 0 END) as mvp_count,
            SUM(CASE WHEN is_svp = 1 THEN 1 ELSE 0 END) as svp_count,
            
            -- ELO变化
            AVG(origin_elo) as avg_elo,
            SUM(change_elo) as total_elo_change,
            MAX(origin_elo) as max_elo,
            MIN(origin_elo) as min_elo
            
        FROM player_match_complete_stats
        WHERE steam_id = %s
        """
        
        stats_result = execute_query(stats_query, (steam_id,))
        
        if not stats_result or not stats_result[0]:
            return jsonify({'error': '未找到玩家比赛数据'}), 404
        
        stats = stats_result[0]
        player_info_data = player_info[0]
        
        # 计算衍生统计数据
        total_matches = stats['total_matches'] or 0
        wins = stats['wins'] or 0
        losses = stats['losses'] or 0
        ties = stats['ties'] or 0
        total_kills = stats['total_kills'] or 0
        total_deaths = stats['total_deaths'] or 0
        total_assists = stats['total_assists'] or 0
        
        # 计算胜率
        win_rate = (wins / total_matches * 100) if total_matches > 0 else 0
        
        # 计算KD比
        kd_ratio = (total_kills / total_deaths) if total_deaths > 0 else total_kills
        
        # 计算KDA比
        kda_ratio = ((total_kills + total_assists) / total_deaths) if total_deaths > 0 else (total_kills + total_assists)
        
        # 计算首杀成功率
        first_kill_rate = (stats['total_first_kills'] / (stats['total_first_kills'] + stats['total_first_deaths']) * 100) if (stats['total_first_kills'] + stats['total_first_deaths']) > 0 else 0
        
        # 构建返回数据
        result = {
            'player_info': {
                'steam_id': steam_id,
                'username': player_info_data['username'],
                'nickname': player_info_data['nickname'],
                'platform_level': player_info_data['platform_level']
            },
            'match_summary': {
                'total_matches': total_matches,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_rate': round(win_rate, 2)
            },
            'performance_stats': {
                'kd_ratio': round(kd_ratio, 2),
                'kda_ratio': round(kda_ratio, 2),
                'avg_adr': round(float(stats['avg_adr'] or 0), 2),
                'avg_rating': round(float(stats['avg_rating'] or 0), 3),
                'avg_rating2': round(float(stats['avg_rating2'] or 0), 3),
                'avg_kast': round(float(stats['avg_kast'] or 0), 3),
                'avg_headshot_rate': round(float(stats['avg_headshot_rate'] or 0), 3)
            },
            'combat_stats': {
                'total_kills': total_kills,
                'total_deaths': total_deaths,
                'total_assists': total_assists,
                'total_headshots': stats['total_headshots'] or 0,
                'first_kill_rate': round(first_kill_rate, 2),
                'total_first_kills': stats['total_first_kills'] or 0,
                'total_first_deaths': stats['total_first_deaths'] or 0
            },
            'multikill_stats': {
                'total_1k': stats['total_1k'] or 0,
                'total_2k': stats['total_2k'] or 0,
                'total_3k': stats['total_3k'] or 0,
                'total_4k': stats['total_4k'] or 0,
                'total_5k': stats['total_5k'] or 0
            },
            'awp_stats': {
                'total_awp_kills': stats['total_awp_kills'] or 0,
                'awp_kills_ct': stats['total_awp_kills_ct'] or 0,
                'awp_kills_t': stats['total_awp_kills_t'] or 0
            },
            'clutch_stats': {
                'total_1v1': stats['total_1v1'] or 0,
                'total_1v2': stats['total_1v2'] or 0,
                'total_1v3': stats['total_1v3'] or 0,
                'total_1v4': stats['total_1v4'] or 0,
                'total_1v5': stats['total_1v5'] or 0
            },
            'honors': {
                'mvp_count': stats['mvp_count'] or 0,
                'svp_count': stats['svp_count'] or 0
            },
            'elo_stats': {
                'avg_elo': round(float(stats['avg_elo'] or 0), 2),
                'total_elo_change': round(float(stats['total_elo_change'] or 0), 2),
                'max_elo': round(float(stats['max_elo'] or 0), 2),
                'min_elo': round(float(stats['min_elo'] or 0), 2)
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"获取玩家统计数据错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/player/<steam_id>/map-stats', methods=['GET'])
def get_player_map_stats(steam_id):
    """获取单个玩家的地图表现统计"""
    try:
        query = """
        SELECT 
            map_name,
            COUNT(*) as matches_played,
            SUM(CASE WHEN match_winner = 0 THEN 0 WHEN team_id = match_winner THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN match_winner = 0 THEN 0 WHEN team_id != match_winner THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN match_winner = 0 THEN 1 ELSE 0 END) as ties,
            
            -- 平均表现数据
            AVG(kills) as avg_kills,
            AVG(deaths) as avg_deaths,
            AVG(assists) as avg_assists,
            AVG(adr) as avg_adr,
            AVG(rating) as avg_rating,
            AVG(rating2) as avg_rating2,
            AVG(kast) as avg_kast,
            AVG(per_headshot) as avg_headshot_rate,
            
            -- 总计数据
            SUM(kills) as total_kills,
            SUM(deaths) as total_deaths,
            SUM(assists) as total_assists,
            SUM(headshot) as total_headshots,
            SUM(awp_kill) as total_awp_kills,
            SUM(first_kill) as total_first_kills,
            SUM(first_death) as total_first_deaths,
            
            -- 荣誉统计
            SUM(CASE WHEN is_mvp = 1 THEN 1 ELSE 0 END) as mvp_count,
            SUM(CASE WHEN is_svp = 1 THEN 1 ELSE 0 END) as svp_count
            
        FROM player_match_complete_stats
        WHERE steam_id = %s
        GROUP BY map_name
        ORDER BY matches_played DESC, wins DESC
        """
        
        map_stats = execute_query(query, (steam_id,))
        
        if not map_stats:
            return jsonify({'error': '未找到玩家地图数据'}), 404
        
        # 处理地图统计数据
        result = []
        for map_data in map_stats:
            matches_played = map_data['matches_played']
            wins = map_data['wins']
            losses = map_data['losses']
            ties = map_data['ties']
            total_kills = map_data['total_kills']
            total_deaths = map_data['total_deaths']
            total_assists = map_data['total_assists']
            
            # 计算胜率
            win_rate = (wins / matches_played * 100) if matches_played > 0 else 0
            
            # 计算KD比
            kd_ratio = (total_kills / total_deaths) if total_deaths > 0 else total_kills
            
            # 计算KDA比
            kda_ratio = ((total_kills + total_assists) / total_deaths) if total_deaths > 0 else (total_kills + total_assists)
            
            # 计算首杀成功率
            first_kill_rate = (map_data['total_first_kills'] / (map_data['total_first_kills'] + map_data['total_first_deaths']) * 100) if (map_data['total_first_kills'] + map_data['total_first_deaths']) > 0 else 0
            
            map_stat = {
                'map_name': map_data['map_name'],
                'matches_played': matches_played,
                'wins': wins,
                'losses': losses,
                'ties': ties,
                'win_rate': round(win_rate, 2),
                'kd_ratio': round(kd_ratio, 2),
                'kda_ratio': round(kda_ratio, 2),
                'avg_kills': round(float(map_data['avg_kills']), 2),
                'avg_deaths': round(float(map_data['avg_deaths']), 2),
                'avg_assists': round(float(map_data['avg_assists']), 2),
                'avg_adr': round(float(map_data['avg_adr'] or 0), 2),
                'avg_rating': round(float(map_data['avg_rating'] or 0), 3),
                'avg_rating2': round(float(map_data['avg_rating2'] or 0), 3),
                'avg_kast': round(float(map_data['avg_kast'] or 0), 3),
                'avg_headshot_rate': round(float(map_data['avg_headshot_rate'] or 0), 3),
                'total_headshots': map_data['total_headshots'],
                'total_awp_kills': map_data['total_awp_kills'],
                'first_kill_rate': round(first_kill_rate, 2),
                'mvp_count': map_data['mvp_count'],
                'svp_count': map_data['svp_count']
            }
            result.append(map_stat)
        
        return jsonify({
            'steam_id': steam_id,
            'map_stats': result
        })
        
    except Exception as e:
        logger.error(f"获取玩家地图统计错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/player/<steam_id>/recent-matches', methods=['GET'])
def get_player_recent_matches(steam_id):
    """获取单个玩家的最近比赛记录"""
    try:
        limit = int(request.args.get('limit', 20))
        page = int(request.args.get('page', 1))
        offset = (page - 1) * limit
        
        query = """
        SELECT 
            match_id,
            map_name,
            start_time,
            kills,
            deaths,
            assists,
            adr,
            rating,
            rating2,
            kast,
            per_headshot,
            is_win,
            is_tie,
            is_mvp,
            is_svp,
            change_elo,
            origin_elo,
            team_id,
            match_winner
        FROM player_match_complete_stats
        WHERE steam_id = %s
        ORDER BY start_time DESC
        LIMIT %s OFFSET %s
        """
        
        recent_matches = execute_query(query, (steam_id, limit, offset))
        
        if not recent_matches:
            return jsonify({'error': '未找到玩家比赛记录'}), 404
        
        # 获取总记录数
        count_query = """
        SELECT COUNT(*) as total
        FROM player_match_complete_stats
        WHERE steam_id = %s
        """
        count_result = execute_query(count_query, (steam_id,))
        total_matches = count_result[0]['total'] if count_result else 0
        
        # 处理比赛数据
        matches = []
        for match in recent_matches:
            # 计算KD比
            kd_ratio = (match['kills'] / match['deaths']) if match['deaths'] > 0 else match['kills']
            
            # 判断比赛结果 - 根据team_id和match_winner来判断
            if match['match_winner'] == 0:  # 平局
                match_result = 'tie'
            elif match['team_id'] == match['match_winner']:  # 玩家所在队伍获胜
                match_result = 'win'
            else:  # 玩家所在队伍失败
                match_result = 'loss'
            
            match_data = {
                'match_id': match['match_id'],
                'map_name': match['map_name'],
                'start_time': match['start_time'],
                'kills': match['kills'],
                'deaths': match['deaths'],
                'assists': match['assists'],
                'kd_ratio': round(kd_ratio, 2),
                'adr': round(float(match['adr'] or 0), 2),
                'rating': round(float(match['rating'] or 0), 3),
                'rating2': round(float(match['rating2'] or 0), 3),
                'kast': round(float(match['kast'] or 0), 3),
                'headshot_rate': round(float(match['per_headshot'] or 0), 3),
                'match_result': match_result,
                'is_mvp': bool(match['is_mvp']),
                'is_svp': bool(match['is_svp']),
                'elo_change': round(float(match['change_elo'] or 0), 2),
                'elo_before': round(float(match['origin_elo'] or 0), 2),
                'team_id': match['team_id'],
                'match_winner': match['match_winner']
            }
            matches.append(match_data)
        
        return jsonify({
            'steam_id': steam_id,
            'matches': matches,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_matches,
                'pages': (total_matches + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取玩家最近比赛错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/matches', methods=['GET'])
def get_matches():
    """获取比赛列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '').strip()
        map_name = request.args.get('map_name', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()
        sort = request.args.get('sort', 'start_time')
        order = request.args.get('order', 'DESC')
        
        # 验证排序字段
        valid_sort_fields = ['start_time', 'map_name', 'player_count']
        if sort not in valid_sort_fields:
            sort = 'start_time'
        
        # 验证排序方向
        if order.upper() not in ['ASC', 'DESC']:
            order = 'DESC'
        
        # 构建查询条件
        where_conditions = ["1=1"]
        params = []
        
        if search:
            where_conditions.append("(map_name LIKE %s)")
            search_param = f"%{search}%"
            params.append(search_param)
        
        if map_name:
            where_conditions.append("map_name = %s")
            params.append(map_name)
        
        if start_date:
            # 将日期字符串转换为Unix时间戳
            try:
                start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                where_conditions.append("start_time >= %s")
                params.append(start_timestamp)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        
        if end_date:
            # 将日期字符串转换为Unix时间戳（结束日期设为当天23:59:59）
            try:
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                end_timestamp = int(end_datetime.timestamp())
                where_conditions.append("start_time <= %s")
                params.append(end_timestamp)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        
        where_clause = " AND ".join(where_conditions)
        
        # 获取比赛列表（按match_id分组）
        matches_query = f"""
        SELECT 
            match_id,
            map_name,
            start_time,
            match_winner,
            COUNT(*) as player_count,
            AVG(rating2) as avg_rating,
            MAX(kills) as max_kills
        FROM player_match_complete_stats
        WHERE {where_clause}
        GROUP BY match_id, map_name, start_time, match_winner
        ORDER BY {sort} {order}
        LIMIT %s OFFSET %s
        """
        
        offset = (page - 1) * limit
        params.extend([limit, offset])
        
        matches = execute_query(matches_query, params)
        
        if not matches:
            return jsonify({
                'matches': [],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': 0,
                    'pages': 0
                }
            })
        
        # 获取总数
        count_query = f"""
        SELECT COUNT(DISTINCT match_id) as total
        FROM player_match_complete_stats
        WHERE {where_clause}
        """
        
        count_params = params[:-2]  # 移除limit和offset参数
        total_result = execute_query(count_query, count_params)
        total_count = total_result[0]['total'] if total_result and len(total_result) > 0 else 0
        
        # 处理数据格式
        for match in matches:
            if match['avg_rating'] is not None:
                match['avg_rating'] = round(float(match['avg_rating']), 2)
        
        return jsonify({
            'matches': matches,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取比赛列表错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/match/<match_id>/players', methods=['GET'])
def get_match_players(match_id):
    """获取单场比赛的所有玩家数据"""
    try:
        sort = request.args.get('sort', 'rating2')
        order = request.args.get('order', 'DESC')
        
        # 验证排序字段
        valid_sort_fields = ['username', 'kills', 'deaths', 'assists', 'adr', 'rating2', 'kast', 'rws']
        if sort not in valid_sort_fields:
            sort = 'rating2'
        
        # 验证排序方向
        if order.upper() not in ['ASC', 'DESC']:
            order = 'DESC'
        
        # 获取比赛基本信息
        match_info_query = """
        SELECT DISTINCT match_id, map_name, start_time, match_winner
        FROM player_match_complete_stats
        WHERE match_id = %s
        """
        
        match_info = execute_query(match_info_query, [match_id])
        
        if not match_info:
            return jsonify({'error': '比赛不存在'}), 404
        
        # 获取该比赛的所有玩家数据
        players_query = f"""
        SELECT 
            username, nickname, steam_id, team_id, platform_level,
            kills, deaths, assists, adr, rating, rating2, kast, rws,
            headshot, per_headshot, first_kill, first_death, awp_kill,
            is_mvp, is_svp, is_win,
            vip_fd_ct, vip_fd_t, vip_kast, vip_awp_kill, vip_awp_kill_ct, vip_awp_kill_t,
            vip_damage_stats, vip_damage_receive
        FROM player_match_complete_stats
        WHERE match_id = %s
        ORDER BY {sort} {order}
        """
        
        players = execute_query(players_query, [match_id])
        
        if not players:
            return jsonify({'error': '该比赛没有玩家数据'}), 404
        
        # 处理数据格式
        for player in players:
            # 布尔值字段
            for field in ['is_mvp', 'is_svp', 'is_win']:
                if field in player and player[field] is not None:
                    player[field] = bool(player[field])
            
            # 浮点数字段
            for field in ['rating', 'rating2', 'kast', 'per_headshot', 'adr', 'rws']:
                if field in player and player[field] is not None:
                    player[field] = float(player[field])
        
        return jsonify({
            'match_info': match_info[0],
            'players': players,
            'player_count': len(players)
        })
        
    except Exception as e:
        logger.error(f"获取比赛玩家数据错误: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    """获取全玩家排行榜数据"""
    try:
        # 获取查询参数
        stat_type = request.args.get('stat', 'rating2')  # 排行榜类型
        map_filter = request.args.get('map', '')  # 地图筛选

        # 验证排行榜类型
        valid_stats = {
            'rating2': 'AVG(mps.rating2)',
            'rating': 'AVG(mps.rating)',
            'adr': 'AVG(mps.adr)',
            'kd_ratio': 'SUM(mps.kills) / NULLIF(SUM(mps.deaths), 0)',
            'avg_kills': 'AVG(mps.kills)',
            'avg_assists': 'AVG(mps.assists)',
            'avg_deaths': 'AVG(mps.deaths)',
            'headshot_rate': 'AVG(mps.per_headshot)',
            'avg_first_kill': 'AVG(mps.first_kill)',
            'avg_first_death': 'AVG(mps.first_death)',
            'first_kill_rate': 'SUM(mps.first_kill) / NULLIF(SUM(m.round_total), 0)',
            'first_death_rate': 'SUM(mps.first_death) / NULLIF(SUM(m.round_total), 0)',
            'avg_awp_kills': 'AVG(mps.awp_kill)',
            'mvp_count': 'SUM(CASE WHEN m.mvp_uid = mps.uid THEN 1 ELSE 0 END)',
            'win_rate': 'SUM(CASE WHEN m.match_winner = mps.team_id AND m.match_winner != 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT mps.match_id), 0)',
            'kast': 'AVG(mps.kast)',
            'rws': 'AVG(mps.rws)'
        }

        if stat_type not in valid_stats:
            return jsonify({'error': '无效的排行榜类型'}), 400

        # 构建基础查询
        base_query = f"""
        SELECT
            p.username,
            p.nickname,
            p.platform_level,
            p.steam_id,
            COUNT(DISTINCT mps.match_id) as total_matches,
            {valid_stats[stat_type]} as stat_value,
            AVG(mps.rating2) as avg_rating2,
            AVG(mps.rating) as avg_rating,
            AVG(mps.adr) as avg_adr,
            SUM(mps.kills) / NULLIF(SUM(mps.deaths), 0) as kd_ratio,
            AVG(mps.kills) as avg_kills,
            AVG(mps.deaths) as avg_deaths,
            AVG(mps.assists) as avg_assists,
            AVG(mps.per_headshot) as avg_headshot_rate,
            AVG(mps.first_kill) as avg_first_kill,
            AVG(mps.first_death) as avg_first_death,
            SUM(mps.first_kill) / NULLIF(SUM(m.round_total), 0) as first_kill_rate,
            SUM(mps.first_death) / NULLIF(SUM(m.round_total), 0) as first_death_rate,
            AVG(mps.awp_kill) as avg_awp_kills,
            SUM(CASE WHEN m.mvp_uid = mps.uid THEN 1 ELSE 0 END) as mvp_count,
            SUM(CASE WHEN m.match_winner = mps.team_id AND m.match_winner != 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT mps.match_id), 0) as win_rate,
            AVG(mps.kast) as avg_kast,
            AVG(mps.rws) as avg_rws,
            MAX(m.start_time) as last_match_time
        FROM match_player_stats mps
        JOIN players p ON mps.uid = p.uid
        JOIN matches m ON mps.match_id = m.match_id
        WHERE 1=1
        """

        params = []

        # 添加筛选条件
        if map_filter:
            base_query += " AND m.map_name = %s"
            params.append(map_filter)

        # 分组和排序 - 使用原始统计表达式而不是别名，以避免NULL值排序问题
        # MySQL不支持NULLS LAST，使用COALESCE来处理NULL值
        base_query += f"""
        GROUP BY p.uid, p.username, p.nickname, p.platform_level, p.steam_id
        ORDER BY COALESCE({valid_stats[stat_type]}, 0) DESC
        """

        # 执行查询
        result = execute_query(base_query, params)

        if result is None:
            return jsonify({'error': '数据库查询失败'}), 500

        # 格式化结果
        leaderboard_data = []
        for i, row in enumerate(result):
            player_data = {
                'rank': i + 1,
                'username': row['username'],
                'nickname': row['nickname'],
                'platform_level': row['platform_level'],
                'steam_id': row['steam_id'],
                'total_matches': row['total_matches'],
                'stat_value': round(float(row['stat_value']) if row['stat_value'] is not None else 0, 3),
                'stats': {
                    'avg_rating2': round(float(row['avg_rating2']) if row['avg_rating2'] is not None else 0, 3),
                    'avg_rating': round(float(row['avg_rating']) if row['avg_rating'] is not None else 0, 3),
                    'avg_adr': round(float(row['avg_adr']) if row['avg_adr'] is not None else 0, 2),
                    'kd_ratio': round(float(row['kd_ratio']) if row['kd_ratio'] is not None else 0, 2),
                    'avg_kills': round(float(row['avg_kills']) if row['avg_kills'] is not None else 0, 2),
                    'avg_deaths': round(float(row['avg_deaths']) if row['avg_deaths'] is not None else 0, 2),
                    'avg_assists': round(float(row['avg_assists']) if row['avg_assists'] is not None else 0, 2),
                    'avg_headshot_rate': round(float(row['avg_headshot_rate']) if row['avg_headshot_rate'] is not None else 0, 3),
                    'avg_first_kill': round(float(row['avg_first_kill']) if row['avg_first_kill'] is not None else 0, 2),
                    'avg_first_death': round(float(row['avg_first_death']) if row['avg_first_death'] is not None else 0, 2),
                    'first_kill_rate': round(float(row['first_kill_rate']) if row['first_kill_rate'] is not None else 0, 3),
                    'first_death_rate': round(float(row['first_death_rate']) if row['first_death_rate'] is not None else 0, 3),
                    'avg_awp_kills': round(float(row['avg_awp_kills']) if row['avg_awp_kills'] is not None else 0, 2),
                    'mvp_count': row['mvp_count'] or 0,
                    'win_rate': round(float(row['win_rate']) if row['win_rate'] is not None else 0, 3),
                    'avg_kast': round(float(row['avg_kast']) if row['avg_kast'] is not None else 0, 3),
                    'avg_rws': round(float(row['avg_rws']) if row['avg_rws'] is not None else 0, 2)
                },
                'last_match_time': row['last_match_time']
            }
            leaderboard_data.append(player_data)

        return jsonify({
            'success': True,
            'data': leaderboard_data,
            'meta': {
                'stat_type': stat_type,
                'total_players': len(leaderboard_data),
                'map_filter': map_filter
            }
        })

    except Exception as e:
        logger.error(f"获取排行榜数据失败: {e}")
        return jsonify({'error': f'获取排行榜数据失败: {str(e)}'}), 500

@app.route('/api/leaderboard/stats-types', methods=['GET'])
def get_leaderboard_stats_types():
    """获取可用的排行榜统计类型"""
    stats_types = [
        {'key': 'rating2', 'name': 'Rating 2.0', 'description': '平均Rating 2.0评分'},
        {'key': 'rating', 'name': 'Rating', 'description': '平均Rating评分'},
        {'key': 'adr', 'name': 'ADR', 'description': '平均每回合伤害'},
        {'key': 'kd_ratio', 'name': 'K/D比', 'description': '击杀死亡比'},
        {'key': 'avg_kills', 'name': '场均击杀', 'description': '平均每场击杀数'},
        {'key': 'avg_assists', 'name': '场均助攻', 'description': '平均每场助攻数'},
        {'key': 'avg_deaths', 'name': '场均死亡', 'description': '平均每场死亡数'},
        {'key': 'headshot_rate', 'name': '爆头率', 'description': '平均爆头率'},
        {'key': 'avg_first_kill', 'name': '场均首杀', 'description': '平均每场首杀数'},
        {'key': 'avg_first_death', 'name': '场均首死', 'description': '平均每场首死数'},
        {'key': 'first_kill_rate', 'name': '首杀率', 'description': '首杀率（首杀数/总回合数）'},
        {'key': 'first_death_rate', 'name': '首死率', 'description': '首死率（首死数/总回合数）'},
        {'key': 'avg_awp_kills', 'name': '场均AWP击杀', 'description': '平均每场AWP击杀数'},
        {'key': 'mvp_count', 'name': 'MVP次数', 'description': 'MVP获得次数'},
        {'key': 'win_rate', 'name': '胜率', 'description': '比赛胜率'},
        {'key': 'kast', 'name': 'KAST', 'description': '平均KAST评分'},
        {'key': 'rws', 'name': 'RWS', 'description': '平均RWS评分'}
    ]
    
    return jsonify({
        'success': True,
        'data': stats_types
    })

@app.route('/api/leaderboard/filters', methods=['GET'])
def get_leaderboard_filters():
    """获取排行榜筛选选项"""
    try:
        # 获取可用地图
        maps_query = "SELECT DISTINCT map_name FROM matches ORDER BY map_name"
        maps_result = execute_query(maps_query)
        
        # 获取可用赛季
        seasons_query = "SELECT DISTINCT season FROM match_player_stats WHERE season IS NOT NULL ORDER BY season DESC"
        seasons_result = execute_query(seasons_query)
        
        return jsonify({
            'success': True,
            'data': {
                'maps': [row['map_name'] for row in maps_result] if maps_result else [],
                'seasons': [row['season'] for row in seasons_result] if seasons_result else []
            }
        })
        
    except Exception as e:
        logger.error(f"获取筛选选项失败: {e}")
        return jsonify({'error': f'获取筛选选项失败: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        # 测试数据库连接
        conn = get_database_connection()
        if conn:
            conn.close()
            return jsonify({
                'status': 'healthy',
                'message': 'API服务器运行正常',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'message': '数据库连接失败'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': f'健康检查失败: {str(e)}'
        }), 500

@app.route('/')
def index():
    """主页重定向到比赛仪表板"""
    return send_from_directory('.', 'matches_dashboard.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """提供静态文件服务"""
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        return jsonify({'error': f'文件未找到: {filename}'}), 404

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': '服务器内部错误'}), 500

# ========================================
# 自定义比赛模块API接口
# ========================================

import time
import re
from datetime import datetime

def validate_tournament_data(data):
    """验证比赛数据"""
    errors = []

    # 比赛名称验证
    name = data.get('name', '').strip()
    if not name:
        errors.append('比赛名称不能为空')
    elif len(name) > 100:
        errors.append('比赛名称过长（最多100字符）')
    elif re.search(r'[<>\'"&]', name):
        errors.append('比赛名称包含非法字符')

    # 时间验证
    start_time = data.get('start_time')
    end_time = data.get('end_time')

    if start_time is None:
        errors.append('缺少开始时间')
    elif not isinstance(start_time, (int, float)) or start_time <= 0:
        errors.append('开始时间格式无效')

    if end_time is None:
        errors.append('缺少结束时间')
    elif not isinstance(end_time, (int, float)) or end_time <= 0:
        errors.append('结束时间格式无效')

    if start_time and end_time:
        if start_time >= end_time:
            errors.append('开始时间必须早于结束时间')
        # 检查开始时间不能早于当前时间超过24小时（允许创建过去的比赛用于测试）
        if start_time < time.time() - 86400:
            errors.append('开始时间不能早于24小时前')

    # 创建者验证
    creator_uid = data.get('creator_uid')
    if creator_uid is None:
        errors.append('缺少创建者UID')
    elif not isinstance(creator_uid, int) or creator_uid <= 0:
        errors.append('无效的创建者UID')

    # 描述验证（可选）
    description = data.get('description', '')
    if description and len(description) > 1000:
        errors.append('比赛描述过长（最多1000字符）')
    elif description and re.search(r'[<>\'"&]', description):
        errors.append('比赛描述包含非法字符')

    return errors

def validate_team_data(team_data, tournament_id):
    """验证队伍数据"""
    errors = []

    if not isinstance(team_data, dict):
        errors.append('队伍数据格式无效')
        return errors

    # 队伍名称验证
    team_name = team_data.get('team_name', '').strip()
    if not team_name:
        errors.append('队伍名称不能为空')
    elif len(team_name) > 50:
        errors.append('队伍名称过长（最多50字符）')
    elif re.search(r'[<>\'"&]', team_name):
        errors.append('队伍名称包含非法字符')

    # 队员UID列表验证
    player_uids = team_data.get('player_uids', [])
    if not isinstance(player_uids, list):
        errors.append('队员列表格式无效')
    else:
        # 检查UID格式
        invalid_uids = [uid for uid in player_uids if not isinstance(uid, int) or uid <= 0]
        if invalid_uids:
            errors.append(f'发现无效的队员UID: {invalid_uids}')

        # 检查重复
        if len(player_uids) != len(set(player_uids)):
            errors.append('队员列表中存在重复的UID')

    # 队长验证（可选）
    captain_uid = team_data.get('captain_uid')
    if captain_uid is not None:
        if not isinstance(captain_uid, int) or captain_uid <= 0:
            errors.append('无效的队长UID')
        elif player_uids and captain_uid not in player_uids:
            errors.append('队长必须在队员列表中')

    return errors

def execute_insert_query(query, params=None):
    """执行插入查询并返回插入的ID"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        return cursor.lastrowid
    except Error as e:
        logger.error(f"插入查询执行错误: {e}")
        connection.rollback()
        return None
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def execute_update_query(query, params=None):
    """执行更新查询"""
    connection = get_database_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        cursor.execute(query, params or ())
        connection.commit()
        return True
    except Error as e:
        logger.error(f"更新查询执行错误: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/custom-tournaments', methods=['GET'])
def get_custom_tournaments():
    """获取自定义比赛列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        status = request.args.get('status', '')
        search = request.args.get('search', '')
        
        # 构建查询
        base_query = """
        SELECT * FROM custom_tournament_complete_view
        WHERE 1=1
        """
        params = []
        
        if status:
            base_query += " AND status = %s"
            params.append(status)
        
        if search:
            base_query += " AND name LIKE %s"
            params.append(f"%{search}%")
        
        # 添加排序和分页
        base_query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, (page - 1) * limit])
        
        tournaments = execute_query(base_query, params)
        
        # 获取总数
        count_query = """
        SELECT COUNT(*) as total FROM custom_tournaments
        WHERE 1=1
        """
        count_params = []
        
        if status:
            count_query += " AND status = %s"
            count_params.append(status)
        
        if search:
            count_query += " AND name LIKE %s"
            count_params.append(f"%{search}%")
        
        total_result = execute_query(count_query, count_params)
        total = total_result[0]['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'data': tournaments or [],
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取自定义比赛列表错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments', methods=['POST'])
def create_custom_tournament():
    """创建自定义比赛"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': '请求数据不能为空'}), 400

        # 使用增强的数据验证
        validation_errors = validate_tournament_data(data)
        if validation_errors:
            return jsonify({'success': False, 'error': '; '.join(validation_errors)}), 400

        # 校验创建者是否存在于 players 表
        try:
            creator_check = execute_query("SELECT uid FROM players WHERE uid = %s", [data['creator_uid']])
            if not creator_check:
                return jsonify({'success': False, 'error': '创建者不存在，请选择有效玩家UID'}), 400
        except Exception as e:
            logger.error(f"校验创建者失败: {e}")
            return jsonify({'success': False, 'error': '创建者校验失败'}), 500

        # 插入自定义比赛
        tournament_query = """
        INSERT INTO custom_tournaments (name, description, start_time, end_time, creator_uid)
        VALUES (%s, %s, %s, %s, %s)
        """
        tournament_params = [
            data['name'],
            data.get('description', ''),
            data['start_time'],
            data['end_time'],
            data['creator_uid']
        ]
        
        tournament_id = execute_insert_query(tournament_query, tournament_params)
        
        if not tournament_id:
            return jsonify({'success': False, 'error': '创建比赛失败'}), 500
        
        # 插入队伍信息（如果提供了teams）
        teams_data = data.get('teams')
        if isinstance(teams_data, list) and len(teams_data) > 0:
            # 验证所有队伍数据
            team_validation_errors = []
            for i, team in enumerate(teams_data):
                errors = validate_team_data(team, tournament_id)
                if errors:
                    team_validation_errors.append(f"队伍{i+1}: {'; '.join(errors)}")

            if team_validation_errors:
                return jsonify({'success': False, 'error': '; '.join(team_validation_errors)}), 400

            # 创建队伍
            for team in teams_data:
                team_query = """
                INSERT INTO custom_tournament_teams (tournament_id, team_name, player_uids, captain_uid)
                VALUES (%s, %s, %s, %s)
                """
                team_params = [
                    tournament_id,
                    team.get('team_name', '').strip(),
                    json.dumps(team.get('player_uids', [])),
                    team.get('captain_uid')
                ]

                team_id = execute_insert_query(team_query, team_params)
                if not team_id:
                    logger.warning(f"创建队伍失败: {team.get('team_name', '')}")
        
        return jsonify({
            'success': True,
            'data': {'tournament_id': tournament_id},
            'message': '自定义比赛创建成功'
        })
        
    except Exception as e:
        logger.error(f"创建自定义比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>', methods=['GET'])
def get_custom_tournament_detail(tournament_id):
    """获取自定义比赛详情"""
    try:
        # 获取比赛基本信息
        tournament_query = """
        SELECT * FROM custom_tournament_complete_view WHERE id = %s
        """
        tournament = execute_query(tournament_query, [tournament_id])
        
        if not tournament:
            return jsonify({'success': False, 'error': '比赛不存在'}), 404
        
        # 获取队伍信息
        teams_query = """
        SELECT * FROM custom_tournament_team_details WHERE tournament_id = %s
        """
        teams = execute_query(teams_query, [tournament_id])
        
        # 获取关联的比赛
        matches_query = """
        SELECT 
            ctm.*,
            m.map_name,
            m.start_time as match_start_time,
            m.group1_all_score,
            m.group2_all_score,
            m.match_winner as original_winner,
            t1.team_name as team1_name,
            t2.team_name as team2_name
        FROM custom_tournament_matches ctm
        LEFT JOIN matches m ON ctm.match_id = m.match_id
        LEFT JOIN custom_tournament_teams t1 ON ctm.team1_id = t1.id
        LEFT JOIN custom_tournament_teams t2 ON ctm.team2_id = t2.id
        WHERE ctm.tournament_id = %s
        ORDER BY ctm.match_order, ctm.created_at
        """
        matches = execute_query(matches_query, [tournament_id])
        
        # 解析队伍的player_uids JSON字段
        for team in teams or []:
            if team['player_uids']:
                try:
                    team['player_uids'] = json.loads(team['player_uids'])
                except:
                    team['player_uids'] = []
        
        tournament_data = tournament[0]
        tournament_data['teams'] = teams or []
        tournament_data['matches'] = matches or []
        
        return jsonify({
            'success': True,
            'data': tournament_data
        })
        
    except Exception as e:
        logger.error(f"获取自定义比赛详情错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>', methods=['PUT'])
def update_custom_tournament(tournament_id):
    """更新自定义比赛"""
    try:
        data = request.get_json()
        
        # 更新比赛基本信息
        update_query = """
        UPDATE custom_tournaments 
        SET name = %s, description = %s, start_time = %s, end_time = %s, status = %s
        WHERE id = %s
        """
        update_params = [
            data.get('name'),
            data.get('description', ''),
            data.get('start_time'),
            data.get('end_time'),
            data.get('status', 'draft'),
            tournament_id
        ]
        
        success = execute_update_query(update_query, update_params)
        
        if not success:
            return jsonify({'success': False, 'error': '更新比赛失败'}), 500
        
        return jsonify({
            'success': True,
            'message': '比赛更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新自定义比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>/teams/<int:team_id>', methods=['PUT'])
def update_custom_tournament_team(tournament_id, team_id):
    """更新自定义比赛中的队伍信息（队名、队员UID、队长UID）"""
    try:
        data = request.get_json() or {}

        # 校验队伍存在且属于该比赛
        team_check_query = "SELECT id, tournament_id FROM custom_tournament_teams WHERE id = %s"
        team_record = execute_query(team_check_query, [team_id])
        if not team_record:
            return jsonify({'success': False, 'error': '队伍不存在'}), 404
        if team_record[0]['tournament_id'] != tournament_id:
            return jsonify({'success': False, 'error': '队伍不属于该比赛'}), 400

        # 组装更新字段
        set_clauses = []
        params = []

        if 'team_name' in data:
            team_name = (data.get('team_name') or '').strip()
            if not team_name:
                return jsonify({'success': False, 'error': '队伍名称不能为空'}), 400
            set_clauses.append('team_name = %s')
            params.append(team_name)

        if 'player_uids' in data:
            player_uids = data.get('player_uids')
            if not isinstance(player_uids, list):
                return jsonify({'success': False, 'error': 'player_uids 必须为数组'}), 400
            try:
                player_uids_json = json.dumps(player_uids)
            except Exception:
                return jsonify({'success': False, 'error': 'player_uids 序列化失败'}), 400
            set_clauses.append('player_uids = %s')
            params.append(player_uids_json)

        if 'captain_uid' in data:
            captain_uid = data.get('captain_uid')
            # captain_uid 可以为 None
            set_clauses.append('captain_uid = %s')
            params.append(captain_uid)

        if not set_clauses:
            return jsonify({'success': False, 'error': '未提供可更新的字段'}), 400

        update_query = f"UPDATE custom_tournament_teams SET {', '.join(set_clauses)} WHERE id = %s"
        params.append(team_id)

        success = execute_update_query(update_query, params)
        if not success:
            return jsonify({'success': False, 'error': '更新队伍失败'}), 500

        return jsonify({'success': True, 'message': '队伍更新成功'})

    except Exception as e:
        logger.error(f"更新队伍错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>/teams/<int:team_id>', methods=['DELETE'])
def delete_custom_tournament_team(tournament_id, team_id):
    """删除自定义比赛中的队伍"""
    try:
        # 校验队伍存在且属于该比赛
        team_check_query = "SELECT id, tournament_id FROM custom_tournament_teams WHERE id = %s"
        team_record = execute_query(team_check_query, [team_id])
        if not team_record:
            return jsonify({'success': False, 'error': '队伍不存在'}), 404
        if team_record[0]['tournament_id'] != tournament_id:
            return jsonify({'success': False, 'error': '队伍不属于该比赛'}), 400

        # 删除队伍。外键约束会将相关比赛中的team1_id/team2_id/winner_team_id置为NULL
        delete_query = "DELETE FROM custom_tournament_teams WHERE id = %s AND tournament_id = %s"
        success = execute_update_query(delete_query, [team_id, tournament_id])
        if not success:
            return jsonify({'success': False, 'error': '删除队伍失败'}), 500

        return jsonify({'success': True, 'message': '队伍删除成功'})
    except Exception as e:
        logger.error(f"删除队伍错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>', methods=['DELETE'])
def delete_custom_tournament(tournament_id):
    """删除自定义比赛"""
    try:
        delete_query = "DELETE FROM custom_tournaments WHERE id = %s"
        success = execute_update_query(delete_query, [tournament_id])
        
        if not success:
            return jsonify({'success': False, 'error': '删除比赛失败'}), 500
        
        return jsonify({
            'success': True,
            'message': '比赛删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除自定义比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# =====================
# 自定义比赛统计接口
# =====================
@app.route('/api/custom-tournaments/<int:tournament_id>/stats/teams', methods=['GET'])
def get_custom_tournament_team_stats(tournament_id):
    """获取自定义比赛中队伍的统计（胜率、总击杀、总死亡、总助攻）"""
    try:
        # 统计每个队伍的参赛场次与胜场
        team_match_stats_query = """
        SELECT 
            ctt.id AS team_id,
            ctt.team_name,
            COUNT(ctm.id) AS matches_played,
            SUM(CASE WHEN ctm.winner_team_id = ctt.id THEN 1 ELSE 0 END) AS wins
        FROM custom_tournament_teams ctt
        LEFT JOIN custom_tournament_matches ctm
          ON ctm.tournament_id = ctt.tournament_id 
         AND (ctm.team1_id = ctt.id OR ctm.team2_id = ctt.id)
        WHERE ctt.tournament_id = %s
        GROUP BY ctt.id, ctt.team_name
        """
        team_match_stats = execute_query(team_match_stats_query, [tournament_id]) or []

        # 聚合每个队伍在本比赛范围内的总击杀/死亡/助攻
        team_kda_query = """
        SELECT tm.team_id AS team_id,
               COALESCE(SUM(mps.kills), 0) AS total_kills,
               COALESCE(SUM(mps.deaths), 0) AS total_deaths,
               COALESCE(SUM(mps.assists), 0) AS total_assists
        FROM match_player_stats mps
        JOIN (
            SELECT ctm.match_id AS match_id, 1 AS team_side, ctm.team1_id AS team_id
            FROM custom_tournament_matches ctm
            WHERE ctm.tournament_id = %s AND ctm.team1_id IS NOT NULL
            UNION ALL
            SELECT ctm.match_id AS match_id, 2 AS team_side, ctm.team2_id AS team_id
            FROM custom_tournament_matches ctm
            WHERE ctm.tournament_id = %s AND ctm.team2_id IS NOT NULL
        ) tm ON tm.match_id = mps.match_id AND tm.team_side = mps.team_id
        GROUP BY tm.team_id
        """
        team_kda_stats = execute_query(team_kda_query, [tournament_id, tournament_id]) or []

        kda_map = {row['team_id']: row for row in team_kda_stats}
        result = []
        for row in team_match_stats:
            team_id = row['team_id']
            matches_played = row['matches_played'] or 0
            wins = row['wins'] or 0
            losses = max(matches_played - wins, 0)
            kda = kda_map.get(team_id, {'total_kills': 0, 'total_deaths': 0, 'total_assists': 0})
            win_rate = (wins / matches_played * 100) if matches_played > 0 else 0
            result.append({
                'team_id': team_id,
                'team_name': row['team_name'],
                'matches_played': matches_played,
                'wins': wins,
                'losses': losses,
                'win_rate': round(win_rate, 2),
                'total_kills': int(kda.get('total_kills', 0) or 0),
                'total_deaths': int(kda.get('total_deaths', 0) or 0),
                'total_assists': int(kda.get('total_assists', 0) or 0)
            })

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取自定义比赛队伍统计错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>/leaderboard', methods=['GET'])
def get_custom_tournament_leaderboard(tournament_id):
    """获取限定于自定义比赛范围的玩家排行榜"""
    try:
        # 支持两种参数名：stat 或 stat_type
        stat_type = request.args.get('stat') or request.args.get('stat_type') or 'rating2'
        map_filter = request.args.get('map', '')

        valid_stats = {
            'rating2': 'AVG(mps.rating2)',
            'rating': 'AVG(mps.rating)',
            'adr': 'AVG(mps.adr)',
            'kd_ratio': 'SUM(mps.kills) / NULLIF(SUM(mps.deaths), 0)',
            'avg_kills': 'AVG(mps.kills)',
            'avg_assists': 'AVG(mps.assists)',
            'avg_deaths': 'AVG(mps.deaths)',
            'headshot_rate': 'AVG(mps.per_headshot)',
            'avg_first_kill': 'AVG(mps.first_kill)',
            'avg_first_death': 'AVG(mps.first_death)',
            'first_kill_rate': 'SUM(mps.first_kill) / NULLIF(SUM(m.round_total), 0)',
            'first_death_rate': 'SUM(mps.first_death) / NULLIF(SUM(m.round_total), 0)',
            'avg_awp_kills': 'AVG(mps.awp_kill)',
            'mvp_count': 'SUM(CASE WHEN m.mvp_uid = mps.uid THEN 1 ELSE 0 END)',
            'win_rate': 'SUM(CASE WHEN m.match_winner = mps.team_id AND m.match_winner != 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT mps.match_id), 0)',
            'kast': 'AVG(mps.kast)',
            'rws': 'AVG(mps.rws)'
        }

        if stat_type not in valid_stats:
            return jsonify({'success': False, 'error': '无效的排行榜类型'}), 400

        base_query = f"""
        SELECT
            p.username,
            p.nickname,
            p.platform_level,
            p.steam_id,
            COUNT(DISTINCT mps.match_id) as total_matches,
            {valid_stats[stat_type]} as stat_value,
            AVG(mps.rating2) as avg_rating2,
            AVG(mps.rating) as avg_rating,
            AVG(mps.adr) as avg_adr,
            SUM(mps.kills) / NULLIF(SUM(mps.deaths), 0) as kd_ratio,
            AVG(mps.kills) as avg_kills,
            AVG(mps.deaths) as avg_deaths,
            AVG(mps.assists) as avg_assists,
            AVG(mps.per_headshot) as avg_headshot_rate,
            AVG(mps.first_kill) as avg_first_kill,
            AVG(mps.first_death) as avg_first_death,
            SUM(mps.first_kill) / NULLIF(SUM(m.round_total), 0) as first_kill_rate,
            SUM(mps.first_death) / NULLIF(SUM(m.round_total), 0) as first_death_rate,
            AVG(mps.awp_kill) as avg_awp_kills,
            SUM(CASE WHEN m.mvp_uid = mps.uid THEN 1 ELSE 0 END) as mvp_count,
            SUM(CASE WHEN m.match_winner = mps.team_id AND m.match_winner != 0 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT mps.match_id), 0) as win_rate,
            AVG(mps.kast) as avg_kast,
            AVG(mps.rws) as avg_rws,
            MAX(m.start_time) as last_match_time
        FROM match_player_stats mps
        JOIN players p ON mps.uid = p.uid
        JOIN matches m ON mps.match_id = m.match_id
        JOIN custom_tournament_matches ctm ON ctm.match_id = mps.match_id AND ctm.tournament_id = %s
        WHERE 1=1
        """

        params = [tournament_id]
        if map_filter:
            base_query += " AND m.map_name = %s"
            params.append(map_filter)

        base_query += f"""
        GROUP BY p.uid, p.username, p.nickname, p.platform_level, p.steam_id
        ORDER BY COALESCE({valid_stats[stat_type]}, 0) DESC
        """

        result = execute_query(base_query, params)
        if result is None:
            return jsonify({'success': False, 'error': '数据库查询失败'}), 500

        leaderboard_data = []
        for i, row in enumerate(result):
            player_data = {
                'rank': i + 1,
                'username': row.get('username'),
                'nickname': row.get('nickname'),
                'platform_level': row.get('platform_level'),
                'steam_id': row.get('steam_id'),
                'total_matches': row.get('total_matches'),
                'stat_value': round(float(row['stat_value']) if row['stat_value'] is not None else 0, 3),
                'stats': {
                    'avg_rating2': round(float(row['avg_rating2']) if row['avg_rating2'] is not None else 0, 3),
                    'avg_rating': round(float(row['avg_rating']) if row['avg_rating'] is not None else 0, 3),
                    'avg_adr': round(float(row['avg_adr']) if row['avg_adr'] is not None else 0, 2),
                    'kd_ratio': round(float(row['kd_ratio']) if row['kd_ratio'] is not None else 0, 2),
                    'avg_kills': round(float(row['avg_kills']) if row['avg_kills'] is not None else 0, 2),
                    'avg_deaths': round(float(row['avg_deaths']) if row['avg_deaths'] is not None else 0, 2),
                    'avg_assists': round(float(row['avg_assists']) if row['avg_assists'] is not None else 0, 2),
                    'avg_headshot_rate': round(float(row['avg_headshot_rate']) if row['avg_headshot_rate'] is not None else 0, 3),
                    'avg_first_kill': round(float(row['avg_first_kill']) if row['avg_first_kill'] is not None else 0, 2),
                    'avg_first_death': round(float(row['avg_first_death']) if row['avg_first_death'] is not None else 0, 2),
                    'first_kill_rate': round(float(row['first_kill_rate']) if row['first_kill_rate'] is not None else 0, 3),
                    'first_death_rate': round(float(row['first_death_rate']) if row['first_death_rate'] is not None else 0, 3),
                    'avg_awp_kills': round(float(row['avg_awp_kills']) if row['avg_awp_kills'] is not None else 0, 2),
                    'mvp_count': int(row['mvp_count'] or 0),
                    'win_rate': round(float(row['win_rate']) if row['win_rate'] is not None else 0, 3),
                    'avg_kast': round(float(row['avg_kast']) if row['avg_kast'] is not None else 0, 3),
                    'avg_rws': round(float(row['avg_rws']) if row['avg_rws'] is not None else 0, 2)
                },
                'last_match_time': row.get('last_match_time')
            }
            leaderboard_data.append(player_data)

        return jsonify({'success': True, 'data': leaderboard_data, 'meta': {'stat_type': stat_type, 'map_filter': map_filter}})
    except Exception as e:
        logger.error(f"获取自定义比赛排行榜错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>/matches', methods=['POST'])
def link_match_to_tournament(tournament_id):
    """关联比赛到自定义比赛"""
    try:
        data = request.get_json()
        
        required_fields = ['match_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'缺少必需字段: {field}'}), 400
        
        # 检查比赛是否存在
        match_check_query = "SELECT match_id, match_winner FROM matches WHERE match_id = %s"
        match_exists = execute_query(match_check_query, [data['match_id']])
        
        if not match_exists:
            return jsonify({'success': False, 'error': '比赛不存在'}), 404
        
        # 如果未指定team1_id或team2_id，则根据比赛玩家自动生成或复用队伍
        team1_id = data.get('team1_id')
        team2_id = data.get('team2_id')

        try:
            # 查询该比赛的两队玩家UID
            team1_players = execute_query(
                "SELECT uid FROM match_player_stats WHERE match_id = %s AND team_id = 1",
                [data['match_id']]
            )
            team2_players = execute_query(
                "SELECT uid FROM match_player_stats WHERE match_id = %s AND team_id = 2",
                [data['match_id']]
            )

            team1_uids = sorted(list({p['uid'] for p in team1_players}))
            team2_uids = sorted(list({p['uid'] for p in team2_players}))

            # 防御性校验
            if (team1_id is None and len(team1_uids) == 0) or (team2_id is None and len(team2_uids) == 0):
                return jsonify({'success': False, 'error': '无法从比赛数据解析两支队伍的玩家'}), 400

            # 读取已存在的队伍并进行去重匹配（按玩家UID集合匹配）
            existing_teams = execute_query(
                "SELECT id, player_uids, team_name FROM custom_tournament_teams WHERE tournament_id = %s",
                [tournament_id]
            )

            def find_team_id_by_uids(uids_set):
                for et in existing_teams or []:
                    try:
                        et_uids = json.loads(et['player_uids']) if et.get('player_uids') else []
                    except Exception:
                        et_uids = []
                    if set(et_uids) == set(uids_set):
                        return et['id']
                return None

            # 生成或复用队伍1
            if team1_id is None:
                team1_id = find_team_id_by_uids(team1_uids)
                if team1_id is None:
                    # 选取该队Rating2最高的玩家作为队长，并用其昵称/用户名生成队名
                    top1 = execute_query(
                        """
                        SELECT mps.uid, p.username, p.nickname, mps.rating2
                        FROM match_player_stats mps
                        LEFT JOIN players p ON p.uid = mps.uid
                        WHERE mps.match_id = %s AND mps.team_id = 1
                        ORDER BY mps.rating2 DESC
                        LIMIT 1
                        """,
                        [data['match_id']]
                    )
                    captain1_uid = top1[0]['uid'] if top1 else None
                    captain1_name = (top1[0].get('nickname') or top1[0].get('username')) if top1 else None
                    team1_name = f"{captain1_name}的队伍" if captain1_name else "自动队伍1"

                    insert_team1_id = execute_insert_query(
                        """
                        INSERT INTO custom_tournament_teams (tournament_id, team_name, player_uids, captain_uid)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [tournament_id, team1_name, json.dumps(team1_uids), captain1_uid]
                    )
                    if not insert_team1_id:
                        return jsonify({'success': False, 'error': '创建队伍1失败'}), 500
                    team1_id = insert_team1_id

            # 生成或复用队伍2
            if team2_id is None:
                team2_id = find_team_id_by_uids(team2_uids)
                if team2_id is None:
                    top2 = execute_query(
                        """
                        SELECT mps.uid, p.username, p.nickname, mps.rating2
                        FROM match_player_stats mps
                        LEFT JOIN players p ON p.uid = mps.uid
                        WHERE mps.match_id = %s AND mps.team_id = 2
                        ORDER BY mps.rating2 DESC
                        LIMIT 1
                        """,
                        [data['match_id']]
                    )
                    captain2_uid = top2[0]['uid'] if top2 else None
                    captain2_name = (top2[0].get('nickname') or top2[0].get('username')) if top2 else None
                    team2_name = f"{captain2_name}的队伍" if captain2_name else "自动队伍2"

                    insert_team2_id = execute_insert_query(
                        """
                        INSERT INTO custom_tournament_teams (tournament_id, team_name, player_uids, captain_uid)
                        VALUES (%s, %s, %s, %s)
                        """,
                        [tournament_id, team2_name, json.dumps(team2_uids), captain2_uid]
                    )
                    if not insert_team2_id:
                        return jsonify({'success': False, 'error': '创建队伍2失败'}), 500
                    team2_id = insert_team2_id
        except Exception as e:
            logger.error(f"解析并创建队伍失败: {e}")
            return jsonify({'success': False, 'error': '解析队伍数据失败'}), 500

        # 插入关联记录
        # 根据 matches.match_winner 映射到当前的 team1_id / team2_id，确定 winner_team_id
        winner_team_id = None
        try:
            original_winner = match_exists[0].get('match_winner') if match_exists else None
            if original_winner == 1:
                winner_team_id = team1_id
            elif original_winner == 2:
                winner_team_id = team2_id
        except Exception:
            winner_team_id = None

        link_query = """
        INSERT INTO custom_tournament_matches 
        (tournament_id, match_id, team1_id, team2_id, round_name, match_order, winner_team_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        link_params = [
            tournament_id,
            data['match_id'],
            team1_id,
            team2_id,
            data.get('round_name', ''),
            data.get('match_order', 0),
            winner_team_id
        ]
        
        link_id = execute_insert_query(link_query, link_params)
        
        if not link_id:
            return jsonify({'success': False, 'error': '关联比赛失败'}), 500
        
        # 更新 total_matches 为当前关联场数
        update_total_query = """
        UPDATE custom_tournaments
        SET total_matches = (
            SELECT COUNT(*)
            FROM custom_tournament_matches
            WHERE tournament_id = %s
        )
        WHERE id = %s
        """
        try:
            execute_update_query(update_total_query, [tournament_id, tournament_id])
        except Exception as e:
            logger.error(f"更新total_matches失败: {e}")
        
        return jsonify({
            'success': True,
            'data': {'link_id': link_id, 'team1_id': team1_id, 'team2_id': team2_id},
            'message': '比赛关联成功，队伍已自动生成/复用'
        })
        
    except Exception as e:
        logger.error(f"关联比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/custom-tournaments/<int:tournament_id>/matches/<int:link_id>', methods=['DELETE'])
def unlink_match_from_tournament(tournament_id, link_id):
    """取消关联比赛（带智能队伍清理）"""
    try:
        # 首先获取要删除的比赛关联信息，包括涉及的队伍
        match_info_query = """
        SELECT team1_id, team2_id, match_id
        FROM custom_tournament_matches 
        WHERE id = %s AND tournament_id = %s
        """
        match_info = execute_query(match_info_query, [link_id, tournament_id])
        
        if not match_info:
            return jsonify({'success': False, 'error': '关联记录不存在'}), 404
        
        team1_id = match_info[0]['team1_id']
        team2_id = match_info[0]['team2_id']
        
        # 删除比赛关联记录
        delete_query = """
        DELETE FROM custom_tournament_matches 
        WHERE id = %s AND tournament_id = %s
        """
        success = execute_update_query(delete_query, [link_id, tournament_id])
        
        if not success:
            return jsonify({'success': False, 'error': '取消关联失败'}), 500
        
        # 智能清理未使用的队伍
        deleted_teams = []
        for team_id in [team1_id, team2_id]:
            if team_id:
                # 检查该队伍是否还在其他比赛中使用
                team_usage_query = """
                SELECT COUNT(*) as usage_count
                FROM custom_tournament_matches
                WHERE tournament_id = %s AND (team1_id = %s OR team2_id = %s)
                """
                usage_result = execute_query(team_usage_query, [tournament_id, team_id, team_id])
                usage_count = usage_result[0]['usage_count'] if usage_result else 0
                
                if usage_count == 0:
                    # 队伍未被其他比赛使用，可以删除
                    try:
                        # 获取队伍名称用于返回信息
                        team_name_query = "SELECT team_name FROM custom_tournament_teams WHERE id = %s"
                        team_name_result = execute_query(team_name_query, [team_id])
                        team_name = team_name_result[0]['team_name'] if team_name_result else f"ID:{team_id}"
                        
                        # 删除队伍
                        delete_team_query = "DELETE FROM custom_tournament_teams WHERE id = %s AND tournament_id = %s"
                        team_delete_success = execute_update_query(delete_team_query, [team_id, tournament_id])
                        
                        if team_delete_success:
                            deleted_teams.append(team_name)
                            logger.info(f"已删除未使用的队伍: {team_name} (ID: {team_id})")
                        else:
                            logger.warning(f"删除队伍失败: {team_name} (ID: {team_id})")
                    except Exception as e:
                        logger.error(f"删除队伍 {team_id} 时出错: {e}")
                else:
                    logger.info(f"队伍 {team_id} 仍在其他 {usage_count} 场比赛中使用，保留")
        
        # 更新 total_matches 为当前关联场数
        update_total_query = """
        UPDATE custom_tournaments
        SET total_matches = (
            SELECT COUNT(*)
            FROM custom_tournament_matches
            WHERE tournament_id = %s
        )
        WHERE id = %s
        """
        try:
            execute_update_query(update_total_query, [tournament_id, tournament_id])
        except Exception as e:
            logger.error(f"更新total_matches失败: {e}")
        
        # 构建返回消息
        message = '取消关联成功'
        if deleted_teams:
            message += f'，同时删除了未使用的队伍: {", ".join(deleted_teams)}'
        
        return jsonify({
            'success': True,
            'message': message,
            'deleted_teams': deleted_teams
        })
        
    except Exception as e:
        logger.error(f"取消关联比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/matches/available', methods=['GET'])
def get_available_matches():
    """获取可用于关联的比赛列表"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        search = request.args.get('search', '')
        
        # 构建查询 - 获取所有比赛并标识是否已被关联
        base_query = """
        SELECT 
            m.match_id,
            m.map_name,
            m.start_time,
            m.group1_all_score,
            m.group2_all_score,
            m.match_winner,
            CASE WHEN ctm.match_id IS NOT NULL THEN 1 ELSE 0 END as is_linked
        FROM matches m
        LEFT JOIN custom_tournament_matches ctm ON m.match_id = ctm.match_id
        WHERE 1=1
        """
        params = []
        
        if search:
            base_query += " AND (m.match_id LIKE %s OR m.map_name LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param])
        
        base_query += " ORDER BY m.start_time DESC LIMIT %s OFFSET %s"
        params.extend([limit, (page - 1) * limit])
        
        matches = execute_query(base_query, params)
        
        return jsonify({
            'success': True,
            'data': matches or []
        })
        
    except Exception as e:
        logger.error(f"获取可用比赛错误: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("启动CS:GO玩家数据API服务器...")
    app.run(host='0.0.0.0', port=5001, debug=True)