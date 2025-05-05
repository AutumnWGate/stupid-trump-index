# main.py
import os
import time
import json
import logging
import argparse
from datetime import datetime

import config
from scraper import scrape_latest_post

# 获取logger
logger = logging.getLogger(__name__)

def get_last_post_id():
    """获取上次抓取的帖子ID"""
    try:
        if not config.HISTORY_FILE.exists():
            return None
            
        with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            
        if not history:
            return None
            
        # 获取最新的记录
        latest_post = max(history, key=lambda x: x.get('time', ''))
        return latest_post.get('contentID')
        
    except Exception as e:
        logger.error(f"获取上次帖子ID失败: {str(e)}")
        return None

def run_scraper(once=False):
    """运行爬虫"""
    try:
        logger.info("开始运行特朗普社交媒体爬虫")
        
        previous_post_id = get_last_post_id()
        if previous_post_id:
            logger.info(f"上次爬取的帖子ID: {previous_post_id}")
        else:
            logger.info("首次运行，尚无历史记录")
        
        # 执行爬取
        result = scrape_latest_post()
        
        if not result:
            logger.warning("未能获取任何帖子")
            return False
            
        current_post_id = result.get('contentID')
        
        if current_post_id == previous_post_id:
            logger.info(f"没有新帖子 (ID: {current_post_id})")
            return True
        else:
            logger.info(f"成功爬取新帖子 (ID: {current_post_id})")
            logger.info(f"发布时间: {result.get('time')}")
            
            # 打印简要内容信息
            text = result.get('text')
            if text:
                # 截取前50个字符，如果文本较长则添加省略号
                preview = text[:50] + "..." if len(text) > 50 else text
                logger.info(f"文本内容: {preview}")
                
            images = result.get('images')
            if images:
                logger.info(f"图片数量: {len(images)}")
                
            videos = result.get('videos')
            if videos:
                logger.info(f"包含视频: 是")
            
            return True
    
    except Exception as e:
        logger.error(f"爬虫运行出错: {str(e)}")
        return False

def continuous_run(interval_minutes):
    """持续运行爬虫，按指定间隔"""
    try:
        while True:
            run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"运行时间: {run_time}")
            
            success = run_scraper()
            
            # 等待下一次执行
            logger.info(f"等待 {interval_minutes} 分钟后再次运行...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"持续运行出错: {str(e)}")

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="特朗普社交媒体爬虫")
    parser.add_argument("--once", action="store_true", help="只运行一次")
    parser.add_argument("--interval", type=int, default=30, help="运行间隔（分钟）")
    
    args = parser.parse_args()
    
    # 初始化配置
    config.init()
    
    if args.once:
        # 只运行一次
        logger.info("单次运行模式")
        run_scraper(once=True)
    else:
        # 持续运行
        logger.info(f"持续运行模式，间隔时间: {args.interval}分钟")
        continuous_run(args.interval)

if __name__ == "__main__":
    main()