#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5E对战平台比赛数据获取脚本（优化版）
基于实际API返回数据结构重新设计
"""

import json
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor
import os
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('match_details_optimized.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = '106.14.121.148'
    port: int = 3306
    user: str = 'root'
    password: str = '9AkWaqCsrd12'
    database: str = 'cs_match_data'
    charset: str = 'utf8mb4'

class MatchDetailsFetcherOptimized:
    """优化版比赛详情获取器"""
    
    def __init__(self, db_config: DatabaseConfig = None):
        self.db_config = db_config or DatabaseConfig()
        self.db_connection = None
        
        # API配置
        self.base_url_match = "https://gate.5eplay.com/crane/http/api/data/match/"
        self.base_url_vip = "https://gate.5eplay.com/crane/http/api/data/vip_plus_match_data/"
        
        # 请求头配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        # 连接数据库
        self.connect_database()
    
    def set_authorization(self, auth_token: str = ""):
        """设置授权头"""
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
        else:
            self.headers.pop('Authorization', None)
    
    def connect_database(self) -> bool:
        """连接数据库"""
        try:
            self.db_connection = pymysql.connect(
                host=self.db_config.host,
                port=self.db_config.port,
                user=self.db_config.user,
                password=self.db_config.password,
                database=self.db_config.database,
                charset=self.db_config.charset,
                cursorclass=DictCursor,
                autocommit=True
            )
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def close_database(self):
        """关闭数据库连接"""
        if self.db_connection:
            self.db_connection.close()
            logger.info("数据库连接已关闭")
    
    def load_match_ids(self, json_file: str = 'filtered_matches.json') -> List[str]:
        """从JSON文件加载比赛ID列表"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if 'matches' in data and isinstance(data['matches'], list):
                match_ids = [str(match['match_id']) for match in data['matches'] if 'match_id' in match]
                logger.info(f"成功加载 {len(match_ids)} 个比赛ID")
                return match_ids
            else:
                logger.error(f"JSON文件格式不正确: {json_file}")
                return []
                
        except FileNotFoundError:
            logger.error(f"文件未找到: {json_file}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return []
        except Exception as e:
            logger.error(f"加载比赛ID失败: {e}")
            return []
    
    def fetch_match_detail(self, match_id: str) -> Optional[Dict[str, Any]]:
        """获取比赛详情数据"""
        url = f"{self.base_url_match}{match_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API返回状态
            if data.get('code') == 0:  # 5E API成功状态码是0
                logger.info(f"Match Detail API调用成功: {match_id}")
                return data.get('data')
            else:
                logger.warning(f"Match Detail API返回错误: {match_id}, code: {data.get('code')}, message: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Match Detail API请求失败: {match_id}, 错误: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Match Detail API响应解析失败: {match_id}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"Match Detail API未知错误: {match_id}, 错误: {e}")
            return None
    
    def fetch_vip_plus_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """获取VIP Plus数据"""
        url = f"{self.base_url_vip}{match_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API返回状态
            if data.get('code') == 0:  # 5E API成功状态码是0
                logger.info(f"VIP Plus API调用成功: {match_id}")
                return data.get('data')
            else:
                logger.warning(f"VIP Plus API返回错误: {match_id}, code: {data.get('code')}, message: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"VIP Plus API请求失败: {match_id}, 错误: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"VIP Plus API响应解析失败: {match_id}, 错误: {e}")
            return None
        except Exception as e:
            logger.error(f"VIP Plus API未知错误: {match_id}, 错误: {e}")
            return None
    
    def fetch_both_apis(self, match_id: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """获取两个API的数据"""
        logger.info(f"开始获取比赛数据: {match_id}")
        
        # 获取Match Detail数据
        match_detail = self.fetch_match_detail(match_id)
        
        # 获取VIP Plus数据
        vip_plus_data = self.fetch_vip_plus_data(match_id)
        
        return match_detail, vip_plus_data
    
    def save_to_database(self, match_id: str, match_detail: Dict, vip_plus_data: Dict) -> bool:
        """保存数据到数据库"""
        if not self.db_connection:
            logger.error("数据库未连接")
            return False
        
        try:
            cursor = self.db_connection.cursor()
            
            # 保存比赛基本信息
            if match_detail:
                self._save_match_info(cursor, match_id, match_detail)
                # 保存玩家数据
                self._save_players_data(cursor, match_id, match_detail)
            
            # 保存VIP Plus数据
            if vip_plus_data:
                self._save_vip_plus_stats(cursor, match_id, vip_plus_data)
            
            # 记录采集日志
            self._log_collection_status(cursor, match_id, 'match_detail', 'success' if match_detail else 'failed')
            self._log_collection_status(cursor, match_id, 'vip_plus', 'success' if vip_plus_data else 'failed')
            
            logger.info(f"数据保存成功: {match_id}")
            return True
            
        except Exception as e:
            logger.error(f"数据保存失败: {match_id}, 错误: {e}")
            if 'cursor' in locals():
                self._log_collection_status(cursor, match_id, 'match_detail', 'failed', str(e))
            return False
    
    def _save_match_info(self, cursor, match_id: str, match_detail: Dict):
        """保存比赛基本信息"""
        main_info = match_detail.get('main', {})
        
        sql = """
        INSERT INTO matches (
            match_id, match_code, game_mode, game_name, map_name, map_desc,
            start_time, end_time, round_total, 
            group1_all_score, group2_all_score, group1_fh_score, group1_sh_score,
            group2_fh_score, group2_sh_score, group1_fh_role, group2_fh_role,
            group1_sh_role, group2_sh_role, group1_uids, group2_uids,
            match_winner, knife_winner, knife_winner_role,
            group1_origin_elo, group1_change_elo, group2_origin_elo, group2_change_elo,
            demo_url, location, location_full, server_ip, server_port,
            season, year, match_mode, mvp_uid, most_kill_uid, most_assist_uid,
            most_awp_uid, most_headshot_uid, most_first_kill_uid, most_1v2_uid,
            most_jump_uid, most_end_uid, status, waiver, cs_type,
            priority_show_type, pug10m_show_type, credit_match_status
        ) VALUES (
            %(match_id)s, %(match_code)s, %(game_mode)s, %(game_name)s, %(map_name)s, %(map_desc)s,
            %(start_time)s, %(end_time)s, %(round_total)s,
            %(group1_all_score)s, %(group2_all_score)s, %(group1_fh_score)s, %(group1_sh_score)s,
            %(group2_fh_score)s, %(group2_sh_score)s, %(group1_fh_role)s, %(group2_fh_role)s,
            %(group1_sh_role)s, %(group2_sh_role)s, %(group1_uids)s, %(group2_uids)s,
            %(match_winner)s, %(knife_winner)s, %(knife_winner_role)s,
            %(group1_origin_elo)s, %(group1_change_elo)s, %(group2_origin_elo)s, %(group2_change_elo)s,
            %(demo_url)s, %(location)s, %(location_full)s, %(server_ip)s, %(server_port)s,
            %(season)s, %(year)s, %(match_mode)s, %(mvp_uid)s, %(most_kill_uid)s, %(most_assist_uid)s,
            %(most_awp_uid)s, %(most_headshot_uid)s, %(most_first_kill_uid)s, %(most_1v2_uid)s,
            %(most_jump_uid)s, %(most_end_uid)s, %(status)s, %(waiver)s, %(cs_type)s,
            %(priority_show_type)s, %(pug10m_show_type)s, %(credit_match_status)s
        ) ON DUPLICATE KEY UPDATE
            match_code = VALUES(match_code),
            end_time = VALUES(end_time),
            updated_at = CURRENT_TIMESTAMP
        """
        
        # 处理group1_uids和group2_uids
        group1_uids = json.dumps(main_info.get('group1_uids', [])) if main_info.get('group1_uids') else None
        group2_uids = json.dumps(main_info.get('group2_uids', [])) if main_info.get('group2_uids') else None
        
        params = {
            'match_id': match_id,
            'match_code': main_info.get('match_code'),
            'game_mode': main_info.get('game_mode'),
            'game_name': main_info.get('game_name'),
            'map_name': main_info.get('map'),
            'map_desc': main_info.get('map_desc'),
            'start_time': main_info.get('start_time'),
            'end_time': main_info.get('end_time'),
            'round_total': main_info.get('round_total'),
            'group1_all_score': main_info.get('group1_all_score'),
            'group2_all_score': main_info.get('group2_all_score'),
            'group1_fh_score': main_info.get('group1_fh_score'),
            'group1_sh_score': main_info.get('group1_sh_score'),
            'group2_fh_score': main_info.get('group2_fh_score'),
            'group2_sh_score': main_info.get('group2_sh_score'),
            'group1_fh_role': main_info.get('group1_fh_role'),
            'group2_fh_role': main_info.get('group2_fh_role'),
            'group1_sh_role': main_info.get('group1_sh_role'),
            'group2_sh_role': main_info.get('group2_sh_role'),
            'group1_uids': group1_uids,
            'group2_uids': group2_uids,
            'match_winner': main_info.get('match_winner'),
            'knife_winner': main_info.get('knife_winner'),
            'knife_winner_role': main_info.get('knife_winner_role'),
            'group1_origin_elo': main_info.get('group1_origin_elo'),
            'group1_change_elo': main_info.get('group1_change_elo'),
            'group2_origin_elo': main_info.get('group2_origin_elo'),
            'group2_change_elo': main_info.get('group2_change_elo'),
            'demo_url': main_info.get('demo_url'),
            'location': main_info.get('location'),
            'location_full': main_info.get('location_full'),
            'server_ip': main_info.get('server_ip'),
            'server_port': main_info.get('server_port'),
            'season': main_info.get('season'),
            'year': main_info.get('year'),
            'match_mode': main_info.get('match_mode'),
            'mvp_uid': main_info.get('mvp_uid'),
            'most_kill_uid': main_info.get('most_kill_uid'),
            'most_assist_uid': main_info.get('most_assist_uid'),
            'most_awp_uid': main_info.get('most_awp_uid'),
            'most_headshot_uid': main_info.get('most_headshot_uid'),
            'most_first_kill_uid': main_info.get('most_first_kill_uid'),
            'most_1v2_uid': main_info.get('most_1v2_uid'),
            'most_jump_uid': main_info.get('most_jump_uid'),
            'most_end_uid': main_info.get('most_end_uid'),
            'status': main_info.get('status', 1),
            'waiver': main_info.get('waiver', 0),
            'cs_type': main_info.get('cs_type', 0),
            'priority_show_type': main_info.get('priority_show_type', 0),
            'pug10m_show_type': main_info.get('pug10m_show_type', 0),
            'credit_match_status': main_info.get('credit_match_status', 0)
        }
        
        cursor.execute(sql, params)
        logger.debug(f"比赛信息保存成功: {match_id}")
    
    def _save_players_data(self, cursor, match_id: str, match_detail: Dict):
        """保存玩家数据"""
        # 处理group1和group2的玩家数据
        for group_num in [1, 2]:
            group_key = f'group_{group_num}'
            group_data = match_detail.get(group_key, [])
            
            for player_data in group_data:
                # 保存玩家基本信息
                self._save_player_info(cursor, player_data)
                
                # 保存玩家比赛统计数据
                self._save_player_match_stats(cursor, match_id, player_data, group_num)
    
    def _save_player_info(self, cursor, player_data: Dict):
        """保存玩家基本信息"""
        user_info = player_data.get('user_info', {})
        user_data = user_info.get('user_data', {})
        profile = user_info.get('profile', {})
        status = user_info.get('status', {})
        platform_exp = user_info.get('platformExp', {})
        steam = user_data.get('steam', {})
        trusted = user_info.get('trusted', {})
        certify = user_info.get('certify', {})
        identity = user_info.get('identity', {})
        
        
        sql = """
        INSERT INTO players (
            uid, steam_id, username, nickname, uuid, email, area, mobile,
            domain, avatar_url, avatar_audit_status, rgb_avatar_url, photo_url,
            gender, birthday, country_id, region_id, city_id, language,
            platform_level, platform_exp, credit, credit_level, credit_score,
            credit_status, certify_status, certify_age, user_status, new_user,
            anticheat_type, anticheat_status, user_created_at, user_updated_at
        ) VALUES (
            %(uid)s, %(steam_id)s, %(username)s, %(nickname)s, %(uuid)s, %(email)s, %(area)s, %(mobile)s,
            %(domain)s, %(avatar_url)s, %(avatar_audit_status)s, %(rgb_avatar_url)s, %(photo_url)s,
            %(gender)s, %(birthday)s, %(country_id)s, %(region_id)s, %(city_id)s, %(language)s,
            %(platform_level)s, %(platform_exp)s, %(credit)s, %(credit_level)s, %(credit_score)s,
            %(credit_status)s, %(certify_status)s, %(certify_age)s, %(user_status)s, %(new_user)s,
            %(anticheat_type)s, %(anticheat_status)s, %(user_created_at)s, %(user_updated_at)s
        ) ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            nickname = VALUES(nickname),
            platform_level = VALUES(platform_level),
            platform_exp = VALUES(platform_exp),
            credit = VALUES(credit),
            credit_level = VALUES(credit_level),
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = {
            'uid': user_data.get('uid'),
            'steam_id': steam.get('steamId'),
            'username': user_data.get('username'),
            'nickname': user_data.get('nickname'),
            'uuid': user_data.get('uuid'),
            'email': user_data.get('email'),
            'area': user_data.get('area'),
            'mobile': user_data.get('mobile'),
            'domain': profile.get('domain'),
            'avatar_url': profile.get('avatar'),
            'avatar_audit_status': profile.get('avatar_audit_status'),
            'rgb_avatar_url': profile.get('rgb_avatar'),
            'photo_url': profile.get('photo'),
            'gender': profile.get('gender'),
            'birthday': profile.get('birthday'),
            'country_id': profile.get('country_id'),
            'region_id': profile.get('region_id'),
            'city_id': profile.get('city_id'),
            'language': profile.get('language'),
            'platform_level': platform_exp.get('level'),
            'platform_exp': platform_exp.get('exp'),
            'credit': trusted.get('credit'),
            'credit_level': trusted.get('credit_level'),
            'credit_score': trusted.get('credit_score'),
            'credit_status': trusted.get('credit_status'),
            'certify_status': certify.get('status'),
            'certify_age': certify.get('age'),
            'user_status': status.get('status'),
            'new_user': status.get('new_user'),
            'anticheat_type': identity.get('anticheat_type'),
            'anticheat_status': identity.get('anticheat_status'),
            'user_created_at': user_data.get('created_at'),
            'user_updated_at': user_data.get('updated_at')
        }
        
        cursor.execute(sql, params)
    
    def _save_player_match_stats(self, cursor, match_id: str, player_data: Dict, team_id: int):
        """保存玩家比赛统计数据"""
        fight = player_data.get('fight', {})
        fight_t = player_data.get('fight_t', {})
        fight_ct = player_data.get('fight_ct', {})
        sts = player_data.get('sts', {})
        level_info = player_data.get('level_info', {})
        user_info = player_data.get('user_info', {})
        user_data = user_info.get('user_data', {})
        steam = user_data.get('steam', {})
        
        sql = """
        INSERT INTO match_player_stats (
            match_id, uid, steam_id, team_id, kills, deaths, assists, adr, rating, rating2,
            kast, rws, kill_1, kill_2, kill_3, kill_4, kill_5, headshot, per_headshot,
            awp_kill, awp_kill_ct, awp_kill_t, first_kill, first_death,
            end_1v1, end_1v2, end_1v3, end_1v4, end_1v5,
            flash_enemy, flash_enemy_time, flash_team, flash_team_time, flash_time,
            throw_harm, throw_harm_enemy, planted_bomb, defused_bomb, explode_bomb,
            jump_total, team_kill, benefit_kill, revenge_kill, assisted_kill, perfect_kill, hold_total,
            many_assists_cnt1, many_assists_cnt2, many_assists_cnt3, many_assists_cnt4, many_assists_cnt5,
            is_mvp, is_svp, is_most_kill, is_most_assist, is_most_awp, is_most_headshot,
            is_most_first_kill, is_most_1v2, is_most_jump, is_most_end, is_highlight,
            is_win, is_tie, change_elo, origin_elo, level_id, origin_level_id,
            star_num, origin_star_num, change_rank, origin_rank, match_mode,
            match_team_id, match_time, day, season, year
        ) VALUES (
            %(match_id)s, %(uid)s, %(steam_id)s, %(team_id)s, %(kills)s, %(deaths)s, %(assists)s, %(adr)s, %(rating)s, %(rating2)s,
            %(kast)s, %(rws)s, %(kill_1)s, %(kill_2)s, %(kill_3)s, %(kill_4)s, %(kill_5)s, %(headshot)s, %(per_headshot)s,
            %(awp_kill)s, %(awp_kill_ct)s, %(awp_kill_t)s, %(first_kill)s, %(first_death)s,
            %(end_1v1)s, %(end_1v2)s, %(end_1v3)s, %(end_1v4)s, %(end_1v5)s,
            %(flash_enemy)s, %(flash_enemy_time)s, %(flash_team)s, %(flash_team_time)s, %(flash_time)s,
            %(throw_harm)s, %(throw_harm_enemy)s, %(planted_bomb)s, %(defused_bomb)s, %(explode_bomb)s,
            %(jump_total)s, %(team_kill)s, %(benefit_kill)s, %(revenge_kill)s, %(assisted_kill)s, %(perfect_kill)s, %(hold_total)s,
            %(many_assists_cnt1)s, %(many_assists_cnt2)s, %(many_assists_cnt3)s, %(many_assists_cnt4)s, %(many_assists_cnt5)s,
            %(is_mvp)s, %(is_svp)s, %(is_most_kill)s, %(is_most_assist)s, %(is_most_awp)s, %(is_most_headshot)s,
            %(is_most_first_kill)s, %(is_most_1v2)s, %(is_most_jump)s, %(is_most_end)s, %(is_highlight)s,
            %(is_win)s, %(is_tie)s, %(change_elo)s, %(origin_elo)s, %(level_id)s, %(origin_level_id)s,
            %(star_num)s, %(origin_star_num)s, %(change_rank)s, %(origin_rank)s, %(match_mode)s,
            %(match_team_id)s, %(match_time)s, %(day)s, %(season)s, %(year)s
        ) ON DUPLICATE KEY UPDATE
            kills = VALUES(kills),
            deaths = VALUES(deaths),
            assists = VALUES(assists),
            rating = VALUES(rating),
            updated_at = CURRENT_TIMESTAMP
        """
        
        params = {
            'match_id': match_id,
            'uid': user_data.get('uid'),
            'steam_id': steam.get('steamId'),
            'team_id': team_id,
            'kills': fight.get('kill', 0),
            'deaths': fight.get('death', 0),
            'assists': fight.get('assist', 0),
            'adr': fight.get('adr', 0),
            'rating': fight.get('rating', 0),
            'rating2': fight.get('rating2', 0),
            'kast': fight.get('kast', 0),
            'rws': fight.get('rws', 0),
            'kill_1': fight.get('kill_1', 0),
            'kill_2': fight.get('kill_2', 0),
            'kill_3': fight.get('kill_3', 0),
            'kill_4': fight.get('kill_4', 0),
            'kill_5': fight.get('kill_5', 0),
            'headshot': fight.get('headshot', 0),
            'per_headshot': fight.get('per_headshot', 0),
            'awp_kill': fight.get('awp_kill', 0),
            'awp_kill_ct': fight_ct.get('awp_kill', 0),
            'awp_kill_t': fight_t.get('awp_kill', 0),
            'first_kill': fight.get('first_kill', 0),
            'first_death': fight.get('first_death', 0),
            'end_1v1': fight.get('end_1v1', 0),
            'end_1v2': fight.get('end_1v2', 0),
            'end_1v3': fight.get('end_1v3', 0),
            'end_1v4': fight.get('end_1v4', 0),
            'end_1v5': fight.get('end_1v5', 0),
            'flash_enemy': fight.get('flash_enemy', 0),
            'flash_enemy_time': fight.get('flash_enemy_time', 0),
            'flash_team': fight.get('flash_team', 0),
            'flash_team_time': fight.get('flash_team_time', 0),
            'flash_time': fight.get('flash_time', 0),
            'throw_harm': fight.get('throw_harm', 0),
            'throw_harm_enemy': fight.get('throw_harm_enemy', 0),
            'planted_bomb': fight.get('planted_bomb', 0),
            'defused_bomb': fight.get('defused_bomb', 0),
            'explode_bomb': fight.get('explode_bomb', 0),
            'jump_total': fight.get('jump_total', 0),
            'team_kill': fight.get('team_kill', 0),
            'benefit_kill': fight.get('benefit_kill', 0),
            'revenge_kill': fight.get('revenge_kill', 0),
            'assisted_kill': fight.get('assisted_kill', 0),
            'perfect_kill': fight.get('perfect_kill', 0),
            'hold_total': fight.get('hold_total', 0),
            'many_assists_cnt1': fight.get('many_assists_cnt1', 0),
            'many_assists_cnt2': fight.get('many_assists_cnt2', 0),
            'many_assists_cnt3': fight.get('many_assists_cnt3', 0),
            'many_assists_cnt4': fight.get('many_assists_cnt4', 0),
            'many_assists_cnt5': fight.get('many_assists_cnt5', 0),
            'is_mvp': sts.get('is_mvp', False),
            'is_svp': sts.get('is_svp', False),
            'is_most_kill': sts.get('is_most_kill', False),
            'is_most_assist': sts.get('is_most_assist', False),
            'is_most_awp': sts.get('is_most_awp', False),
            'is_most_headshot': sts.get('is_most_headshot', False),
            'is_most_first_kill': sts.get('is_most_first_kill', False),
            'is_most_1v2': sts.get('is_most_1v2', False),
            'is_most_jump': sts.get('is_most_jump', False),
            'is_most_end': sts.get('is_most_end', False),
            'is_highlight': sts.get('is_highlight', False),
            'is_win': sts.get('is_win', False),
            'is_tie': sts.get('is_tie', False),
            'change_elo': sts.get('change_elo', 0),
            'origin_elo': sts.get('origin_elo', 0),
            'level_id': level_info.get('level_id', 0),
            'origin_level_id': level_info.get('origin_level_id', 0),
            'star_num': level_info.get('star_num', 0),
            'origin_star_num': level_info.get('origin_star_num', 0),
            'change_rank': sts.get('change_rank', 0),
            'origin_rank': sts.get('origin_rank', 0),
            'match_mode': sts.get('match_mode'),
            'match_team_id': sts.get('match_team_id', 0),
            'match_time': sts.get('match_time'),
            'day': sts.get('day'),
            'season': sts.get('season'),
            'year': sts.get('year')
        }
        
        cursor.execute(sql, params)
    
    def _save_vip_plus_stats(self, cursor, match_id: str, vip_plus_data: Dict):
        """保存VIP Plus数据"""
        for steam_id, stats in vip_plus_data.items():
            sql = """
            INSERT INTO match_player_vip_stats (
                match_id, steam_id, fd_ct, fd_t, kast, awp_kill, awp_kill_ct, awp_kill_t,
                damage_stats, damage_receive
            ) VALUES (
                %(match_id)s, %(steam_id)s, %(fd_ct)s, %(fd_t)s, %(kast)s, %(awp_kill)s, %(awp_kill_ct)s, %(awp_kill_t)s,
                %(damage_stats)s, %(damage_receive)s
            ) ON DUPLICATE KEY UPDATE
                fd_ct = VALUES(fd_ct),
                fd_t = VALUES(fd_t),
                kast = VALUES(kast),
                awp_kill = VALUES(awp_kill),
                awp_kill_ct = VALUES(awp_kill_ct),
                awp_kill_t = VALUES(awp_kill_t),
                damage_stats = VALUES(damage_stats),
                damage_receive = VALUES(damage_receive),
                updated_at = CURRENT_TIMESTAMP
            """
            
            # 处理damage_stats和damage_receive字段，确保为整数类型
            damage_stats = stats.get('damage_stats', 0)
            damage_receive = stats.get('damage_receive', 0)

            # 如果是字典类型，尝试提取数值
            if isinstance(damage_stats, dict):
                damage_stats = damage_stats.get('total', 0) or 0
            if isinstance(damage_receive, dict):
                damage_receive = damage_receive.get('total', 0) or 0

            # 确保是整数
            try:
                damage_stats = int(damage_stats)
            except (ValueError, TypeError):
                damage_stats = 0

            try:
                damage_receive = int(damage_receive)
            except (ValueError, TypeError):
                damage_receive = 0

            params = {
                'match_id': match_id,
                'steam_id': steam_id,
                'fd_ct': stats.get('fd_ct', 0),
                'fd_t': stats.get('fd_t', 0),
                'kast': stats.get('kast', 0),
                'awp_kill': stats.get('awp_kill', 0),
                'awp_kill_ct': stats.get('awp_kill_ct', 0),
                'awp_kill_t': stats.get('awp_kill_t', 0),
                'damage_stats': damage_stats,
                'damage_receive': damage_receive
            }
            
            cursor.execute(sql, params)
    
    def _log_collection_status(self, cursor, match_id: str, api_type: str, status: str, error_message: str = None):
        """记录采集状态"""
        sql = """
        INSERT INTO data_collection_logs (match_id, api_type, status, error_message)
        VALUES (%(match_id)s, %(api_type)s, %(status)s, %(error_message)s)
        """
        
        params = {
            'match_id': match_id,
            'api_type': api_type,
            'status': status,
            'error_message': error_message
        }
        
        cursor.execute(sql, params)
    
    def process_all_matches(self, json_file: str = 'filtered_matches.json', 
                          delay: float = 1.0, max_matches: int = None) -> Dict[str, int]:
        """处理所有比赛"""
        match_ids = self.load_match_ids(json_file)
        
        if not match_ids:
            logger.error("没有找到比赛ID")
            return {'success': 0, 'failed': 0}
        
        if max_matches:
            match_ids = match_ids[:max_matches]
            logger.info(f"限制处理比赛数量: {max_matches}")
        
        success_count = 0
        failed_count = 0
        
        logger.info(f"开始处理 {len(match_ids)} 个比赛")
        
        for i, match_id in enumerate(match_ids, 1):
            logger.info(f"处理进度: {i}/{len(match_ids)} - {match_id}")
            
            try:
                # 获取数据
                match_detail, vip_plus_data = self.fetch_both_apis(match_id)
                
                # 保存数据
                if match_detail or vip_plus_data:
                    if self.save_to_database(match_id, match_detail, vip_plus_data):
                        success_count += 1
                    else:
                        failed_count += 1
                else:
                    logger.warning(f"两个API都没有返回数据: {match_id}")
                    failed_count += 1
                
                # 延迟
                if delay > 0 and i < len(match_ids):
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"处理比赛失败: {match_id}, 错误: {e}")
                failed_count += 1
        
        logger.info(f"处理完成 - 成功: {success_count}, 失败: {failed_count}")
        return {'success': success_count, 'failed': failed_count}

def main():
    """主函数"""
    logger.info("=== 5E对战平台比赛数据获取脚本（优化版）启动 ===")
    
    # 创建获取器实例
    fetcher = MatchDetailsFetcherOptimized()
    
    try:
        # 处理比赛数据
        result = fetcher.process_all_matches()
        
        logger.info(f"脚本执行完成 - 成功: {result['success']}, 失败: {result['failed']}")
        
    except KeyboardInterrupt:
        logger.info("用户中断执行")
    except Exception as e:
        logger.error(f"脚本执行出错: {e}")
    finally:
        # 关闭数据库连接
        fetcher.close_database()
        logger.info("=== 脚本执行结束 ===")

if __name__ == "__main__":
    main()