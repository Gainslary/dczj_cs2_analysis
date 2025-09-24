#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5E对战平台比赛数据抓取脚本
用于获取指定API接口中game_mode为39且时间在2025年9月1日0时之后的match_id列表
"""

import requests
import time
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def fetch_match_data(url: str) -> Dict[str, Any]:
    """
    从指定URL获取比赛数据
    
    Args:
        url: API接口地址
        
    Returns:
        返回API响应的JSON数据
        
    Raises:
        requests.RequestException: 请求失败时抛出异常
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查HTTP错误
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON解析失败: {e}")
        raise


def get_september_1_2025_timestamp() -> int:
    """
    获取2025年9月1日0时的时间戳
    
    Returns:
        时间戳
    """
    # 2025年9月1日0时0分0秒
    target_date = datetime(2025, 9, 1, 0, 0, 0)
    return int(target_date.timestamp())


def get_recent_three_months_range() -> Tuple[int, int]:
    """
    计算近三个月的时间范围
    
    Returns:
        (start_timestamp, end_timestamp) 元组
    """
    # 获取当前时间
    now = datetime.now()
    
    # 计算三个月前的时间
    three_months_ago = now - relativedelta(months=3)
    
    # 设置为当天的0点0分0秒
    start_date = three_months_ago.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 设置结束时间为当前时间
    end_date = now
    
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    print(f"时间范围: {start_date.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"时间戳范围: {start_timestamp} 到 {end_timestamp}")
    
    return start_timestamp, end_timestamp


def filter_matches(data: Dict[str, Any], target_timestamp: int) -> List[Dict[str, Any]]:
    """
    筛选出game_mode为39且时间在指定时间戳之后的比赛记录
    
    Args:
        data: API返回的JSON数据
        target_timestamp: 目标时间戳
        
    Returns:
        符合条件的完整比赛数据列表
    """
    filtered_matches = []
    
    # 检查数据结构
    if 'data' not in data:
        print("警告: 响应数据中没有找到'data'字段")
        return filtered_matches
    
    matches = data['data']
    if not isinstance(matches, list):
        print("警告: 'data'字段不是列表格式")
        return filtered_matches
    
    # 筛选符合条件的记录
    for match in matches:
        if isinstance(match, dict) and match.get('game_mode') == '39':
            start_time = match.get('start_time')
            
            if start_time:
                try:
                    # 将start_time转换为整数时间戳
                    start_timestamp = int(start_time)
                    
                    # 检查是否在目标时间之后
                    if start_timestamp >= target_timestamp:
                        # 添加格式化时间字段
                        match_copy = match.copy()
                        match_copy['formatted_start_time'] = datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                        filtered_matches.append(match_copy)
                        
                except (ValueError, TypeError):
                    print(f"警告: 无法解析时间戳 {start_time} for match {match.get('match_id', 'unknown')}")
                    continue
    
    return filtered_matches


def fetch_all_pages(start_time: int, end_time: int, target_timestamp: int) -> List[Dict[str, Any]]:
    """
    自动获取所有页面的数据
    
    Args:
        start_time: API查询开始时间戳
        end_time: API查询结束时间戳
        target_timestamp: 筛选目标时间戳
        
    Returns:
        所有符合条件的比赛数据列表
    """
    all_matches = []
    page = 1
    max_pages = 100  # 设置最大页数防止无限循环
    
    print("开始自动获取所有页面数据...")
    
    while page <= max_pages:
        print(f"正在获取第 {page} 页数据...")
        
        try:
            api_url = build_api_url(page, start_time, end_time)
            data = fetch_match_data(api_url)
            
            # 检查是否有数据
            if 'data' not in data or not data['data']:
                print(f"第 {page} 页没有数据，停止获取")
                break
            
            # 检查当前页面是否所有数据都早于目标时间
            page_data = data['data']
            page_has_valid_data = False
            
            # 检查当前页面是否有符合时间条件的数据
            for match in page_data:
                if isinstance(match, dict) and match.get('game_mode') == '39':
                    start_time_str = match.get('start_time')
                    if start_time_str:
                        try:
                            match_timestamp = int(start_time_str)
                            if match_timestamp >= target_timestamp:
                                page_has_valid_data = True
                                break
                        except (ValueError, TypeError):
                            continue
            
            # 如果当前页面没有符合时间条件的数据，说明后续页面也不会有，可以提前结束
            if not page_has_valid_data:
                print(f"第 {page} 页所有数据都早于2025年9月1日，后续页面数据会更早，停止获取")
                break
            
            # 筛选符合条件的数据
            filtered_matches = filter_matches(data, target_timestamp)
            
            if filtered_matches:
                all_matches.extend(filtered_matches)
                print(f"第 {page} 页找到 {len(filtered_matches)} 条符合条件的记录")
            else:
                print(f"第 {page} 页没有符合条件的记录")
            
            # 如果返回的数据少于30条，说明已经是最后一页
            if len(data['data']) < 30:
                print(f"第 {page} 页数据不足30条，已到最后一页")
                break
            
            page += 1
            
            # 添加延迟避免请求过于频繁
            time.sleep(0.5)
            
        except Exception as e:
            print(f"获取第 {page} 页数据时出错: {e}")
            break
    
    print(f"总共获取了 {page} 页数据")
    return all_matches


def build_api_url(page: int, start_time: int, end_time: int) -> str:
    """
    构建指定页码的API URL
    
    Args:
        page: 页码
        start_time: 开始时间戳
        end_time: 结束时间戳
        
    Returns:
        完整的API URL
    """
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


def main():
    """主函数"""
    print("开始获取比赛数据...")
    
    # 获取近三个月的时间范围
    start_time, end_time = get_recent_three_months_range()
    
    # 获取目标时间戳（2025年9月1日0时）
    target_timestamp = get_september_1_2025_timestamp()
    
    try:
        # 自动获取所有页面的数据
        all_filtered_matches = fetch_all_pages(start_time, end_time, target_timestamp)
        
        if all_filtered_matches:
            # 按时间倒序排序（最新的在前面）
            all_filtered_matches.sort(key=lambda x: int(x['start_time']), reverse=True)
            
            # 输出结果摘要
            print(f"\n总共找到 {len(all_filtered_matches)} 条符合条件的记录")
            print("最新的5条记录:")
            for i, match in enumerate(all_filtered_matches[:5]):
                print(f"{i+1}. Match ID: {match['match_id']}, 开始时间: {match['formatted_start_time']}")
            
            if len(all_filtered_matches) > 5:
                print(f"... 还有 {len(all_filtered_matches) - 5} 条记录")
            
            # 保存为JSON文件
            output_data = {
                "filter_criteria": {
                    "game_mode": "39",
                    "start_time_after": "2025-09-01 00:00:00",
                    "query_time_range": {
                        "start": datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
                        "end": datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
                    }
                },
                "total_count": len(all_filtered_matches),
                "matches": all_filtered_matches
            }
            
            with open('filtered_matches.json', 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"\n完整的比赛详情已保存到 filtered_matches.json")
            print("JSON文件包含:")
            print("- 筛选条件信息")
            print("- 查询时间范围")
            print("- 总记录数")
            print("- 完整的比赛数据（包括所有字段）")
            
        else:
            print("\n没有找到符合条件的记录")
            
    except Exception as e:
        print(f"获取数据时出错: {e}")


if __name__ == "__main__":
    main()