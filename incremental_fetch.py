#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5E对战平台增量比赛数据抓取脚本
用于定时获取新增的比赛数据，避免重复抓取
集成比赛详情获取和数据库存储功能
"""

import requests
import time
import json
import os
import logging
from typing import Dict, Any, List, Tuple, Set, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pymysql
from pymysql.cursors import DictCursor
from dataclasses import dataclass

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = '106.14.121.148'
    port: int = 3306
    user: str = 'root'
    password: str = '9AkWaqCsrd12'
    database: str = 'cs_match_data'
    charset: str = 'utf8mb4'


class IncrementalMatchFetcher:
    """增量比赛数据抓取器（集成比赛详情获取功能）"""
    
    def __init__(self, data_dir: str = "data", log_dir: str = "logs", db_config: DatabaseConfig = None, fetch_details: bool = True):
        """
        初始化抓取器
        
        Args:
            data_dir: 数据存储目录
            log_dir: 日志存储目录
            db_config: 数据库配置
            fetch_details: 是否获取比赛详情并入库
        """
        self.data_dir = data_dir
        self.log_dir = log_dir
        self.state_file = os.path.join(data_dir, "fetch_state.json")
        self.matches_file = os.path.join(data_dir, "all_matches.json")
        self.fetch_details = fetch_details
        
        # 数据库配置
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
        
        # 创建必要的目录
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        # 连接数据库（如果需要获取详情）
        if self.fetch_details:
            self.connect_database()
        
        # 加载状态
        self.state = self._load_state()
        
        # 目标时间戳（2025年9月1日0时）
        self.target_timestamp = self._get_september_1_2025_timestamp()
    
    def _setup_logging(self):
        """设置日志配置"""
        log_file = os.path.join(self.log_dir, f"fetch_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
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
            self.logger.info("数据库连接成功")
            return True
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False
    
    def close_database(self):
        """关闭数据库连接"""
        if self.db_connection:
            self.db_connection.close()
            self.logger.info("数据库连接已关闭")
    
    def fetch_match_detail(self, match_id: str) -> Optional[Dict[str, Any]]:
        """获取比赛详情数据"""
        url = f"{self.base_url_match}{match_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # 检查API返回状态
            if data.get('code') == 0:  # 5E API成功状态码是0
                self.logger.info(f"Match Detail API调用成功: {match_id}")
                return data.get('data')
            else:
                self.logger.warning(f"Match Detail API返回错误: {match_id}, code: {data.get('code')}, message: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Match Detail API请求失败: {match_id}, 错误: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Match Detail API响应解析失败: {match_id}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Match Detail API未知错误: {match_id}, 错误: {e}")
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
                self.logger.info(f"VIP Plus API调用成功: {match_id}")
                return data.get('data')
            else:
                self.logger.warning(f"VIP Plus API返回错误: {match_id}, code: {data.get('code')}, message: {data.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"VIP Plus API请求失败: {match_id}, 错误: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"VIP Plus API响应解析失败: {match_id}, 错误: {e}")
            return None
        except Exception as e:
            self.logger.error(f"VIP Plus API未知错误: {match_id}, 错误: {e}")
            return None
    
    def check_match_exists(self, match_id: str) -> bool:
        """检查比赛是否已存在于数据库中"""
        if not self.db_connection:
            return False
            
        try:
            with self.db_connection.cursor() as cursor:
                sql = "SELECT COUNT(*) as count FROM matches WHERE match_id = %s"
                cursor.execute(sql, (match_id,))
                result = cursor.fetchone()
                return result['count'] > 0
        except Exception as e:
            self.logger.error(f"检查比赛是否存在时出错: {match_id}, 错误: {e}")
            return False
    
    def insert_match_data(self, match_data: Dict[str, Any], detail_data: Optional[Dict[str, Any]] = None, 
                         vip_data: Optional[Dict[str, Any]] = None) -> bool:
        """插入比赛数据到数据库"""
        if not self.db_connection:
            return False
            
        try:
            with self.db_connection.cursor() as cursor:
                # 插入基本比赛信息
                match_sql = """
                INSERT INTO matches (
                    match_id, match_uuid, match_type, match_mode, match_status,
                    start_time, end_time, duration, map_name, server_location,
                    team1_name, team1_score, team2_name, team2_score,
                    winner_team, mvp_player, created_at, updated_at
                ) VALUES (
                    %(match_id)s, %(match_uuid)s, %(match_type)s, %(match_mode)s, %(match_status)s,
                    %(start_time)s, %(end_time)s, %(duration)s, %(map_name)s, %(server_location)s,
                    %(team1_name)s, %(team1_score)s, %(team2_name)s, %(team2_score)s,
                    %(winner_team)s, %(mvp_player)s, NOW(), NOW()
                ) ON DUPLICATE KEY UPDATE
                    match_status = VALUES(match_status),
                    end_time = VALUES(end_time),
                    duration = VALUES(duration),
                    team1_score = VALUES(team1_score),
                    team2_score = VALUES(team2_score),
                    winner_team = VALUES(winner_team),
                    mvp_player = VALUES(mvp_player),
                    updated_at = NOW()
                """
                
                # 准备基本比赛数据
                match_params = {
                    'match_id': match_data.get('match_id'),
                    'match_uuid': match_data.get('match_uuid'),
                    'match_type': match_data.get('match_type'),
                    'match_mode': match_data.get('match_mode'),
                    'match_status': match_data.get('match_status'),
                    'start_time': match_data.get('start_time'),
                    'end_time': match_data.get('end_time'),
                    'duration': match_data.get('duration'),
                    'map_name': match_data.get('map_name'),
                    'server_location': match_data.get('server_location'),
                    'team1_name': match_data.get('team1_name'),
                    'team1_score': match_data.get('team1_score'),
                    'team2_name': match_data.get('team2_name'),
                    'team2_score': match_data.get('team2_score'),
                    'winner_team': match_data.get('winner_team'),
                    'mvp_player': match_data.get('mvp_player')
                }
                
                cursor.execute(match_sql, match_params)
                
                # 如果有详情数据，插入玩家统计
                if detail_data and 'players' in detail_data:
                    self._insert_player_stats(cursor, match_data.get('match_id'), detail_data['players'])
                
                # 如果有VIP数据，插入额外统计
                if vip_data:
                    self._insert_vip_stats(cursor, match_data.get('match_id'), vip_data)
                
                self.logger.info(f"比赛数据插入成功: {match_data.get('match_id')}")
                return True
                
        except Exception as e:
            self.logger.error(f"插入比赛数据时出错: {match_data.get('match_id')}, 错误: {e}")
            return False
    
    def _insert_player_stats(self, cursor, match_id: str, players_data: List[Dict[str, Any]]):
        """插入玩家统计数据"""
        player_sql = """
        INSERT INTO player_stats (
            match_id, player_id, player_name, team_id, team_name,
            kills, deaths, assists, headshots, kd_ratio,
            adr, rating, mvp_count, score, created_at
        ) VALUES (
            %(match_id)s, %(player_id)s, %(player_name)s, %(team_id)s, %(team_name)s,
            %(kills)s, %(deaths)s, %(assists)s, %(headshots)s, %(kd_ratio)s,
            %(adr)s, %(rating)s, %(mvp_count)s, %(score)s, NOW()
        ) ON DUPLICATE KEY UPDATE
            kills = VALUES(kills),
            deaths = VALUES(deaths),
            assists = VALUES(assists),
            headshots = VALUES(headshots),
            kd_ratio = VALUES(kd_ratio),
            adr = VALUES(adr),
            rating = VALUES(rating),
            mvp_count = VALUES(mvp_count),
            score = VALUES(score)
        """
        
        for player in players_data:
            player_params = {
                'match_id': match_id,
                'player_id': player.get('player_id'),
                'player_name': player.get('player_name'),
                'team_id': player.get('team_id'),
                'team_name': player.get('team_name'),
                'kills': player.get('kills'),
                'deaths': player.get('deaths'),
                'assists': player.get('assists'),
                'headshots': player.get('headshots'),
                'kd_ratio': player.get('kd_ratio'),
                'adr': player.get('adr'),
                'rating': player.get('rating'),
                'mvp_count': player.get('mvp_count'),
                'score': player.get('score')
            }
            cursor.execute(player_sql, player_params)
    
    def _insert_vip_stats(self, cursor, match_id: str, vip_data: Dict[str, Any]):
        """插入VIP统计数据"""
        vip_sql = """
        INSERT INTO vip_stats (
            match_id, additional_data, created_at
        ) VALUES (
            %(match_id)s, %(additional_data)s, NOW()
        ) ON DUPLICATE KEY UPDATE
            additional_data = VALUES(additional_data)
        """
        
        vip_params = {
            'match_id': match_id,
            'additional_data': json.dumps(vip_data, ensure_ascii=False)
        }
        cursor.execute(vip_sql, vip_params)
    
    def _load_state(self) -> Dict[str, Any]:
        """加载抓取状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"加载状态文件失败: {e}")
        
        # 默认状态
        return {
            "last_fetch_time": None,
            "last_match_timestamp": None,
            "total_matches": 0,
            "known_match_ids": []
        }
    
    def _save_state(self):
        """保存抓取状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存状态文件失败: {e}")
    
    def _get_september_1_2025_timestamp(self) -> int:
        """获取2025年9月1日0时的时间戳"""
        target_date = datetime(2025, 9, 1, 0, 0, 0)
        return int(target_date.timestamp())
    
    def _get_fetch_time_range(self) -> Tuple[int, int]:
        """
        获取本次抓取的时间范围
        
        Returns:
            (start_timestamp, end_timestamp) 元组
        """
        end_time = int(datetime.now().timestamp())
        
        if self.state["last_fetch_time"]:
            # 从上次抓取时间开始，但往前推1小时以防遗漏
            start_time = self.state["last_fetch_time"] - 3600
        else:
            # 首次抓取，从三个月前开始
            three_months_ago = datetime.now() - relativedelta(months=3)
            start_time = int(three_months_ago.timestamp())
        
        self.logger.info(f"抓取时间范围: {datetime.fromtimestamp(start_time)} 到 {datetime.fromtimestamp(end_time)}")
        return start_time, end_time
    
    def _fetch_match_data(self, url: str) -> Dict[str, Any]:
        """从指定URL获取比赛数据"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            raise
    
    def _build_api_url(self, page: int, start_time: int, end_time: int) -> str:
        """构建API URL"""
        base_url = "https://gate.5eplay.com/crane/http/api/data/match/list"
        params = {
            'match_type': -1,
            'page': page,
            'date': 0,
            'start_time': start_time,
            'end_time': end_time,
            'uuid': '4ecb6b0d-a7ca-11ea-8109-ec0d9a7185b0',
            'limit': 30,
            'cs_type': 0
        }
        
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_str}"
    
    def _filter_new_matches(self, matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        筛选出新的比赛数据
        
        Args:
            matches: 原始比赛数据列表
            
        Returns:
            新的比赛数据列表
        """
        new_matches = []
        known_ids = set(self.state["known_match_ids"])
        
        for match in matches:
            if (isinstance(match, dict) and 
                match.get('game_mode') == '39' and
                match.get('match_id') not in known_ids):
                
                start_time = match.get('start_time')
                if start_time:
                    try:
                        start_timestamp = int(start_time)
                        
                        # 检查是否在目标时间之后
                        if start_timestamp >= self.target_timestamp:
                            # 添加格式化时间字段
                            match_copy = match.copy()
                            match_copy['formatted_start_time'] = datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            new_matches.append(match_copy)
                            
                    except (ValueError, TypeError):
                        self.logger.warning(f"无法解析时间戳 {start_time} for match {match.get('match_id', 'unknown')}")
                        continue
        
        return new_matches
    
    def _fetch_incremental_data(self) -> List[Dict[str, Any]]:
        """获取增量数据"""
        start_time, end_time = self._get_fetch_time_range()
        new_matches = []
        page = 1
        max_pages = 50  # 增量抓取不需要太多页
        
        self.logger.info("开始增量数据抓取...")
        
        while page <= max_pages:
            try:
                api_url = self._build_api_url(page, start_time, end_time)
                data = self._fetch_match_data(api_url)
                
                if 'data' not in data or not data['data']:
                    self.logger.info(f"第 {page} 页没有数据，停止获取")
                    break
                
                # 筛选新的比赛数据
                page_new_matches = self._filter_new_matches(data['data'])
                
                if page_new_matches:
                    new_matches.extend(page_new_matches)
                    self.logger.info(f"第 {page} 页找到 {len(page_new_matches)} 条新记录")
                
                # 如果返回的数据少于30条，说明已经是最后一页
                if len(data['data']) < 30:
                    self.logger.info(f"第 {page} 页数据不足30条，已到最后一页")
                    break
                
                page += 1
                time.sleep(0.5)  # 避免请求过于频繁
                
            except Exception as e:
                self.logger.error(f"获取第 {page} 页数据时出错: {e}")
                break
        
        self.logger.info(f"增量抓取完成，共获取 {len(new_matches)} 条新记录")
        return new_matches
    
    def _load_existing_matches(self) -> List[Dict[str, Any]]:
        """加载现有的比赛数据"""
        if os.path.exists(self.matches_file):
            try:
                with open(self.matches_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('matches', [])
            except Exception as e:
                self.logger.warning(f"加载现有比赛数据失败: {e}")
        return []
    
    def _save_matches(self, all_matches: List[Dict[str, Any]]):
        """保存所有比赛数据"""
        try:
            output_data = {
                "filter_criteria": {
                    "game_mode": "39",
                    "start_time_after": "2025-09-01 00:00:00"
                },
                "last_update": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_count": len(all_matches),
                "matches": all_matches
            }
            
            with open(self.matches_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"比赛数据已保存到 {self.matches_file}")
            
        except Exception as e:
            self.logger.error(f"保存比赛数据失败: {e}")
    
    def run_incremental_fetch(self) -> Dict[str, Any]:
        """
        执行增量抓取
        
        Returns:
            抓取结果统计
        """
        start_time = datetime.now()
        self.logger.info("开始执行增量抓取任务")
        
        # 统计变量
        db_inserted_count = 0
        db_failed_count = 0
        detail_fetched_count = 0
        detail_failed_count = 0
        
        try:
            # 如果需要获取详情，先连接数据库
            if self.fetch_details and not self.connect_database():
                self.logger.warning("数据库连接失败，将只保存到文件")
                self.fetch_details = False
            
            # 获取新的比赛数据
            new_matches = self._fetch_incremental_data()
            
            if new_matches:
                self.logger.info(f"开始处理 {len(new_matches)} 条新比赛数据")
                
                # 如果启用了详情获取，处理每个新比赛
                if self.fetch_details:
                    for i, match in enumerate(new_matches, 1):
                        match_id = match.get('match_id')
                        self.logger.info(f"处理比赛 {i}/{len(new_matches)}: {match_id}")
                        
                        try:
                            # 检查比赛是否已存在于数据库
                            if self.check_match_exists(match_id):
                                self.logger.info(f"比赛 {match_id} 已存在于数据库，跳过")
                                continue
                            
                            # 获取比赛详情
                            detail_data = self.fetch_match_detail(match_id)
                            if detail_data:
                                detail_fetched_count += 1
                                self.logger.info(f"成功获取比赛详情: {match_id}")
                            else:
                                detail_failed_count += 1
                                self.logger.warning(f"获取比赛详情失败: {match_id}")
                            
                            # 获取VIP数据（可选）
                            vip_data = self.fetch_vip_plus_data(match_id)
                            if vip_data:
                                self.logger.info(f"成功获取VIP数据: {match_id}")
                            
                            # 插入数据库
                            if self.insert_match_data(match, detail_data, vip_data):
                                db_inserted_count += 1
                                self.logger.info(f"成功插入数据库: {match_id}")
                            else:
                                db_failed_count += 1
                                self.logger.error(f"插入数据库失败: {match_id}")
                            
                            # 添加延迟避免请求过于频繁
                            time.sleep(1)
                            
                        except Exception as e:
                            self.logger.error(f"处理比赛 {match_id} 时出错: {e}")
                            db_failed_count += 1
                            continue
                
                # 加载现有数据
                existing_matches = self._load_existing_matches()
                
                # 合并数据
                all_matches = existing_matches + new_matches
                
                # 按时间倒序排序
                all_matches.sort(key=lambda x: int(x['start_time']), reverse=True)
                
                # 保存合并后的数据
                self._save_matches(all_matches)
                
                # 更新状态
                new_match_ids = [match['match_id'] for match in new_matches]
                self.state["known_match_ids"].extend(new_match_ids)
                self.state["last_fetch_time"] = int(start_time.timestamp())
                self.state["total_matches"] = len(all_matches)
                
                # 保持known_match_ids列表不要太大（只保留最近的10000个）
                if len(self.state["known_match_ids"]) > 10000:
                    self.state["known_match_ids"] = self.state["known_match_ids"][-10000:]
                
                self._save_state()
                
                self.logger.info(f"增量抓取成功完成，新增 {len(new_matches)} 条记录")
                if self.fetch_details:
                    self.logger.info(f"数据库操作统计: 插入成功 {db_inserted_count}, 插入失败 {db_failed_count}")
                    self.logger.info(f"详情获取统计: 成功 {detail_fetched_count}, 失败 {detail_failed_count}")
                
            else:
                self.logger.info("没有发现新的比赛数据")
                # 仍然更新最后抓取时间
                self.state["last_fetch_time"] = int(start_time.timestamp())
                self._save_state()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                "success": True,
                "new_matches_count": len(new_matches),
                "total_matches": self.state["total_matches"],
                "db_inserted_count": db_inserted_count,
                "db_failed_count": db_failed_count,
                "detail_fetched_count": detail_fetched_count,
                "detail_failed_count": detail_failed_count,
                "duration_seconds": duration,
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            self.logger.error(f"增量抓取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        finally:
            # 确保关闭数据库连接
            if self.fetch_details:
                self.close_database()


def main():
    """主函数"""
    fetcher = IncrementalMatchFetcher()
    result = fetcher.run_incremental_fetch()
    
    if result["success"]:
        print(f"✅ 增量抓取成功完成")
        print(f"📊 新增比赛: {result['new_matches_count']} 条")
        print(f"📈 总比赛数: {result['total_matches']} 条")
        print(f"⏱️ 耗时: {result['duration_seconds']:.2f} 秒")
    else:
        print(f"❌ 增量抓取失败: {result['error']}")
        exit(1)


if __name__ == "__main__":
    main()