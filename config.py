# config.py
import os
import logging
from pathlib import Path

# URL配置
TARGET_URL = "https://truthsocial.com/@realDonaldTrump"

# 请求头配置，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive"
}

# 请求超时设置（秒）
REQUEST_TIMEOUT = 30

# 文件路径配置
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PICS_DIR = BASE_DIR / "pics"
MOVS_DIR = BASE_DIR / "movs"
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
RESULT_DIR = DATA_DIR / "result" # 新增，用于存放AI分析结果
SCREENSHOTS_DIR = BASE_DIR / "screenshots"  # 新增：截图目录
BROWSER_USER_DATA_DIR = BASE_DIR / "browser_data"  # 新增：浏览器用户数据目录

# 浏览器配置 - 新增
BROWSER_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "viewport": {"width": 1920, "height": 1080},
    "locale": "en-US",
    "timezone": "America/New_York"
}

# 浏览器模式配置 - 新增
# 可以通过环境变量 USE_UNDETECTED_CHROME=true/false 来控制
USE_UNDETECTED_CHROME = os.getenv('USE_UNDETECTED_CHROME', 'true').lower() == 'true'

# HTML选择器
SELECTORS = {
    "post": "div[data-testid='status']",  # 帖子选择器
    "pinned_indicator": "div[role='status-info']",  # 置顶标记选择器
    "time": "time",
    "text": "p[data-markup='true']",
    "image_container": "div[data-testid='still-image-container']",
    "image": "img",
    "video_480p": "source[type='video/mp4'][data-quality='480p']",
    "video_generic": "video source[type='video/mp4']",
    "post_link_primary": 'a[href*="/posts/"]',
    "post_link_secondary": 'a[href*="/@realDonaldTrump/posts/"]',
    "text_embedded_link": "a[href]",
}

# 日志配置
LOG_LEVEL = logging.INFO

# 确保必要的目录存在
def ensure_dirs():
    """创建必要的目录结构"""
    for directory in [PICS_DIR, MOVS_DIR, DATA_DIR, RESULT_DIR, SCREENSHOTS_DIR, BROWSER_USER_DATA_DIR]:
        directory.mkdir(exist_ok=True)

# 配置日志格式
def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # 输出到控制台
            logging.FileHandler(BASE_DIR / "trump_social.log", encoding='utf-8')  # 输出到文件
        ]
    )

# 初始化函数
def init():
    """初始化配置"""
    ensure_dirs()
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("配置初始化完成")
    logger.info(f"图片保存路径: {PICS_DIR}")
    logger.info(f"视频保存路径: {MOVS_DIR}")
    logger.info(f"数据保存路径: {DATA_DIR}")
    logger.info(f"浏览器模式: {'undetected-chromedriver' if USE_UNDETECTED_CHROME else 'playwright'}")

# 当这个模块被导入时自动初始化
if __name__ == "__main__":
    init()
