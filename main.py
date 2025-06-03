# main.py
import os
import time
import json
import logging
import argparse
from datetime import datetime

import config
from scraper import scrape_latest_post, cleanup_browser
from article_generator import ArticleGenerator
from wechat_publisher import WechatPublisher

import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) 

sys.path.append(os.path.dirname(os.path.abspath(__file__))) 
from models.qwen_analyzer import analyze_content_with_qwen
from models.grok_analyzer import analyze_content_with_grok
from models.gemini_analyzer import analyze_content_with_gemini

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

def run_scraper(once=False, skip_publish=False):
    """
    运行完整的业务流程：采集 → 分析 → 生成 → 发布
    
    Args:
        once (bool): 是否单次运行模式
        skip_publish (bool): 是否跳过发布步骤
    """
    try:
        logger.info("="*60)
        logger.info("开始运行特朗普社交媒体爬虫及AI分析发布流程")
        logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        # ========== 1. 采集阶段 ==========
        logger.info("\n【第1步：数据采集】")
        
        previous_post_id = get_last_post_id()
        if previous_post_id:
            logger.info(f"上次爬取的帖子ID: {previous_post_id}")
        else:
            logger.info("首次运行，尚无历史记录")
        
        # 执行爬取
        scraped_data = scrape_latest_post()
        
        if not scraped_data:
            logger.warning("未能获取任何帖子")
            return False
            
        current_post_id = scraped_data.get('contentID')
        
        if current_post_id == previous_post_id and not once:
            logger.info(f"没有新帖子 (ID: {current_post_id})")
            return True
        else:
            if current_post_id != previous_post_id:
                logger.info(f"成功爬取新帖子 (ID: {current_post_id})")
            else:
                logger.info(f"单次运行模式：重新分析已爬取的最新帖子 (ID: {current_post_id})")

            logger.info(f"发布时间: {scraped_data.get('time')}")
            
            # 显示爬取结果摘要
            text = scraped_data.get('text')
            if text:
                preview = text[:50] + "..." if len(text) > 50 else text
                logger.info(f"文本内容: {preview}")

            # 安全处理图片数量
            images = scraped_data.get('images')
            if images is None:
                logger.info(f"图片数量: 0")
            elif isinstance(images, list):
                logger.info(f"图片数量: {len(images)}")
            else:
                logger.info(f"图片数量: 0")

            # 安全处理视频
            videos = scraped_data.get('videos')
            logger.info(f"视频: {'有' if videos else '无'}")

            # 安全处理截图
            screenshot = scraped_data.get('screenshot')
            logger.info(f"截图: {'已保存' if screenshot else '未生成'}")

            # ========== 2. 分析阶段 ==========
            logger.info(f"\n【第2步：AI分析】")
            logger.info(f"开始对帖子 {current_post_id} 进行多AI分析...")
            
            # 加载系统提示词
            system_prompt_path = config.BASE_DIR / "docs" / "system_prompt.md"
            system_prompt_text = ""
            try:
                with open(system_prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt_text = f.read().strip()
                if not system_prompt_text:
                    raise ValueError("system_prompt.md 文件内容为空或只有注释。")
                logger.info("成功加载 system_prompt.md")
            except FileNotFoundError:
                logger.error(f"未找到 system_prompt.md 文件于: {system_prompt_path}。使用默认分析提示。")
                system_prompt_text = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。"
            except ValueError as e:
                logger.error(f"{e} 使用默认分析提示。")
                system_prompt_text = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。"

            # 按顺序执行三个AI分析：qwen → grok → gemini
            ai_results = {}
            
            # 2.1 QWEN分析
            logger.info("\n--- 开始QWEN分析 ---")
            qwen_result = analyze_content_with_qwen(scraped_data, system_prompt_text)
            if qwen_result:
                logger.info("QWEN分析完成")
                ai_results['qwen'] = qwen_result
                # 保存QWEN结果
                qwen_file_name = f"{current_post_id}_qwen.json"
                qwen_file_path = config.RESULT_DIR / qwen_file_name
                try:
                    with open(qwen_file_path, 'w', encoding='utf-8') as f:
                        json.dump(qwen_result, f, ensure_ascii=False, indent=2)
                    logger.info(f"QWEN分析结果已保存到: {qwen_file_path}")
                except Exception as e:
                    logger.error(f"保存QWEN分析结果失败: {e}")
            else:
                logger.error("QWEN分析失败")
                ai_results['qwen'] = {"error": "QWEN analysis failed"}
            
            # 2.2 GROK分析
            logger.info("\n--- 开始GROK分析 ---")
            grok_result = analyze_content_with_grok(scraped_data, system_prompt_text)
            if grok_result:
                logger.info("GROK分析完成")
                ai_results['grok'] = grok_result
                # 保存GROK结果
                grok_file_name = f"{current_post_id}_grok.json"
                grok_file_path = config.RESULT_DIR / grok_file_name
                try:
                    with open(grok_file_path, 'w', encoding='utf-8') as f:
                        json.dump(grok_result, f, ensure_ascii=False, indent=2)
                    logger.info(f"GROK分析结果已保存到: {grok_file_path}")
                except Exception as e:
                    logger.error(f"保存GROK分析结果失败: {e}")
            else:
                logger.error("GROK分析失败")
                ai_results['grok'] = {"error": "GROK analysis failed"}
            
            # 2.3 GEMINI分析
            logger.info("\n--- 开始GEMINI分析 ---")
            gemini_result = analyze_content_with_gemini(scraped_data, system_prompt_text)
            if gemini_result:
                logger.info("GEMINI分析完成")
                ai_results['gemini'] = gemini_result
                # 保存GEMINI结果
                gemini_file_name = f"{current_post_id}_gemini.json"
                gemini_file_path = config.RESULT_DIR / gemini_file_name
                try:
                    with open(gemini_file_path, 'w', encoding='utf-8') as f:
                        json.dump(gemini_result, f, ensure_ascii=False, indent=2)
                    logger.info(f"GEMINI分析结果已保存到: {gemini_file_path}")
                except Exception as e:
                    logger.error(f"保存GEMINI分析结果失败: {e}")
            else:
                logger.error("GEMINI分析失败")
                ai_results['gemini'] = {"error": "GEMINI analysis failed"}
            
            # 保存综合结果（包含截图信息）
            summary_data = {
                "post_data": {
                    "contentID": current_post_id,
                    "time": scraped_data.get('time'),
                    "text": scraped_data.get('text'),
                    "url": scraped_data.get('url'),
                    "images": scraped_data.get('images'),
                    "videos": scraped_data.get('videos'),
                    "screenshot": scraped_data.get('screenshot')  # 截图路径
                },
                "ai_analysis": ai_results,
                "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            summary_file_name = f"{current_post_id}_all_ai_results.json"
            summary_file_path = config.RESULT_DIR / summary_file_name
            try:
                with open(summary_file_path, 'w', encoding='utf-8') as f:
                    json.dump(summary_data, f, ensure_ascii=False, indent=2)
                logger.info(f"所有AI分析结果（含帖子数据）已保存到: {summary_file_path}")
            except Exception as e:
                logger.error(f"保存综合分析结果失败: {e}")
            
            logger.info("\nAI分析阶段完成")
            
            # ========== 3. 生成阶段 ==========
            logger.info(f"\n【第3步：文章生成】")
            
            try:
                generator = ArticleGenerator()
                html_file, screenshot_path = generator.generate_article(current_post_id)
                logger.info(f"文章HTML已生成: {html_file}")
                logger.info(f"使用截图: {screenshot_path}")
            except Exception as e:
                logger.error(f"文章生成失败: {e}")
                return False
            
            # ========== 4. 发布阶段 ==========
            if not skip_publish:
                logger.info(f"\n【第4步：微信发布】")
                
                try:
                    # 加载环境变量
                    from dotenv import load_dotenv
                    env_path = config.BASE_DIR / ".env"
                    if env_path.exists():
                        load_dotenv(dotenv_path=env_path)
                        logger.info("已加载.env配置文件")
                    
                    publisher = WechatPublisher()
                    publish_result = publisher.publish_article(current_post_id)
                    
                    if publish_result:
                        logger.info("微信公众号发布成功！")
                    else:
                        logger.error("微信公众号发布失败")
                        
                except Exception as e:
                    logger.error(f"发布过程出错: {e}")
                    return False
            else:
                logger.info("\n跳过发布步骤（--skip-publish参数）")
            
            # ========== 执行结果摘要 ==========
            logger.info("\n" + "="*60)
            logger.info("执行结果摘要")
            logger.info("="*60)
            logger.info(f"帖子ID: {current_post_id}")
            logger.info(f"发布时间: {scraped_data.get('time')}")
            logger.info(f"文本内容: {'有' if scraped_data.get('text') else '无'}")
            logger.info(f"图片数量: {len(scraped_data.get('images') or [])}")
            logger.info(f"视频: {'有' if scraped_data.get('videos') else '无'}")
            logger.info(f"截图: {'已保存' if scraped_data.get('screenshot') else '未生成'}")
            logger.info(f"AI分析: QWEN-{'✓' if ai_results.get('qwen') and 'error' not in ai_results['qwen'] else '✗'}, "
                       f"GROK-{'✓' if ai_results.get('grok') and 'error' not in ai_results['grok'] else '✗'}, "
                       f"GEMINI-{'✓' if ai_results.get('gemini') and 'error' not in ai_results['gemini'] else '✗'}")
            logger.info(f"文章生成: {'✓' if html_file else '✗'}")
            if not skip_publish:
                logger.info(f"微信发布: {'✓' if publish_result else '✗'}")
            logger.info("="*60 + "\n")
            
            return True
    
    except Exception as e:
        logger.error(f"流程运行出错: {str(e)}", exc_info=True)
        return False

def cleanup():
    """清理资源"""
    try:
        cleanup_browser()
    except Exception as e:
        logger.error(f"清理浏览器失败: {e}")

def continuous_run(interval_minutes, skip_publish=False):
    """持续运行爬虫，按指定间隔"""
    try:
        while True:
            run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"\n{'#'*60}")
            logger.info(f"# 新一轮执行开始: {run_time}")
            logger.info(f"{'#'*60}\n")
            
            success = run_scraper(skip_publish=skip_publish)
            
            logger.info(f"\n{'#'*60}")
            logger.info(f"# 本轮执行结束 ({'成功' if success else '失败'})")
            logger.info(f"# 等待 {interval_minutes} 分钟后再次运行...")
            logger.info(f"{'#'*60}\n")
            
            time.sleep(interval_minutes * 60)
            
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        cleanup()
    except Exception as e:
        logger.error(f"持续运行出错: {str(e)}", exc_info=True)
        cleanup()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="特朗普社交媒体爬虫及AI分析发布系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
业务流程：
  1. 采集 - 从Truth Social爬取特朗普最新帖子
  2. 分析 - 使用QWEN、GROK、GEMINI三个AI进行投资分析
  3. 生成 - 生成适合微信公众号的HTML文章
  4. 发布 - 创建草稿并自动发布到微信公众号

示例：
  python main.py --once                    # 运行一次完整流程
  python main.py --once --skip-publish     # 运行一次但跳过发布
  python main.py --interval 30             # 每30分钟运行一次

注意事项：
  - 发布后会自动轮询状态，确认发布是否成功
  - 发布成功后会返回文章链接
  - 如发布失败会显示具体失败原因
        """
    )
    
    parser.add_argument("--once", action="store_true", 
                       help="只运行一次完整流程（采集→分析→生成→发布）")
    parser.add_argument("--interval", type=int, default=30, 
                       help="持续运行时的间隔时间（分钟），默认30分钟")
    parser.add_argument("--skip-publish", action="store_true",
                       help="跳过微信发布步骤（仅采集、分析、生成）")
    
    args = parser.parse_args()
    
    # 初始化配置
    config.init()
    
    if args.once:
        logger.info("单次运行模式")
        run_scraper(once=True, skip_publish=args.skip_publish)
    else:
        logger.info(f"持续运行模式，间隔时间: {args.interval}分钟")
        continuous_run(args.interval, skip_publish=args.skip_publish)

if __name__ == "__main__":
    main()