# scraper.py
import re
import json
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

import config
from downloader import download_media

# 获取logger
logger = logging.getLogger(__name__)

def fetch_page():
    """
    使用Playwright获取Truth Social页面内容
    
    Returns:
        BeautifulSoup: 解析后的页面，失败则返回None
    """
    try:
        logger.info(f"开始获取页面: {config.TARGET_URL}")
        
        with sync_playwright() as p:
            # 启动可见的浏览器
            browser = p.chromium.launch(
                headless=False,  # 保持浏览器可见
                proxy={"server": "socks5://127.0.0.1:10808"},
                slow_mo=300  # 放慢操作，更容易观察
            )
            
            page = browser.new_page(ignore_https_errors=True)
            page.goto(config.TARGET_URL, wait_until="networkidle")
            
            # 等待内容加载 - 更新为实际页面中帖子的选择器
            try:
                page.wait_for_selector("div[data-testid='status']", timeout=10000)
                logger.info("帖子内容已加载")
            except Exception as e:
                logger.error(f"等待帖子超时: {str(e)}")
            
            # 获取页面内容
            html = page.content()
            
            # 可选：截图保存
            page.screenshot(path="page_screenshot.png")
            
            browser.close()
            
            soup = BeautifulSoup(html, 'html.parser')
            logger.info("页面获取成功")
            return soup
    
    except Exception as e:
        logger.error(f"获取页面失败: {str(e)}")
        return None

def extract_post_info(soup):
    """
    从页面中提取最新帖子信息
    
    Args:
        soup (BeautifulSoup): 解析后的页面
        
    Returns:
        dict: 帖子信息，包含ID、时间、文本、图片URL和视频URL
    """
    try:
        # 找到第一个帖子 - 根据实际页面结构更新
        post = soup.select_one("div[data-testid='status']")
        if not post:
            logger.error("未找到帖子")
            return None
        
        # 提取内容ID
        post_link = post.select_one('a[href*="/posts/"]')
        if not post_link:
            # 检查另一种格式的链接
            post_link = post.select_one('a[href*="/@realDonaldTrump/posts/"]')
            
        if not post_link:
            logger.error("未找到帖子链接")
            return None
            
        href = post_link.get('href', '')
        content_id = re.search(r'/posts/(\d+)', href)
        if not content_id:
            logger.error(f"无法从链接中提取内容ID: {href}")
            return None
        content_id = content_id.group(1)
        
        # 提取时间
        time_element = post.select_one("time")
        if not time_element:
            logger.error("未找到时间元素")
            return None
            
        time_str = time_element.get('title', '')
        try:
            # 解析时间格式 "May 04, 2025, 11:47 AM"
            post_time = datetime.strptime(time_str, "%b %d, %Y, %I:%M %p")
            formatted_time = post_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"时间解析错误: {str(e)}")
            formatted_time = time_str
        
        # 提取文本内容
        text_element = post.select_one("p[data-markup='true']")
        text_content = text_element.get_text(strip=True) if text_element else None
        if text_content == "":
            text_content = None

        # 提取URL链接
        url_link = None
        if text_element:
            link_element = text_element.select_one("a[href]")
            if link_element and 'href' in link_element.attrs:
                url_link = link_element['href']
                # 确保是完整URL
                if not url_link.startswith(('http://', 'https://')):
                    url_link = f"https://truthsocial.com{url_link}"

        # 提取图片URL
        image_urls = []
        image_containers = post.select("div[data-testid='still-image-container']")
        for container in image_containers:
            # 过滤掉头像和其他界面元素的图片
            if 'rounded-full' in container.get('class', []):
                continue
                
            img = container.select_one("img")
            if img and 'src' in img.attrs:
                image_url = img['src']
                # 确保使用完整URL
                if not image_url.startswith(('http://', 'https://')):
                    if image_url.startswith('./'):
                        image_url = image_url[2:]
                    # 为相对URL添加域名
                    image_url = f"https://truthsocial.com/{image_url}"
                image_urls.append(image_url)
        
        # 提取视频URL
        video_element = post.select_one("video source[type='video/mp4']")
        if not video_element:
            video_element = post.select_one("source[type='video/mp4'][data-quality='480p']")
            
        video_url = video_element['src'] if video_element else None
        
        return {
            "contentID": content_id,
            "time": formatted_time,
            "text": text_content,
            "url": url_link,
            "image_urls": image_urls,
            "video_url": video_url
        }
        
    except Exception as e:
        logger.error(f"提取帖子信息失败: {str(e)}")
        return None

def process_post(post_info):
    """
    处理帖子信息，下载媒体文件并保存结果
    
    Args:
        post_info (dict): 帖子信息
        
    Returns:
        dict: 处理后的帖子数据
    """
    if not post_info:
        return None
        
    try:
        content_id = post_info["contentID"]
        
        # 下载媒体文件
        image_paths, video_path = download_media(
            content_id,
            image_urls=post_info.get("image_urls", []),
            video_url=post_info.get("video_url")
        )
        
        # 构建结果数据
        result = {
            "contentID": content_id,
            "time": post_info["time"],
            "text": post_info.get("text"),
            "url": post_info.get("url"),
            "images": image_paths if image_paths else None,
            "videos": video_path if video_path else None
        }
        
        # 保存到JSON文件
        save_post_data(result)
        
        return result
        
    except Exception as e:
        logger.error(f"处理帖子失败: {str(e)}")
        return None

def save_post_data(post_data):
    """
    保存帖子数据到JSON文件
    
    Args:
        post_data (dict): 帖子数据
    """
    try:
        # 检查历史记录文件是否存在
        history_exists = config.HISTORY_FILE.exists()
        
        # 读取现有历史记录
        if history_exists:
            with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        else:
            history = []
            
        # 检查是否已存在相同内容ID的记录
        exists = False
        for i, item in enumerate(history):
            if item.get('contentID') == post_data['contentID']:
                # 更新现有记录
                history[i] = post_data
                exists = True
                break
                
        # 如果是新记录，添加到历史记录
        if not exists:
            history.append(post_data)
            
        # 保存更新后的历史记录
        with open(config.HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
        logger.info(f"保存帖子数据成功: {post_data['contentID']}")
        
    except Exception as e:
        logger.error(f"保存帖子数据失败: {str(e)}")

def scrape_latest_post():
    """
    抓取最新的帖子信息并处理
    
    Returns:
        dict: 处理后的帖子数据，失败则返回None
    """
    # 确保配置初始化
    config.init()
    
    # 获取页面
    soup = fetch_page()
    if not soup:
        return None
        
    # 提取帖子信息
    post_info = extract_post_info(soup)
    if not post_info:
        return None
        
    # 处理帖子
    result = process_post(post_info)
    return result

# 测试
if __name__ == "__main__":
    config.init()
    result = scrape_latest_post()
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("抓取失败")
