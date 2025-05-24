# main.py
import os
import time
import json
import logging
import argparse
from datetime import datetime

import config
from scraper import scrape_latest_post
# 导入 qwen_analyzer 中的分析函数和可能的辅助函数
# 假设 qwen_analyzer.py 中有一个主分析函数 analyze_post_with_qwen_and_save
# 我们先定义一个占位，具体导入需要看 qwen_analyzer.py 的最终结构
# from models.qwen_analyzer import analyze_content_with_qwen # 假设这是核心分析函数
# 为了能运行，我们先模拟一个导入
# from models.qwen_analyzer import analyze_content_with_qwen # 实际应解除此行注释，并确保qwen_analyzer.py可被导入

# --- 临时的 sys.path 修改，确保可以找到 models 包 ---
# 在实际部署或更好的项目结构中，这可能通过其他方式处理（如PYTHONPATH或作为可安装包）
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # 假设main.py在项目根目录下的某个地方，或者直接在根
# 如果 main.py 就在项目根目录，则 sys.path.append(current_dir) 即可，或者什么都不用加，如果models是平级的
# 假设 main.py 和 models 文件夹都在 stupid_trump_index 这个根目录下
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # 将当前文件所在目录（即项目根目录）加入sys.path
from models.qwen_analyzer import analyze_content_with_qwen # 现在应该能找到了

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
        # 先确保时间字段存在且格式可比较
        valid_posts = [post for post in history if post.get('time')]
        if not valid_posts:
            return None
        latest_post = max(valid_posts, key=lambda x: x.get('time', ''))
        return latest_post.get('contentID')
        
    except Exception as e:
        logger.error(f"获取上次帖子ID失败: {str(e)}")
        return None

def run_scraper(once=False):
    """运行爬虫并进行AI分析"""
    try:
        logger.info("开始运行特朗普社交媒体爬虫及AI分析流程")
        
        previous_post_id = get_last_post_id()
        if previous_post_id:
            logger.info(f"上次爬取的帖子ID: {previous_post_id}")
        else:
            logger.info("首次运行，尚无历史记录")
        
        # 执行爬取
        scraped_data = scrape_latest_post() # 重命名变量以示区分
        
        if not scraped_data:
            logger.warning("未能获取任何帖子")
            return False
            
        current_post_id = scraped_data.get('contentID')
        
        if current_post_id == previous_post_id and not once: # 如果是单次运行，即使ID相同也分析
            logger.info(f"没有新帖子 (ID: {current_post_id})")
            return True
        else:
            if current_post_id != previous_post_id:
                logger.info(f"成功爬取新帖子 (ID: {current_post_id})")
            else: # current_post_id == previous_post_id and once == True
                logger.info(f"单次运行模式：重新分析已爬取的最新帖子 (ID: {current_post_id})")

            logger.info(f"发布时间: {scraped_data.get('time')}")
            
            text = scraped_data.get('text')
            if text:
                preview = text[:50] + "..." if len(text) > 50 else text
                logger.info(f"文本内容: {preview}")
            if scraped_data.get('images'):
                logger.info(f"图片数量: {len(scraped_data.get('images'))}")
            if scraped_data.get('videos'):
                logger.info(f"包含视频: 是")

            # --- 开始AI分析流程 ---
            logger.info(f"开始对帖子 {current_post_id} 进行AI分析...")
            system_prompt_path = config.BASE_DIR / "docs" / "system_prompt.md"
            system_prompt_text = ""
            try:
                with open(system_prompt_path, 'r', encoding='utf-8') as f:
                    test_system_prompt = f.read().strip()
                if not system_prompt_text:
                    raise ValueError("system_prompt.md 文件内容为空或只有注释。")
                logger.info("成功加载 system_prompt.md")
            except FileNotFoundError:
                logger.error(f"未找到 system_prompt.md 文件于: {system_prompt_path}。使用默认分析提示。")
                system_prompt_text = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。"
            except ValueError as e:
                logger.error(f"{e} 使用默认分析提示。")
                system_prompt_text = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。"

            # 调用 qwen_analyzer 中的函数
            # scraped_data 已经是单个帖子的字典，符合 analyze_content_with_qwen 的输入
            analysis_result = analyze_content_with_qwen(scraped_data, system_prompt_text)

            if analysis_result:
                logger.info(f"帖子 {current_post_id} AI分析完成。")
                logger.info(f"AI分析结果预览: {str(analysis_result)[:100]}...") # 打印部分结果

                # 保存AI分析结果
                result_file_name = f"{current_post_id}_qwen.json"
                result_file_path = config.RESULT_DIR / result_file_name
                try:
                    with open(result_file_path, 'w', encoding='utf-8') as f:
                        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                    logger.info(f"AI分析结果已保存到: {result_file_path}")
                except Exception as e:
                    logger.error(f"保存AI分析结果失败: {e}")
            else:
                logger.error(f"帖子 {current_post_id} AI分析失败或未返回有效结果。")
            # --- AI分析流程结束 ---
            
            return True
    
    except Exception as e:
        logger.error(f"爬虫及AI分析运行出错: {str(e)}", exc_info=True) # 添加 exc_info=True 获取更详细的堆栈跟踪
        return False

def continuous_run(interval_minutes):
    """持续运行爬虫，按指定间隔"""
    try:
        while True:
            run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"--- 新一轮执行开始: {run_time} ---")
            
            success = run_scraper() # run_scraper 现在包含AI分析
            
            logger.info(f"--- 本轮执行结束 ({'成功' if success else '失败'}) ---")
            logger.info(f"等待 {interval_minutes} 分钟后再次运行...")
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"持续运行出错: {str(e)}", exc_info=True)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="特朗普社交媒体爬虫及AI分析器")
    parser.add_argument("--once", action="store_true", help="只运行一次爬取和分析")
    parser.add_argument("--interval", type=int, default=30, help="持续运行时，爬取和分析的间隔（分钟）")
    
    args = parser.parse_args()
    
    config.init() # 初始化日志和配置
    
    if args.once:
        logger.info("单次运行模式（爬取并分析）")
        run_scraper(once=True)
    else:
        logger.info(f"持续运行模式（爬取并分析），间隔时间: {args.interval}分钟")
        continuous_run(args.interval)

if __name__ == "__main__":
    main()