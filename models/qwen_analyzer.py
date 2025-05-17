# ./models/qwen_analyzer.py
import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import dashscope

# 导入 dashscope SDK 中的 MultiModalConversation
from dashscope import MultiModalConversation

# 将项目根目录添加到sys.path，以便导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

logger = logging.getLogger(__name__)

# 加载 .env 文件
env_path = config.BASE_DIR / ".env"
if env_path.exists():
    logger.info(f"尝试加载 .env 文件: {env_path}")
    load_dotenv(dotenv_path=env_path, override=True) # 添加 override=True 确保覆盖已存在的环境变量
    logger.info(f".env 文件已处理。")
    logger.info(f"从 .env (直接os.environ) 读取 QWEN_MODEL_NAME: {os.environ.get('QWEN_MODEL_NAME')}") # 直接看加载后的环境变量
else:
    logger.warning(f".env 文件未在 {env_path} 找到。")

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
logger.info(f"获取到的 DASHSCOPE_API_KEY (通过 os.getenv): {DASHSCOPE_API_KEY}")

default_model_in_code = "qvq-max-latest" # 或者您代码中实际的默认值
logger.info(f"代码中 QWEN_MODEL_NAME 的默认值是: '{default_model_in_code}'")
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", default_model_in_code)
logger.info(f"最终使用的 QWEN_MODEL_NAME (通过 os.getenv 带默认值): '{QWEN_MODEL_NAME}'")

if not DASHSCOPE_API_KEY:
    logger.error("未找到 Dashscope API 密钥 (DASHSCOPE_API_KEY)，无法与通义千问交互。")

def format_media_and_text_for_qwen(scraped_post_data):
    """
    将采集到的帖子数据格式化为适合通义千问 MultiModalConversation 的内容列表。
    """
    content_list = []
    
    # 处理视频
    local_video_path_str = scraped_post_data.get("videos")
    if local_video_path_str:
        video_path = Path(local_video_path_str)
        if video_path.exists():
            content_list.append({'video': f"file://{video_path.resolve()}", "fps": 2}) # 使用 resolve() 获取绝对路径
            logger.info(f"视频文件已准备: file://{video_path.resolve()}")
        else:
            logger.warning(f"视频文件未找到，已跳过: {video_path}")

    # 处理图片 (如果视频不存在，则处理图片)
    # Qwen示例显示图片列表也用 'video' 键
    if not local_video_path_str: # 仅在没有视频时才将图片作为主要视觉内容
        local_image_paths = scraped_post_data.get("images")
        if local_image_paths and isinstance(local_image_paths, list):
            image_file_urls = []
            for img_path_str in local_image_paths:
                img_path = Path(img_path_str)
                if img_path.exists():
                    image_file_urls.append(f"file://{img_path.resolve()}")
                else:
                    logger.warning(f"图片文件未找到，已跳过: {img_path}")
            
            if image_file_urls:
                content_list.append({'video': image_file_urls, "fps": 2}) # 多张图片作为视频帧
                logger.info(f"图片文件已准备 (作为视频帧): {image_file_urls}")

    # 构建文本描述
    text_parts = []
    if scraped_post_data.get("text"):
        text_parts.append(scraped_post_data['text'])
    if scraped_post_data.get("url"):
        text_parts.append(f"相关链接: {scraped_post_data['url']}")
    
    text_description = "\n".join(text_parts)
    if not text_description.strip() and not content_list: # 如果完全没有内容
         text_description = "没有可供分析的文本、图片或视频内容。"

    if text_description.strip(): # 确保文本非空
        content_list.append({'text': text_description.strip()})

    if not content_list:
        logger.warning("没有有效的文本、图片或视频内容可以发送给模型。")
        return [{'text': "没有可分析的内容。"}] # 避免发送空内容

    return content_list

def analyze_content_with_qwen(scraped_post_data, system_prompt_text):
    if not DASHSCOPE_API_KEY:
        logger.error("Dashscope API Key 未配置，无法进行分析。")
        return None

    try:
        logger.info(f"向通义千问发送内容进行分析 (模型: {QWEN_MODEL_NAME})...")
        
        user_formatted_content = format_media_and_text_for_qwen(scraped_post_data)
        
        if not user_formatted_content or all(not part.get('text','').strip() and not part.get('video') for part in user_formatted_content):
            logger.error("格式化后的用户输入内容为空或无效，无法发送给通义千问。")
            return None

        messages = [
            {'role': 'system', 'content': [{'text': system_prompt_text}]},
            {'role': 'user', 'content': user_formatted_content}
        ]
        
        logger.debug(f"发送给通义千问 MultiModalConversation 的 messages: {json.dumps(messages, ensure_ascii=False, indent=2)}")

        response = MultiModalConversation.call(
            api_key=DASHSCOPE_API_KEY,
            model=QWEN_MODEL_NAME,
            messages=messages
        )

        if response.status_code == 200 and response.output and response.output.choices:
            analysis_result_str = response.output.choices[0].message.content[0].get("text", "")
            if not analysis_result_str: # 有时多模态返回内容可能在不同的结构
                 # 尝试查找其他可能包含文本的字段，或记录整个content
                alt_content = response.output.choices[0].message.content
                logger.warning(f"主要文本字段为空，检查备选内容: {alt_content}")
                # 尝试从第一个元素（如果是字典且有text）获取
                if isinstance(alt_content, list) and len(alt_content) > 0 and isinstance(alt_content[0], dict):
                    analysis_result_str = alt_content[0].get("text", "")

            logger.info("通义千问分析完成。")
            logger.debug(f"通义千问 MultiModalConversation 原始输出: {response}") # 记录整个响应对象

            if not analysis_result_str.strip():
                logger.error(f"通义千问返回的分析结果文本为空。响应详情: {response}")
                return None

            try:
                analysis_result_json = json.loads(analysis_result_str)
                return analysis_result_json
            except json.JSONDecodeError as e:
                logger.error(f"无法将通义千问的输出解析为JSON: '{analysis_result_str}'. 错误: {e}")
                logger.info("将返回原始文本结果。")
                # 对于无法解析为JSON的，可以考虑返回原始文本或特定错误结构
                # 根据项目需求，这里返回原始文本字符串
                return {"error": "Failed to parse Qwen response as JSON", "raw_response": analysis_result_str}
        else:
            logger.error(f"通义千问 API 调用失败。状态码: {response.status_code}, 响应: {response}")
            return None

    except Exception as e:
        logger.error(f"与通义千问 MultiModalConversation 交互时发生未知错误: {str(e)}", exc_info=True)
    return None

if __name__ == '__main__':
    config.init() # 初始化日志等配置

    system_prompt_path = config.BASE_DIR / "docs" / "system_prompt.md"
    try:
        with open(system_prompt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # 移除注释行并合并
            prompt_lines = [line for line in lines if not line.strip().startswith("#")]
            test_system_prompt = "".join(prompt_lines).strip()
            if not test_system_prompt:
                raise ValueError("system_prompt.md 文件内容为空或只有注释。")
    except FileNotFoundError:
        logger.error(f"未找到 system_prompt.md 文件于: {system_prompt_path}。使用默认提示。")
        test_system_prompt = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。" # 强化JSON要求
    except ValueError as e:
        logger.error(f"{e} 使用默认提示。")
        test_system_prompt = "你是一位金融分析师，请分析以下内容并以JSON格式返回结果，确保分析结果是一个合法的JSON对象。"

    latest_post_to_analyze = None
    if config.HISTORY_FILE.exists():
        try:
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
                if history and isinstance(history, list) and len(history) > 0:
                    latest_post_to_analyze = history[-1] 
                    logger.info(f"从 history.json 加载了最新的帖子 (ID: {latest_post_to_analyze.get('contentID')}) 进行分析。")
                else:
                    logger.warning("history.json 为空或格式不正确。")
        except Exception as e:
            logger.error(f"读取或解析 history.json 失败: {e}")
    else:
        logger.warning(f"history.json 文件未找到于: {config.HISTORY_FILE}")

    if latest_post_to_analyze:
        logger.info(f"准备分析的帖子数据: {json.dumps(latest_post_to_analyze, indent=2, ensure_ascii=False)}")
        
        analysis_result = analyze_content_with_qwen(latest_post_to_analyze, test_system_prompt)
        
        if analysis_result:
            logger.info("通义千问分析结果:")
            # analysis_result 现在可能是JSON对象或包含错误的字典
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
    else:
        logger.error("未能从 history.json 加载到最新的帖子进行分析。请先运行采集程序，确保 history.json 中有数据。")
