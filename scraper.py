# scraper.py
import re
import json
import logging
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import atexit
import random
import time as time_module

import config
from downloader import download_media

# 获取logger
logger = logging.getLogger(__name__)

# 全局浏览器实例
_browser = None
_context = None
_page = None
_playwright = None

def init_browser():
    """初始化浏览器实例"""
    global _browser, _context, _page, _playwright
    
    if _browser is None:
        logger.info("初始化浏览器...")
        _playwright = sync_playwright().start()
        
        # 创建用户数据目录路径
        user_data_dir = str(config.BROWSER_USER_DATA_DIR)
        
        # 启动浏览器参数
        launch_args = [
            '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
            '--disable-infobars',  # 禁用信息栏
            '--disable-dev-shm-usage',  # 解决资源限制问题
            '--no-sandbox',  # 在某些环境下需要
            '--disable-web-security',  # 禁用同源策略（谨慎使用）
            '--disable-features=IsolateOrigins,site-per-process',  # 禁用站点隔离
            '--flag-switches-begin',
            '--disable-site-isolation-trials',
            '--flag-switches-end',
            f'--user-agent={config.BROWSER_CONFIG["user_agent"]}',  # 设置用户代理
            '--start-maximized',  # 最大化窗口
            '--disable-gpu',  # 禁用GPU加速（某些环境需要）
            '--lang=en-US',  # 设置语言
            '--disable-background-timer-throttling',  # 禁用后台标签页限制
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',  # 禁用翻译提示
            '--disable-ipc-flooding-protection',
            '--disable-default-apps',
            '--no-first-run',  # 跳过首次运行
            '--password-store=basic',  # 密码存储
            '--use-mock-keychain',
        ]
        
        # 启动浏览器（使用持久化的用户数据）
        _browser = _playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,  # 保持浏览器可见
            proxy={"server": "socks5://127.0.0.1:10808"},
            args=launch_args,
            viewport=config.BROWSER_CONFIG["viewport"],
            locale=config.BROWSER_CONFIG["locale"],
            timezone_id=config.BROWSER_CONFIG["timezone"],
            user_agent=config.BROWSER_CONFIG["user_agent"],
            ignore_https_errors=True,
            # 添加更多真实浏览器的设置
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            accept_downloads=True,
            # 权限设置
            permissions=["geolocation", "notifications"],
            # 绕过CSP
            bypass_csp=True,
            # 启用服务工作者
            service_workers="allow",
            # 颜色方案
            color_scheme="light",
            # 减少运动
            reduced_motion="no-preference",
            # 强制颜色
            forced_colors="none",
        )
        
        # 获取第一个页面或创建新页面
        if _browser.pages:
            _page = _browser.pages[0]
        else:
            _page = _browser.new_page()
            
        # 注入一些JavaScript来进一步隐藏自动化特征
        _page.add_init_script("""
            // 重写navigator.webdriver属性
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 修改navigator.plugins使其看起来更真实
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format", 
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ]
            });
            
            // 修改权限查询
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 修改chrome对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 修改语言相关属性
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // 时区欺骗
            Date.prototype.getTimezoneOffset = function() { return 300; }; // EST时区
        """)
        
        logger.info("浏览器初始化完成（使用持久化用户数据）")
        
        # 注册退出时的清理函数
        atexit.register(cleanup_browser)
    
    return _page

def cleanup_browser():
    """清理浏览器资源"""
    global _browser, _context, _page, _playwright
    
    logger.info("清理浏览器资源...")
    # 注意：使用 launch_persistent_context 时，browser 就是 context
    if _browser:
        _browser.close()
        _browser = None
        _page = None
    if _playwright:
        _playwright.stop()
        _playwright = None
    logger.info("浏览器资源已清理")

def fetch_page_and_screenshot():
    """
    使用Playwright获取Truth Social页面内容并截图
    
    Returns:
        tuple: (BeautifulSoup对象, 截图路径)，失败则返回(None, None)
    """
    try:
        # 获取或初始化浏览器页面
        page = init_browser()
        
        # 添加随机延迟，模拟人类行为
        time_module.sleep(random.uniform(1, 3))
        
        # 检查是否已经在目标页面
        current_url = page.url
        if current_url.startswith(config.TARGET_URL):
            logger.info(f"刷新页面: {config.TARGET_URL}")
            # 随机选择刷新方式
            if random.choice([True, False]):
                page.reload(wait_until="networkidle")
            else:
                # 使用 F5 键刷新
                page.keyboard.press("F5")
                page.wait_for_load_state("networkidle")
        else:
            logger.info(f"导航到页面: {config.TARGET_URL}")
            # 第一次访问或URL不匹配，导航到目标页面
            page.goto(config.TARGET_URL, wait_until="networkidle")
        
        # 模拟人类行为：随机滚动
        for _ in range(random.randint(1, 3)):
            scroll_amount = random.randint(100, 500)
            page.mouse.wheel(0, scroll_amount)
            time_module.sleep(random.uniform(0.5, 1.5))
        
        # 滚动回顶部
        page.mouse.wheel(0, -2000)
        time_module.sleep(random.uniform(0.5, 1))
        
        # 等待帖子加载
        try:
            page.wait_for_selector(config.SELECTORS['post'], timeout=15000)
            logger.info("帖子内容已加载")
        except PlaywrightTimeoutError:
            logger.error("等待帖子超时")
            return None, None
        
        # 等待图片加载完成（如果有）
        page.wait_for_timeout(2000)  # 额外等待2秒确保图片加载
        
        # 获取所有帖子元素
        all_posts = page.locator(config.SELECTORS['post']).all()
        
        # 找到第一个非置顶的帖子
        post_element = None
        post_index = 0
        
        for i, post in enumerate(all_posts):
            # 检查帖子是否包含置顶标记
            pinned_indicator = post.locator(config.SELECTORS['pinned_indicator'])
            
            # 检查是否存在置顶标记并且文本包含 "Pinned"
            if pinned_indicator.count() > 0:
                try:
                    pinned_text = pinned_indicator.first.text_content()
                    if pinned_text and "Pinned" in pinned_text:
                        logger.info(f"跳过置顶帖子 (索引: {i})")
                        continue
                except:
                    # 如果获取文本失败，也尝试下一个
                    pass
            
            # 找到第一个非置顶帖子
            post_element = post
            post_index = i
            logger.info(f"选择帖子 (索引: {post_index})")
            break
        
        if not post_element:
            logger.error("未找到非置顶的帖子")
            return None, None
        
        # 滚动到帖子位置，确保完全可见
        post_element.scroll_into_view_if_needed()
        page.wait_for_timeout(500)  # 等待滚动完成
        
        # 隐藏可能的干扰元素（如固定的导航栏、弹窗等）
        page.evaluate("""
            // 隐藏可能的固定元素
            const fixedElements = document.querySelectorAll('[style*="position: fixed"], [style*="position: sticky"]');
            fixedElements.forEach(el => el.style.display = 'none');
            
            // 隐藏可能的模态框
            const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
            modals.forEach(el => el.style.display = 'none');
            
            // 隐藏cookie提示等
            const banners = document.querySelectorAll('[class*="banner"], [class*="consent"], [class*="cookie"]');
            banners.forEach(el => el.style.display = 'none');
        """)
        
        # 生成截图文件名（使用时间戳，稍后会更新为content_id）
        temp_screenshot_path = config.SCREENSHOTS_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # 对帖子元素进行截图
        try:
            # 获取帖子的边界框
            bounding_box = post_element.bounding_box()
            if bounding_box:
                # 添加一些内边距，确保完整截图
                padding = 20
                clip = {
                    'x': max(0, bounding_box['x'] - padding),
                    'y': max(0, bounding_box['y'] - padding),
                    'width': bounding_box['width'] + 2 * padding,
                    'height': bounding_box['height'] + 2 * padding
                }
                
                # 截图特定区域
                page.screenshot(
                    path=str(temp_screenshot_path),
                    clip=clip,
                    full_page=False
                )
                logger.info(f"帖子截图已保存到临时文件: {temp_screenshot_path}")
            else:
                # 如果无法获取边界框，使用元素截图方法
                post_element.screenshot(path=str(temp_screenshot_path))
                logger.info(f"帖子截图已保存（使用元素截图）: {temp_screenshot_path}")
                
        except Exception as e:
            logger.error(f"截图失败: {str(e)}")
            temp_screenshot_path = None
        
        # 获取页面HTML
        html = page.content()
        
        soup = BeautifulSoup(html, 'html.parser')
        logger.info("页面获取成功")
        return soup, str(temp_screenshot_path) if temp_screenshot_path else None
    
    except Exception as e:
        logger.error(f"获取页面失败: {str(e)}")
        return None, None

def extract_post_info(soup):
    """
    从页面中提取最新的非置顶帖子信息
    
    Args:
        soup (BeautifulSoup): 解析后的页面
        
    Returns:
        dict: 帖子信息，包含ID、时间、文本、图片URL和视频URL
    """
    try:
        # 找到所有帖子
        all_posts = soup.select(config.SELECTORS['post'])
        if not all_posts:
            logger.error("未找到任何帖子")
            return None
        
        # 找到第一个非置顶的帖子
        post = None
        for i, p in enumerate(all_posts):
            # 检查是否包含置顶标记
            pinned_indicator = p.select_one(config.SELECTORS['pinned_indicator'])
            if pinned_indicator:
                pinned_text = pinned_indicator.get_text(strip=True)
                if "Pinned" in pinned_text:
                    logger.info(f"跳过置顶帖子 (索引: {i})")
                    continue
            
            # 找到第一个非置顶帖子
            post = p
            logger.info(f"处理帖子 (索引: {i})")
            break
        
        if not post:
            logger.error("未找到非置顶的帖子")
            return None
        
        # 提取内容ID
        post_link = post.select_one(config.SELECTORS['post_link_primary'])
        if not post_link:
            post_link = post.select_one(config.SELECTORS['post_link_secondary'])
            
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
        text_element = post.select_one(config.SELECTORS['text'])
        text_content = text_element.get_text(strip=True) if text_element else None
        if text_content == "":
            text_content = None

        # 提取URL链接
        url_link = None
        if text_element:
            link_element = text_element.select_one(config.SELECTORS['text_embedded_link'])
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
        video_element = post.select_one(config.SELECTORS['video_generic'])
        if not video_element:
            video_element = post.select_one(config.SELECTORS['video_480p'])
            
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

def process_post(post_info, screenshot_path=None):
    """
    处理帖子信息，下载媒体文件并保存结果
    
    Args:
        post_info (dict): 帖子信息
        screenshot_path (str): 临时截图路径
        
    Returns:
        dict: 处理后的帖子数据
    """
    if not post_info:
        return None
        
    try:
        content_id = post_info["contentID"]
        
        # 处理截图：重命名为正确的文件名
        final_screenshot_path = None
        if screenshot_path and os.path.exists(screenshot_path):
            final_screenshot_path = config.SCREENSHOTS_DIR / f"{content_id}.png"
            os.rename(screenshot_path, final_screenshot_path)
            logger.info(f"截图已重命名为: {final_screenshot_path}")
        
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
            "images": image_paths or [],
            "videos": video_path if video_path else None,
            "screenshot": str(final_screenshot_path) if final_screenshot_path else None  # 新增截图路径
        }
        
        # 保存到JSON文件
        save_post_data(result)
        
        return result
        
    except Exception as e:
        logger.error(f"处理帖子失败: {str(e)}")
        # 清理临时截图
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
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
    抓取最新的帖子信息并处理（包括截图）
    
    Returns:
        dict: 处理后的帖子数据，失败则返回None
    """
    # 确保配置初始化
    config.init()
    
    # 获取页面和截图
    soup, temp_screenshot_path = fetch_page_and_screenshot()
    if not soup:
        return None
        
    # 提取帖子信息
    post_info = extract_post_info(soup)
    if not post_info:
        # 如果提取失败，删除临时截图
        if temp_screenshot_path and os.path.exists(temp_screenshot_path):
            os.remove(temp_screenshot_path)
        return None
        
    # 处理帖子（包括重命名截图）
    result = process_post(post_info, temp_screenshot_path)
    return result

# 测试
if __name__ == "__main__":
    config.init()
    result = scrape_latest_post()
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get('screenshot'):
            print(f"截图已保存: {result['screenshot']}")
    else:
        print("抓取失败")
