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
        self.base_url_detail = "https://gate.5eplay.com/crane/http/api/data/match/"
        self.base_url_vip = "https://gate.5eplay.com/crane/http/api/data/vip_plus_match_data/"
        
        # 请求头配置 - 针对不同环境优化
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'identity',  # 禁用压缩，避免服务器端压缩问题
            'Connection': 'keep-alive',
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
    
    def _decompress_response(self, content_bytes: bytes, match_id: str, api_name: str) -> Optional[str]:
        """尝试解压响应内容，支持多种压缩格式"""
        import gzip
        import zlib
        import io
        
        # 记录原始字节信息用于调试
        self.logger.debug(f"{api_name} 响应字节长度: {len(content_bytes)}, 前16字节: {content_bytes[:16].hex()}")
        
        # 尝试不同的解压方法
        decompression_methods = [
            ("gzip", lambda data: gzip.GzipFile(fileobj=io.BytesIO(data)).read()),
            ("deflate", lambda data: zlib.decompress(data)),
            ("deflate_raw", lambda data: zlib.decompress(data, -zlib.MAX_WBITS)),
            ("brotli", lambda data: self._try_brotli_decompress(data)),
            ("lzma", lambda data: self._try_lzma_decompress(data)),
            ("lz4", lambda data: self._try_lz4_decompress(data))
        ]
        
        for method_name, decompress_func in decompression_methods:
            try:
                decompressed_data = decompress_func(content_bytes)
                if decompressed_data:
                    content = decompressed_data.decode('utf-8')
                    self.logger.info(f"成功使用{method_name}解压{api_name}内容: {match_id}")
                    return content
            except Exception as e:
                self.logger.debug(f"{method_name}解压失败: {e}")
                continue
        
        # 尝试直接以不同编码解析
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']
        for encoding in encodings:
            try:
                content = content_bytes.decode(encoding)
                if content.strip().startswith(('{', '[')):
                    self.logger.info(f"成功使用{encoding}编码解析{api_name}内容: {match_id}")
                    return content
            except Exception as e:
                self.logger.debug(f"{encoding}编码解析失败: {e}")
                continue
        
        # 所有方法都失败，记录详细信息
        content_preview = content_bytes[:200].decode('utf-8', errors='replace')
        hex_preview = content_bytes[:32].hex()
        self.logger.warning(f"{api_name} API返回非JSON内容且所有解压方法都失败: {match_id}")
        self.logger.warning(f"响应字节长度: {len(content_bytes)}, 十六进制前32字节: {hex_preview}")
        self.logger.warning(f"响应开头: {content_preview}")
        return None
    
    def _try_brotli_decompress(self, data: bytes) -> bytes:
        """尝试brotli解压"""
        try:
            import brotli
            return brotli.decompress(data)
        except ImportError:
            self.logger.debug("brotli模块未安装，跳过brotli解压")
            return b""
        except Exception:
            return b""
    
    def _try_lzma_decompress(self, data: bytes) -> bytes:
        """尝试LZMA解压"""
        try:
            import lzma
            return lzma.decompress(data)
        except ImportError:
            self.logger.debug("lzma模块未安装，跳过lzma解压")
            return b""
        except Exception:
            return b""
    
    def _try_lz4_decompress(self, data: bytes) -> bytes:
        """尝试LZ4解压"""
        try:
            import lz4.frame
            return lz4.frame.decompress(data)
        except ImportError:
            self.logger.debug("lz4模块未安装，跳过lz4解压")
            return b""
        except Exception:
            return b""
    
    def _get_alternative_headers(self) -> Dict[str, str]:
        """获取备用请求头配置"""
        return {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',  # 允许标准压缩
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    def fetch_match_detail(self, match_id: str) -> Optional[Dict[str, Any]]:
        """获取比赛详情数据"""
        return self._fetch_match_detail_with_retry(match_id)

    def _fetch_match_detail_with_retry(self, match_id: str, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """带重试的比赛详情获取"""
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"获取比赛详情 (尝试 {attempt + 1}/{max_retries}): {match_id}")
                detail_data = self._fetch_match_detail_single(match_id)

                if detail_data:
                    return detail_data

                # 如果不是最后一次重试，等待一段时间
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 8)  # 指数退避，最多等待8秒
                    self.logger.info(f"获取比赛详情失败，等待 {wait_time} 秒后重试: {match_id}")
                    time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"获取比赛详情异常 (尝试 {attempt + 1}/{max_retries}): {match_id}, 错误: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 8)
                    time.sleep(wait_time)

        self.logger.error(f"比赛详情获取失败，已重试 {max_retries} 次: {match_id}")
        return None

    def _fetch_match_detail_single(self, match_id: str) -> Optional[Dict[str, Any]]:
        """单次获取比赛详情数据"""
        url = f"{self.base_url_detail}{match_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # 首先尝试直接解析响应文本
            content = response.text

            # 如果响应内容以非JSON字符开头，尝试解压或记录错误
            if not content.strip().startswith(('{', '[')):
                # 记录原始响应信息用于调试
                self.logger.warning(f"Match Detail API返回非JSON内容: {match_id}")
                self.logger.warning(f"响应状态码: {response.status_code}")
                self.logger.warning(f"响应头: {dict(response.headers)}")
                self.logger.warning(f"响应内容长度: {len(response.content)}")
                self.logger.warning(f"响应开头: {content[:200]}")

                # 尝试解压（作为备用方案）
                content = self._decompress_response(response.content, match_id, "Match Detail")
                if content is None:
                    return None

            # 使用解析的内容
            data = json.loads(content)

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
            self.logger.error(f"Match Detail API响应解析失败: {match_id}, 错误: {e}, 响应内容: {response.text[:200]}...")
            return None
        except Exception as e:
            self.logger.error(f"Match Detail API未知错误: {match_id}, 错误: {e}")
            return None
    
    def fetch_vip_plus_data(self, match_id: str) -> Optional[Dict[str, Any]]:
        """获取VIP Plus数据"""
        return self._fetch_vip_plus_data_with_retry(match_id)

    def _fetch_vip_plus_data_with_retry(self, match_id: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """带重试的VIP Plus数据获取"""
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"获取VIP Plus数据 (尝试 {attempt + 1}/{max_retries}): {match_id}")
                vip_data = self._fetch_vip_plus_data_single(match_id)

                if vip_data:
                    return vip_data

                # 如果不是最后一次重试，等待一段时间
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 4)  # 指数退避，最多等待4秒
                    self.logger.info(f"获取VIP Plus数据失败，等待 {wait_time} 秒后重试: {match_id}")
                    time.sleep(wait_time)

            except Exception as e:
                self.logger.error(f"获取VIP Plus数据异常 (尝试 {attempt + 1}/{max_retries}): {match_id}, 错误: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 4)
                    time.sleep(wait_time)

        self.logger.warning(f"VIP Plus数据获取失败，已重试 {max_retries} 次: {match_id}")
        return None

    def _fetch_vip_plus_data_single(self, match_id: str) -> Optional[Dict[str, Any]]:
        """单次获取VIP Plus数据"""
        url = f"{self.base_url_vip}{match_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            # 首先尝试直接解析响应文本
            content = response.text

            # 如果响应内容以非JSON字符开头，尝试解压或记录错误
            if not content.strip().startswith(('{', '[')):
                # 记录原始响应信息用于调试
                self.logger.warning(f"VIP Plus API返回非JSON内容: {match_id}")
                self.logger.warning(f"响应状态码: {response.status_code}")
                self.logger.warning(f"响应头: {dict(response.headers)}")
                self.logger.warning(f"响应内容长度: {len(response.content)}")
                self.logger.warning(f"响应开头: {content[:200]}")

                # 尝试解压（作为备用方案）
                content = self._decompress_response(response.content, match_id, "VIP Plus")
                if content is None:
                    return None

            # 使用解析的内容
            data = json.loads(content)

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
            self.logger.error(f"VIP Plus API响应解析失败: {match_id}, 错误: {e}, 响应内容: {response.text[:200]}...")
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
            # 验证数据完整性
            if not self._validate_match_data(match_data):
                self.logger.error(f"比赛数据验证失败: {match_data.get('match_id')}")
                return False

            with self.db_connection.cursor() as cursor:
                # 智能合并比赛数据
                merged_data = self._merge_match_data(match_data, detail_data)

                # 保存比赛基本信息
                self._save_match_info(cursor, match_data.get('match_id'), merged_data)

                # 保存详情数据
                if detail_data:
                    # 保存玩家数据
                    self._save_players_data(cursor, match_data.get('match_id'), detail_data)

                # 保存VIP Plus数据
                if vip_data:
                    self._save_vip_plus_stats(cursor, match_data.get('match_id'), vip_data)

                # 记录采集日志
                self._log_collection_status(cursor, match_data.get('match_id'), 'match_detail', 'success' if detail_data else 'failed')
                self._log_collection_status(cursor, match_data.get('match_id'), 'vip_plus', 'success' if vip_data else 'failed')

                self.logger.info(f"比赛数据插入成功: {match_data.get('match_id')}")
                return True

        except Exception as e:
            self.logger.error(f"插入比赛数据时出错: {match_data.get('match_id')}, 错误: {e}")
            if 'cursor' in locals():
                self._log_collection_status(cursor, match_data.get('match_id'), 'match_detail', 'failed', str(e))
            return False
    
    def _save_match_info(self, cursor, match_id: str, match_data: Dict):
        """保存比赛基本信息"""
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
        group1_uids = json.dumps(match_data.get('group1_uids', [])) if match_data.get('group1_uids') else None
        group2_uids = json.dumps(match_data.get('group2_uids', [])) if match_data.get('group2_uids') else None
        
        params = {
            'match_id': match_id,
            'match_code': match_data.get('match_code') or match_id,
            'game_mode': match_data.get('game_mode'),
            'game_name': match_data.get('game_name'),
            'map_name': match_data.get('map'),
            'map_desc': match_data.get('map_desc'),
            'start_time': match_data.get('start_time'),
            'end_time': match_data.get('end_time'),
            'round_total': match_data.get('round_total'),
            'group1_all_score': match_data.get('group1_all_score'),
            'group2_all_score': match_data.get('group2_all_score'),
            'group1_fh_score': match_data.get('group1_fh_score'),
            'group1_sh_score': match_data.get('group1_sh_score'),
            'group2_fh_score': match_data.get('group2_fh_score'),
            'group2_sh_score': match_data.get('group2_sh_score'),
            'group1_fh_role': match_data.get('group1_fh_role'),
            'group2_fh_role': match_data.get('group2_fh_role'),
            'group1_sh_role': match_data.get('group1_sh_role'),
            'group2_sh_role': match_data.get('group2_sh_role'),
            'group1_uids': group1_uids,
            'group2_uids': group2_uids,
            'match_winner': match_data.get('match_winner'),
            'knife_winner': match_data.get('knife_winner'),
            'knife_winner_role': match_data.get('knife_winner_role'),
            'group1_origin_elo': match_data.get('group1_origin_elo'),
            'group1_change_elo': match_data.get('group1_change_elo'),
            'group2_origin_elo': match_data.get('group2_origin_elo'),
            'group2_change_elo': match_data.get('group2_change_elo'),
            'demo_url': match_data.get('demo_url'),
            'location': match_data.get('location'),
            'location_full': match_data.get('location_full'),
            'server_ip': match_data.get('server_ip'),
            'server_port': match_data.get('server_port'),
            'season': match_data.get('season'),
            'year': match_data.get('year'),
            'match_mode': match_data.get('match_mode'),
            'mvp_uid': match_data.get('mvp_uid'),
            'most_kill_uid': match_data.get('most_kill_uid'),
            'most_assist_uid': match_data.get('most_assist_uid'),
            'most_awp_uid': match_data.get('most_awp_uid'),
            'most_headshot_uid': match_data.get('most_headshot_uid'),
            'most_first_kill_uid': match_data.get('most_first_kill_uid'),
            'most_1v2_uid': match_data.get('most_1v2_uid'),
            'most_jump_uid': match_data.get('most_jump_uid'),
            'most_end_uid': match_data.get('most_end_uid'),
            'status': match_data.get('status', 1),
            'waiver': match_data.get('waiver', 0),
            'cs_type': match_data.get('cs_type', 0),
            'priority_show_type': match_data.get('priority_show_type', 0),
            'pug10m_show_type': match_data.get('pug10m_show_type', 0),
            'credit_match_status': match_data.get('credit_match_status', 0)
        }
        
        cursor.execute(sql, params)
        self.logger.debug(f"比赛信息保存成功: {match_id}")

    def _validate_match_data(self, match_data: Dict[str, Any]) -> bool:
        """验证比赛数据完整性"""
        if not match_data:
            return False

        # 必需字段检查
        required_fields = ['match_id', 'start_time', 'game_mode']
        for field in required_fields:
            if field not in match_data or not match_data[field]:
                self.logger.warning(f"比赛数据缺少必需字段 {field}: {match_data.get('match_id')}")
                return False

        return True

    def _merge_match_data(self, list_data: Dict[str, Any], detail_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """智能合并比赛数据"""
        merged_data = list_data.copy()

        if detail_data:
            # 从详情数据中获取主要信息
            main_info = detail_data.get('main', {})
            if main_info:
                # 优先使用详情数据中的关键字段
                key_fields = [
                    'match_code', 'game_name', 'map', 'map_desc', 'end_time',
                    'round_total', 'group1_all_score', 'group2_all_score',
                    'group1_fh_score', 'group1_sh_score', 'group2_fh_score', 'group2_sh_score',
                    'group1_fh_role', 'group2_fh_role', 'group1_sh_role', 'group2_sh_role',
                    'group1_uids', 'group2_uids', 'match_winner', 'knife_winner',
                    'knife_winner_role', 'group1_origin_elo', 'group1_change_elo',
                    'group2_origin_elo', 'group2_change_elo', 'demo_url', 'location',
                    'location_full', 'server_ip', 'server_port', 'season', 'year',
                    'match_mode', 'mvp_uid', 'most_kill_uid', 'most_assist_uid',
                    'most_awp_uid', 'most_headshot_uid', 'most_first_kill_uid',
                    'most_1v2_uid', 'most_jump_uid', 'most_end_uid'
                ]

                for field in key_fields:
                    if field in main_info and main_info[field] is not None:
                        merged_data[field] = main_info[field]

        # 确保关键字段存在
        if 'match_code' not in merged_data or not merged_data['match_code']:
            merged_data['match_code'] = list_data.get('match_id', '')

        # 确保map_name字段正确
        if 'map' in merged_data:
            merged_data['map_name'] = merged_data['map']
        elif 'map_name' not in merged_data:
            merged_data['map_name'] = None

        # 设置默认值
        default_values = {
            'status': 1,
            'waiver': 0,
            'cs_type': 0,
            'priority_show_type': 0,
            'pug10m_show_type': 0,
            'credit_match_status': 0,
            'group1_uids': [],
            'group2_uids': []
        }

        for field, default_value in default_values.items():
            if field not in merged_data or merged_data[field] is None:
                merged_data[field] = default_value

        return merged_data

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
        INSERT INTO data_collection_logs (
            match_id, api_type, status, error_message, created_at
        ) VALUES (
            %(match_id)s, %(api_type)s, %(status)s, %(error_message)s, NOW()
        )
        """

        params = {
            'match_id': match_id,
            'api_type': api_type,
            'status': status,
            'error_message': error_message
        }

        cursor.execute(sql, params)
    
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
        self.logger.info("=== 开始执行增量抓取任务 ===")

        # 统计变量
        db_inserted_count = 0
        db_failed_count = 0
        detail_fetched_count = 0
        detail_failed_count = 0
        vip_fetched_count = 0
        vip_failed_count = 0
        skipped_count = 0

        try:
            # 如果需要获取详情，先连接数据库
            if self.fetch_details and not self.connect_database():
                self.logger.warning("数据库连接失败，将只保存到文件")
                self.fetch_details = False

            # 获取新的比赛数据
            self.logger.info("正在获取新的比赛数据...")
            new_matches = self._fetch_incremental_data()

            if new_matches:
                self.logger.info(f"✅ 发现 {len(new_matches)} 条新比赛数据，开始处理...")

                # 如果启用了详情获取，处理每个新比赛
                if self.fetch_details:
                    failed_matches = []  # 记录失败的比赛，用于后续分析

                    for i, match in enumerate(new_matches, 1):
                        match_id = match.get('match_id')
                        self.logger.info(f"🔄 处理比赛 [{i}/{len(new_matches)}]: {match_id}")

                        try:
                            # 检查比赛是否已存在于数据库
                            if self.check_match_exists(match_id):
                                self.logger.info(f"⏭️  比赛 {match_id} 已存在于数据库，跳过")
                                skipped_count += 1
                                continue

                            # 验证数据完整性
                            if not self._validate_match_data(match):
                                self.logger.warning(f"⚠️  比赛 {match_id} 数据验证失败，跳过")
                                db_failed_count += 1
                                failed_matches.append(match_id)
                                continue

                            # 获取比赛详情
                            detail_data = self.fetch_match_detail(match_id)
                            if detail_data:
                                detail_fetched_count += 1
                                self.logger.info(f"✅ 成功获取比赛详情: {match_id}")
                            else:
                                detail_failed_count += 1
                                self.logger.warning(f"❌ 获取比赛详情失败: {match_id}")

                            # 获取VIP数据（可选）
                            vip_data = self.fetch_vip_plus_data(match_id)
                            if vip_data:
                                vip_fetched_count += 1
                                self.logger.info(f"✅ 成功获取VIP数据: {match_id}")
                            else:
                                vip_failed_count += 1
                                self.logger.debug(f"VIP数据获取失败: {match_id}")

                            # 插入数据库
                            if self.insert_match_data(match, detail_data, vip_data):
                                db_inserted_count += 1
                                self.logger.info(f"✅ 成功插入数据库: {match_id}")
                            else:
                                db_failed_count += 1
                                self.logger.error(f"❌ 插入数据库失败: {match_id}")
                                failed_matches.append(match_id)

                            # 动态调整延迟时间
                            delay = self._get_dynamic_delay(i, len(new_matches))
                            if delay > 0:
                                time.sleep(delay)

                        except Exception as e:
                            self.logger.error(f"❌ 处理比赛 {match_id} 时出错: {e}")
                            db_failed_count += 1
                            failed_matches.append(match_id)
                            continue

                    # 输出失败比赛的统计信息
                    if failed_matches:
                        self.logger.warning(f"❌ 处理失败的比赛列表: {failed_matches[:10]}{'...' if len(failed_matches) > 10 else ''}")
                        self.logger.warning(f"❌ 总共失败 {len(failed_matches)} 场比赛")

                # 加载现有数据
                existing_matches = self._load_existing_matches()

                # 合并数据
                all_matches = existing_matches + new_matches

                # 按时间倒序排序
                try:
                    all_matches.sort(key=lambda x: int(x['start_time']), reverse=True)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"排序失败: {e}，保持原始顺序")

                # 保存合并后的数据
                self._save_matches(all_matches)

                # 更新状态
                new_match_ids = [match['match_id'] for match in new_matches]
                self.state["known_match_ids"].extend(new_match_ids)
                self.state["last_fetch_time"] = int(start_time.timestamp())
                self.state["total_matches"] = len(all_matches)

                # 保持known_match_ids列表不要太大（只保留最近的10000个）
                if len(self.state["known_match_ids"]) > 10000:
                    removed_count = len(self.state["known_match_ids"]) - 10000
                    self.state["known_match_ids"] = self.state["known_match_ids"][-10000:]
                    self.logger.info(f"清理了 {removed_count} 个旧的match_id记录")

                self._save_state()

                self.logger.info(f"🎉 增量抓取成功完成，新增 {len(new_matches)} 条记录")
                if self.fetch_details:
                    self.logger.info(f"📊 数据库操作统计: ✅插入成功 {db_inserted_count}, ❌插入失败 {db_failed_count}, ⏭️跳过 {skipped_count}")
                    self.logger.info(f"📊 详情获取统计: ✅成功 {detail_fetched_count}, ❌失败 {detail_failed_count}")
                    self.logger.info(f"📊 VIP数据统计: ✅成功 {vip_fetched_count}, ❌失败 {vip_failed_count}")

            else:
                self.logger.info("📝 没有发现新的比赛数据")
                # 仍然更新最后抓取时间
                self.state["last_fetch_time"] = int(start_time.timestamp())
                self._save_state()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = {
                "success": True,
                "new_matches_count": len(new_matches),
                "total_matches": self.state["total_matches"],
                "db_inserted_count": db_inserted_count,
                "db_failed_count": db_failed_count,
                "skipped_count": skipped_count,
                "detail_fetched_count": detail_fetched_count,
                "detail_failed_count": detail_failed_count,
                "vip_fetched_count": vip_fetched_count,
                "vip_failed_count": vip_failed_count,
                "duration_seconds": duration,
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S')
            }

            self.logger.info(f"📈 执行统计: {result}")
            return result

        except Exception as e:
            self.logger.error(f"❌ 增量抓取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        finally:
            # 确保关闭数据库连接
            if self.fetch_details:
                self.close_database()
            self.logger.info("=== 增量抓取任务结束 ===")

    def _get_dynamic_delay(self, current_index: int, total_count: int) -> float:
        """
        根据进度动态调整延迟时间

        Args:
            current_index: 当前处理到第几个
            total_count: 总数量

        Returns:
            延迟时间（秒）
        """
        # 根据进度调整延迟
        progress = current_index / total_count if total_count > 0 else 0

        # 初始延迟1秒，随着进度增加减少延迟，但最少保持0.5秒
        base_delay = 1.0
        min_delay = 0.5
        dynamic_delay = base_delay * (1 - progress * 0.5)  # 最多减少50%

        return max(min_delay, dynamic_delay)


def main():
    """主函数"""
    print("🚀 启动增量比赛数据抓取器...")
    fetcher = IncrementalMatchFetcher()
    result = fetcher.run_incremental_fetch()

    if result["success"]:
        print("\n" + "="*60)
        print("🎉 增量抓取成功完成!")
        print("="*60)
        print(f"📊 新增比赛: {result['new_matches_count']} 条")
        print(f"📈 总比赛数: {result['total_matches']} 条")
        print(f"⏱️ 耗时: {result['duration_seconds']:.2f} 秒")

        if result.get('db_inserted_count') is not None:
            print(f"💾 数据库操作:")
            print(f"   ✅ 插入成功: {result['db_inserted_count']} 条")
            print(f"   ❌ 插入失败: {result['db_failed_count']} 条")
            print(f"   ⏭️  跳过: {result.get('skipped_count', 0)} 条")

        if result.get('detail_fetched_count') is not None:
            print(f"🔍 详情获取:")
            print(f"   ✅ 成功: {result['detail_fetched_count']} 条")
            print(f"   ❌ 失败: {result['detail_failed_count']} 条")

        if result.get('vip_fetched_count') is not None:
            print(f"⭐ VIP数据:")
            print(f"   ✅ 成功: {result['vip_fetched_count']} 条")
            print(f"   ❌ 失败: {result['vip_failed_count']} 条")

        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ 增量抓取失败!")
        print("="*60)
        print(f"错误信息: {result['error']}")
        print(f"开始时间: {result.get('start_time', '未知')}")
        print("="*60)
        exit(1)


if __name__ == "__main__":
    main()