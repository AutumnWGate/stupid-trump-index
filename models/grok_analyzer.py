import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
import sys
from openai import OpenAI  # 使用OpenAI SDK

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

# 注意：根据文档，环境变量应该是XAI_API_KEY
XAI_API_KEY = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")  # 兼容两种命名
GROK_MODEL_NAME = os.getenv("GROK_MODEL_NAME", "grok-2-1212")  # 使用最新模型

logger.info(f"获取到的 XAI_API_KEY: {XAI_API_KEY[:10]}..." if XAI_API_KEY else "未找到XAI_API_KEY")
logger.info(f"使用的 GROK_MODEL_NAME: {GROK_MODEL_NAME}")

if not XAI_API_KEY:
    logger.error("未找到 XAI API 密钥 (XAI_API_KEY 或 GROK_API_KEY)，无法与GROK交互。")

def format_content_for_grok(scraped_post_data):
    """
    将采集到的帖子数据格式化为适合GROK的文本内容
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
    
    # 添加媒体信息
    images = scraped_post_data.get("images")
    if images and images != "null" and isinstance(images, list):
        content_parts.append(f"包含图片: {len(images)}张")
    
    videos = scraped_post_data.get("videos")
    if videos and videos != "null" and isinstance(videos, str):
        content_parts.append("包含视频: 1个")
    
    if not content_parts:
        return "没有可供分析的内容。"
    
    return "\n".join(content_parts)

def analyze_content_with_grok(scraped_post_data, system_prompt_text):
    """
    使用GROK分析内容，启用Live Search、Structured Outputs和Reasoning
    """
    if not XAI_API_KEY:
        logger.error("XAI API Key 未配置，无法进行分析。")
        return None

    try:
        logger.info(f"向GROK发送内容进行分析 (模型: {GROK_MODEL_NAME})...")
        logger.info("启用功能: Live Search + Structured Outputs + Reasoning")
        
        # 格式化内容
        user_content = format_content_for_grok(scraped_post_data)
        
        # 使用OpenAI SDK连接GROK API
        client = OpenAI(
            api_key=XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )
        
        # 增强系统提示词，启用推理模式和搜索
        enhanced_system_prompt = f"""{system_prompt_text}

重要指令：
1. 请使用推理模式(Reasoning)进行深度思考和分析
2. 请使用实时搜索(Live Search)获取最新的股票信息和市场数据
3. 必须以结构化JSON格式返回分析结果
4. 在分析过程中展示你的推理步骤和搜索发现

分析要求：
- 搜索相关公司的最新股价、财务数据和新闻
- 搜索中美关系、教育政策的最新动态
- 搜索A股市场的当前状况和趋势
- 基于搜索结果进行深度推理分析"""
        
        # 定义结构化输出的JSON Schema
        json_schema = {
            "type": "object",
            "properties": {
                "分析时间": {"type": "string"},
                "特朗普言论摘要": {"type": "string"},
                "市场相关性": {"type": "string", "enum": ["高", "中", "低"]},
                "综合评分": {"type": "string"},
                "推理过程": {
                    "type": "object",
                    "properties": {
                        "初步分析": {"type": "string"},
                        "搜索发现": {"type": "string"},
                        "深度推理": {"type": "string"},
                        "结论推导": {"type": "string"}
                    },
                    "required": ["初步分析", "搜索发现", "深度推理", "结论推导"]
                },
                "影响分析": {
                    "type": "object",
                    "properties": {
                        "直接影响": {"type": "string"},
                        "影响路径": {"type": "string"},
                        "影响时限": {"type": "string"},
                        "影响强度": {"type": "string"}
                    },
                    "required": ["直接影响", "影响路径", "影响时限", "影响强度"]
                },
                "搜索发现": {
                    "type": "object",
                    "properties": {
                        "关键信息": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "数据来源": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "最新股价": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["关键信息", "数据来源", "最新股价"]
                },
                "个股建议": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "股票代码": {"type": "string"},
                            "股票名称": {"type": "string"},
                            "所属行业": {"type": "string"},
                            "当前价格": {"type": "string"},
                            "交易建议": {"type": "string"},
                            "目标价位": {"type": "string"},
                            "预期收益": {"type": "string"},
                            "操作逻辑": {"type": "string"},
                            "置信度": {"type": "string"}
                        }
                    }
                },
                "风险提示": {"type": "string"},
                "思维链": {"type": "string"}
            },
            "required": ["分析时间", "特朗普言论摘要", "市场相关性", "综合评分", "推理过程", "影响分析", "搜索发现", "个股建议", "风险提示", "思维链"]
        }
        
        # 发送请求，启用所有高级功能
        completion = client.chat.completions.create(
            model=GROK_MODEL_NAME,
            messages=[
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": user_content}
            ],
            temperature=0.1,
            max_tokens=8192,
            # 启用结构化输出
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "stock_analysis",
                    "schema": json_schema,
                    "strict": True
                }
            },
            # 启用实时搜索
            extra_body={
                "search": True,  # 启用Live Search
                "reasoning": True  # 启用Reasoning模式
            }
        )
        
        if completion.choices and len(completion.choices) > 0:
            analysis_result_str = completion.choices[0].message.content
            
            logger.info("GROK分析完成。")
            logger.debug(f"GROK原始输出: {completion}")
            
            # 检查是否有推理过程
            if hasattr(completion.choices[0].message, 'reasoning') and completion.choices[0].message.reasoning:
                logger.info(f"GROK推理过程: {completion.choices[0].message.reasoning[:200]}...")
            
            try:
                # 由于使用了结构化输出，应该直接是有效的JSON
                analysis_result_json = json.loads(analysis_result_str)
                logger.info("GROK JSON解析成功")
                
                # 记录搜索和推理信息
                if "搜索发现" in analysis_result_json:
                    search_info = analysis_result_json["搜索发现"]
                    logger.info(f"GROK搜索发现: {len(search_info.get('关键信息', []))}条关键信息")
                
                if "推理过程" in analysis_result_json:
                    logger.info("GROK推理过程已包含在结果中")
                
                return analysis_result_json
                
            except json.JSONDecodeError as e:
                logger.error(f"无法将GROK的输出解析为JSON: '{analysis_result_str[:500]}...'. 错误: {e}")
                return {
                    "error": "Failed to parse GROK response as JSON", 
                    "raw_response": analysis_result_str,
                    "分析时间": "解析失败",
                    "市场相关性": "解析失败",
                    "综合评分": "0%"
                }
        else:
            logger.error("GROK响应格式异常")
            return {
                "error": "GROK response format error",
                "分析时间": "响应异常",
                "市场相关性": "响应异常", 
                "综合评分": "0%"
            }

    except Exception as e:
        logger.error(f"与GROK交互时发生未知错误: {str(e)}", exc_info=True)
        return {
            "error": f"GROK interaction error: {str(e)}",
            "分析时间": "交互错误",
            "市场相关性": "交互错误",
            "综合评分": "0%"
        } 