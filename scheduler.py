#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5E对战平台定时任务调度器
用于定时执行增量比赛数据抓取
"""

import schedule
import time
import logging
import os
import sys
from datetime import datetime
from incremental_fetch import IncrementalMatchFetcher, DatabaseConfig


class MatchDataScheduler:
    """比赛数据定时调度器"""
    
    def __init__(self, log_dir: str = "logs", data_dir: str = "data", 
                 db_config: DatabaseConfig = None, fetch_details: bool = True):
        """
        初始化调度器
        
        Args:
            log_dir: 日志存储目录
            data_dir: 数据存储目录
            db_config: 数据库配置
            fetch_details: 是否获取比赛详情
        """
        self.log_dir = log_dir
        self.data_dir = data_dir
        self.fetch_details = fetch_details
        
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        
        # 设置调度器日志
        self._setup_logging()
        
        # 初始化抓取器
        if db_config is None:
            db_config = DatabaseConfig()
        
        self.fetcher = IncrementalMatchFetcher(
            data_dir=data_dir,
            log_dir=log_dir,
            db_config=db_config,
            fetch_details=fetch_details
        )
    
    def _setup_logging(self):
        """设置日志配置"""
        log_file = os.path.join(self.log_dir, f"scheduler_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("Scheduler")
    
    def run_fetch_job(self):
        """执行抓取任务"""
        self.logger.info("🚀 开始执行定时抓取任务")
        
        try:
            result = self.fetcher.run_incremental_fetch()
            
            if result["success"]:
                msg = f"✅ 定时抓取成功完成 - 新增: {result['new_matches_count']} 条, 总计: {result['total_matches']} 条"
                
                # 如果启用了详情获取，显示数据库统计
                if self.fetch_details:
                    db_stats = f", 数据库插入: {result.get('db_inserted_count', 0)} 成功/{result.get('db_failed_count', 0)} 失败"
                    detail_stats = f", 详情获取: {result.get('detail_fetched_count', 0)} 成功/{result.get('detail_failed_count', 0)} 失败"
                    msg += db_stats + detail_stats
                
                self.logger.info(msg)
            else:
                self.logger.error(f"❌ 定时抓取失败: {result['error']}")
                
        except Exception as e:
            self.logger.error(f"💥 定时抓取任务异常: {e}")
    
    def start_scheduler(self):
        """启动调度器"""
        self.logger.info("🕐 启动定时任务调度器")
        
        # 设置定时任务
        # 每天早上8点执行
        schedule.every().day.at("08:00").do(self.run_fetch_job)
        
        # 每天下午2点执行
        schedule.every().day.at("14:00").do(self.run_fetch_job)
        
        # 每天晚上8点执行
        schedule.every().day.at("20:00").do(self.run_fetch_job)
        
        self.logger.info("📅 已设置定时任务:")
        self.logger.info("   - 每天 08:00 执行增量抓取")
        self.logger.info("   - 每天 14:00 执行增量抓取")
        self.logger.info("   - 每天 20:00 执行增量抓取")
        
        # 立即执行一次
        self.logger.info("🏃 立即执行一次抓取任务")
        self.run_fetch_job()
        
        # 开始调度循环
        self.logger.info("⏰ 调度器开始运行，等待定时任务...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
        except KeyboardInterrupt:
            self.logger.info("🛑 收到停止信号，调度器正在关闭...")
        except Exception as e:
            self.logger.error(f"💥 调度器运行异常: {e}")
            raise


def main():
    """主函数"""
    print("5E对战平台比赛数据定时抓取调度器")
    print("=" * 50)
    
    try:
        scheduler = MatchDataScheduler()
        scheduler.start_scheduler()
        
    except KeyboardInterrupt:
        print("\n👋 程序已停止")
        sys.exit(0)
    except Exception as e:
        print(f"💥 程序异常退出: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()