import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
import google.generativeai as genai
from datetime import datetime

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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# 使用支持更多功能的模型
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")

logger.info(f"获取到的 GEMINI_API_KEY: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "未找到GEMINI_API_KEY")
logger.info(f"使用的 GEMINI_MODEL_NAME: {GEMINI_MODEL_NAME}")

if not GEMINI_API_KEY:
    logger.error("未找到 GEMINI API 密钥 (GEMINI_API_KEY)，无法与GEMINI交互。")
else:
    genai.configure(api_key=GEMINI_API_KEY)

def format_content_for_gemini(scraped_post_data):
    """
    将采集到的帖子数据格式化为适合GEMINI的内容
    """
    content_parts = []
    
    # 添加文本内容
    text_content = scraped_post_data.get("text")
    if text_content and isinstance(text_content, str) and text_content.strip():
        content_parts.append(f"文本内容: {text_content.strip()}")
    
    # 添加URL链接
    url_content = scraped_post_data.get("url")
    if url_content and isinstance(url_content, str) and url_content.strip() and url_content != "null":
        content_parts.append(f"相关链接: {url_content}")
    
    # 处理图片（GEMINI支持图片分析）
    images = scraped_post_data.get("images")
    if images and images != "null" and isinstance(images, list):
        content_parts.append(f"包含图片: {len(images)}张")
        # 注意：这里可以扩展为实际上传图片到GEMINI进行分析
    
    # 处理视频
    videos = scraped_post_data.get("videos")
    if videos and videos != "null" and isinstance(videos, str):
        content_parts.append("包含视频: 1个")
    
    if not content_parts:
        return "没有可供分析的内容。"
    
    return "\n".join(content_parts)

def analyze_content_with_gemini(scraped_post_data, system_prompt_text):
    """
    使用GEMINI分析内容
    """
    if not GEMINI_API_KEY:
        logger.error("GEMINI API Key 未配置，无法进行分析。")
        return None

    try:
        logger.info(f"向GEMINI发送内容进行分析 (模型: {GEMINI_MODEL_NAME})...")
        
        # 格式化内容
        user_content = format_content_for_gemini(scraped_post_data)
        
        # 在系统提示词中强调JSON格式要求
        enhanced_system_prompt = f"""{system_prompt_text}

重要格式要求：
1. 必须以完整的JSON格式返回分析结果
2. 即使判断内容与中国股市无关，也要按照完整的JSON格式返回
3. 不要返回纯文本，必须是有效的JSON对象
4. 如果相关性低，请在JSON中的"市场相关性"字段标注为"低"，在"个股建议"中返回空数组[]
5. 请进行深度思考分析
6. 请主动搜索相关的最新股票信息和市场数据"""
        
        # 创建模型实例
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL_NAME,
            system_instruction=enhanced_system_prompt
        )
        
        # 简化的生成参数配置
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            top_p=0.8,
            top_k=40,
            max_output_tokens=8192,
            response_mime_type="application/json"  # 只强制JSON格式
        )
        
        # 构建完整的提示，包含JSON格式示例
        full_prompt = f"""请分析以下特朗普社交媒体内容对中国A股市场的影响：

{user_content}

请严格按照以下JSON格式返回结果：
{{
    "分析时间": "2025-05-25 18:12:00",
    "特朗普言论摘要": "核心内容概括",
    "市场相关性": "高/中/低",
    "综合评分": "+XX%或-XX%",
    "影响分析": {{
        "直接影响": "具体说明",
        "影响路径": "传导链条",
        "影响时限": "短期/中期/长期",
        "影响强度": "重大/中等/轻微"
    }},
    "搜索发现": {{
        "关键信息": ["信息1", "信息2"],
        "数据来源": ["来源1", "来源2"]
    }},
    "个股建议": [],
    "风险提示": "风险提示内容",
    "思维链": "完整的分析推理过程"
}}

请确保返回的是有效的JSON格式。"""
        
        # 发送请求
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        if response.text:
            analysis_result_str = response.text
            
            logger.info("GEMINI分析完成。")
            logger.debug(f"GEMINI原始输出: {response}")
            
            try:
                # 直接解析JSON
                analysis_result_json = json.loads(analysis_result_str)
                logger.info("GEMINI JSON解析成功")
                return analysis_result_json
                
            except json.JSONDecodeError as e:
                logger.error(f"无法将GEMINI的输出解析为JSON: '{analysis_result_str[:500]}...'. 错误: {e}")
                # 创建fallback JSON
                fallback_json = {
                    "error": "Failed to parse GEMINI response as JSON",
                    "raw_response": analysis_result_str,
                    "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "市场相关性": "解析失败",
                    "综合评分": "0%",
                    "影响分析": {
                        "直接影响": "JSON解析失败",
                        "影响路径": "无法解析",
                        "影响时限": "无",
                        "影响强度": "无"
                    },
                    "搜索发现": {
                        "关键信息": [],
                        "数据来源": []
                    },
                    "个股建议": [],
                    "风险提示": "本分析因JSON解析失败，结果可能不准确。",
                    "思维链": analysis_result_str
                }
                return fallback_json
        else:
            logger.error("GEMINI返回空响应")
            return {
                "error": "GEMINI returned empty response",
                "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "市场相关性": "无响应",
                "综合评分": "0%"
            }

    except Exception as e:
        logger.error(f"与GEMINI交互时发生未知错误: {str(e)}", exc_info=True)
        return {
            "error": f"GEMINI interaction error: {str(e)}",
            "分析时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "市场相关性": "错误",
            "综合评分": "0%"
        } 