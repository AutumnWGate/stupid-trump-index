# ./models/qwen_analyzer.py
import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import dashscope

# 导入 dashscope SDK 中的 MultiModalConversation
from dashscope import MultiModalConversation, Generation

# 将项目根目录添加到sys.path，以便导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

# 加载 .env 文件
env_path = config.BASE_DIR / ".env"
if env_path.exists():
    logger.info(f"尝试加载 .env 文件: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True)
    logger.info(f".env 文件已处理。")
else:
    logger.warning(f".env 文件未在 {env_path} 找到。")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
logger.info(f"获取到的 DASHSCOPE_API_KEY (通过 os.getenv): {DASHSCOPE_API_KEY}")

# 模型配置
default_text_model = "qwen-max"  # 文本使用
default_video_model = "qwen2.5-vl-72b-instruct"  # 视频和图片使用

QWEN_TEXT_MODEL = os.getenv("QWEN_MODEL_NAME", default_text_model)
QWEN_VIDEO_MODEL = os.getenv("QWEN_VIDEO_MODEL_NAME", default_video_model)

logger.info(f"文本模型: '{QWEN_TEXT_MODEL}'")
logger.info(f"视觉模型(图片/视频): '{QWEN_VIDEO_MODEL}'")

if not DASHSCOPE_API_KEY:
    logger.error("未找到 Dashscope API 密钥 (DASHSCOPE_API_KEY)，无法与通义千问交互。")

def format_media_and_text_for_qwen(scraped_post_data):
    """
    将采集到的帖子数据格式化为适合通义千问 MultiModalConversation 的内容列表。
    返回：(content_list, media_type) 其中 media_type 为 'video', 'image', 'text'
    """
    content_list = []
    media_type = 'text'
    
    # 优先处理视频
    local_video_path_str = scraped_post_data.get("videos")
    if local_video_path_str and local_video_path_str != "null" and isinstance(local_video_path_str, str):
        video_path = Path(local_video_path_str)
        if video_path.exists() and video_path.is_file():
            try:
                # 使用绝对路径
                absolute_path = video_path.resolve()
                video_url = f"file://{absolute_path}"
                content_list.append({'video': video_url, "fps": 2})  # fps=2 表示每0.5秒抽一帧
                media_type = 'video'
                logger.info(f"视频文件已准备: {video_url}")
            except Exception as e:
                logger.warning(f"处理视频文件时出错: {e}")
        else:
            logger.warning(f"视频文件未找到或不是有效文件: {video_path}")

    # 如果没有视频，处理图片
    if media_type == 'text':
        local_image_paths = scraped_post_data.get("images")
        if local_image_paths and local_image_paths != "null" and isinstance(local_image_paths, list):
            image_urls = []
            for img_path_str in local_image_paths:
                if img_path_str and isinstance(img_path_str, str):
                    img_path = Path(img_path_str)
                    if img_path.exists() and img_path.is_file():
                        try:
                            # 使用绝对路径
                            absolute_path = img_path.resolve()
                            image_url = f"file://{absolute_path}"
                            image_urls.append(image_url)
                        except Exception as e:
                            logger.warning(f"处理图片文件时出错: {e}")
                    else:
                        logger.warning(f"图片文件未找到或不是有效文件: {img_path}")
            
            if image_urls:
                # 将图片作为视频帧处理
                content_list.append({'video': image_urls, "fps": 2})
                media_type = 'image'
                logger.info(f"图片文件已准备 (作为视频帧): {len(image_urls)}张")

    # 构建文本描述
    text_parts = []
    text_content = scraped_post_data.get("text")
    if text_content and isinstance(text_content, str) and text_content.strip():
        text_parts.append(text_content.strip())
    
    url_content = scraped_post_data.get("url")
    if url_content and isinstance(url_content, str) and url_content.strip() and url_content != "null":
        text_parts.append(f"相关链接: {url_content}")
    
    text_description = "\n".join(text_parts)
    
    # 如果完全没有内容，提供默认文本
    if not text_description.strip() and media_type == 'text':
        text_description = "没有可供分析的文本、图片或视频内容。"

    # 添加文本内容
    if text_description.strip():
        content_list.append({'text': text_description.strip()})

    return content_list, media_type

def analyze_content_with_qwen(scraped_post_data, system_prompt_text):
    if not DASHSCOPE_API_KEY:
        logger.error("Dashscope API Key 未配置，无法进行分析。")
        return None

    try:
        logger.info("向通义千问发送内容进行分析...")
        
        user_formatted_content, media_type = format_media_and_text_for_qwen(scraped_post_data)
        
        if not user_formatted_content:
            logger.error("格式化后的用户输入内容为空或无效，无法发送给通义千问。")
            return None

        # 根据媒体类型选择模型
        if media_type in ['video', 'image']:  # 图片和视频都使用视觉模型
            model_name = QWEN_VIDEO_MODEL
            logger.info(f"检测到视频内容，使用视频模型: {model_name}")
        else:
            model_name = QWEN_TEXT_MODEL
            logger.info(f"检测到{media_type}内容，使用文本/图片模型: {model_name}")

        # 如果是纯文本，使用Generation API
        if media_type == 'text' and all(part.get('text') for part in user_formatted_content):
            logger.info("使用Generation API处理纯文本")
            
            # 提取纯文本内容
            text_content = ""
            for part in user_formatted_content:
                if part.get('text'):
                    text_content += part['text'] + "\n"
            
            messages = [
                {'role': 'system', 'content': system_prompt_text},
                {'role': 'user', 'content': text_content.strip()}
            ]
            
            response = Generation.call(
                api_key=DASHSCOPE_API_KEY,
                model=model_name,
                messages=messages,
                result_format='message',
                enable_search=True,  # 启用联网搜索
                search_options={
                    "forced_search": True  # 强制搜索
                },
                enable_thinking=True,  # 启用思维链功能
                thinking_budget=10000,  # 思考过程的最大长度
                response_format={"type": "json_object"}  # 强制JSON格式输出
            )
            
        else:
            # 使用多模态API处理视频/图片
            logger.info("使用MultiModalConversation API处理多媒体")
            messages = [
                {'role': 'system', 'content': [{'text': system_prompt_text}]},
                {'role': 'user', 'content': user_formatted_content}
            ]
            
            # 多模态API使用extra_body传递参数
            response = MultiModalConversation.call(
                api_key=DASHSCOPE_API_KEY,
                model=model_name,
                messages=messages,
                extra_body={
                    "enable_search": True,  # 启用联网搜索
                    "search_options": {
                        "forced_search": True  # 强制搜索
                    },
                    "enable_thinking": True,  # 启用思维链
                    "thinking_budget": 10000,
                    "response_format": {"type": "json_object"}  # JSON格式输出
                }
            )

        # 统一处理响应
        if response.status_code == 200 and response.output:
            analysis_result_str = None
            
            # 尝试从不同的响应格式中提取内容
            if hasattr(response.output, 'choices') and response.output.choices:
                choice = response.output.choices[0]
                
                # Generation API 响应
                if hasattr(choice, 'message'):
                    message = choice.message
                    if hasattr(message, 'content'):
                        analysis_result_str = message.content
                    elif isinstance(message, dict) and 'content' in message:
                        analysis_result_str = message['content']
                    
                # MultiModalConversation API 响应
                elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    message_content = choice.message.content
                    if isinstance(message_content, list) and len(message_content) > 0:
                        analysis_result_str = message_content[0].get("text", "")
                    else:
                        analysis_result_str = str(message_content)
            
            # 如果还是没有获取到，尝试其他方式
            if not analysis_result_str:
                if hasattr(response.output, 'text'):
                    analysis_result_str = response.output.text
                else:
                    analysis_result_str = str(response.output)
            
            if not analysis_result_str:
                logger.error("API返回的分析结果为空")
                return None
                
            logger.info("API调用成功，开始解析结果")
            logger.debug(f"原始响应: {analysis_result_str[:500]}...")
            
            try:
                # 清理可能的markdown格式
                cleaned_response = analysis_result_str.strip()
                
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                elif cleaned_response.startswith('```'):
                    lines = cleaned_response.split('\n')
                    if len(lines) > 1:
                        cleaned_response = '\n'.join(lines[1:])
                        if cleaned_response.endswith('```'):
                            cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                
                # 尝试解析JSON
                analysis_result_json = json.loads(cleaned_response)
                logger.info("JSON解析成功")
                return analysis_result_json
                
            except json.JSONDecodeError as e:
                logger.error(f"无法将输出解析为JSON: {e}")
                logger.info("返回默认结构")
                return {
                    "error": "Failed to parse response as JSON",
                    "raw_response": analysis_result_str,
                    "综合评分": "0%",
                    "市场相关性": "无法分析",
                    "影响分析": {
                        "直接影响": "分析失败",
                        "影响路径": "分析失败",
                        "影响时限": "分析失败",
                        "影响强度": "分析失败"
                    },
                    "风险提示": "由于技术原因无法完成分析"
                }
        else:
            logger.error(f"API调用失败。状态码: {response.status_code}")
            if hasattr(response, 'code'):
                logger.error(f"错误代码: {response.code}")
            if hasattr(response, 'message'):
                logger.error(f"错误信息: {response.message}")
            return None

    except Exception as e:
        logger.error(f"与通义千问交互时发生未知错误: {str(e)}", exc_info=True)
    return None

if __name__ == '__main__':
    config.init()

    system_prompt_path = config.BASE_DIR / "docs" / "system_prompt.md"
    try:
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            test_system_prompt = f.read().strip()
    except FileNotFoundError:
        logger.error(f"未找到 system_prompt.md 文件")
        test_system_prompt = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果。"

    latest_post_to_analyze = None
    if config.HISTORY_FILE.exists():
        try:
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                if history and isinstance(history, list) and len(history) > 0:
                    latest_post_to_analyze = history[-1]
                    logger.info(f"从 history.json 加载了最新的帖子 (ID: {latest_post_to_analyze.get('contentID')})")
        except Exception as e:
            logger.error(f"读取 history.json 失败: {e}")

    if latest_post_to_analyze:
        analysis_result = analyze_content_with_qwen(latest_post_to_analyze, test_system_prompt)
        
        if analysis_result:
            logger.info("通义千问分析结果:")
            logger.info(json.dumps(analysis_result, indent=2, ensure_ascii=False))
            
            result_file_name = f"{latest_post_to_analyze['contentID']}_qwen.json"
            result_file_path = config.RESULT_DIR / result_file_name
            try:
                with open(result_file_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, ensure_ascii=False, indent=2)
                logger.info(f"分析结果已保存到: {result_file_path}")
            except Exception as e:
                logger.error(f"保存分析结果失败: {e}")
        else:
            logger.error("通义千问分析失败或未返回有效结果。")
