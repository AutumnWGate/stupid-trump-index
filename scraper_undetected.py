import undetected_chromedriver as uc
import time
import random
import json
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import os
import re
from bs4 import BeautifulSoup
import atexit

import config
from downloader import download_media

logger = logging.getLogger(__name__)

class UndetectedScraper:
    def __init__(self):
        self.driver = None
        self.user_data_dir = str(config.BROWSER_USER_DATA_DIR / "undetected_chrome")
        
    def init_driver(self):
        """初始化 undetected-chromedriver"""
        if self.driver is None:
            logger.info("初始化 undetected-chromedriver...")
            
            # 确保用户数据目录存在
            os.makedirs(self.user_data_dir, exist_ok=True)
            
            # Chrome选项
            options = uc.ChromeOptions()
            
            # 使用用户数据目录
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            
            # 其他选项
            options.add_argument('--start-maximized')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            
            # 设置代理
            options.add_argument('--proxy-server=socks5://127.0.0.1:10808')
            
            # 设置语言和时区
            options.add_experimental_option("prefs", {
                "intl.accept_languages": "en-US,en",
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            })
            
            # 创建驱动（指定Chrome版本为135）
            try:
                self.driver = uc.Chrome(
                    options=options,
                    driver_executable_path=None,  # 自动下载驱动
                    version_main=135,  # 指定Chrome版本为135
                    use_subprocess=True  # 使用子进程
                )
            except Exception as e:
                logger.error(f"创建Chrome驱动失败: {e}")
                raise
            
            # 设置隐式等待
            self.driver.implicitly_wait(10)
            
            # 执行一些JavaScript来进一步隐藏特征
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // 覆盖 navigator.webdriver
                    delete Object.getPrototypeOf(navigator).webdriver;
                    
                    // 模拟真实的 chrome 对象
                    window.chrome = {
                        app: {},
                        runtime: {
                            connect: function() {},
                            sendMessage: function() {}
                        }
                    };
                    
                    // 修改 permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                '''
            })
            
            logger.info("undetected-chromedriver 初始化完成")
            
        return self.driver
    
    def human_like_delay(self, min_sec=1, max_sec=3):
        """模拟人类的随机延迟"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def random_mouse_movement(self):
        """随机鼠标移动"""
        try:
            # 获取页面大小
            window_size = self.driver.get_window_size()
            width = window_size['width']
            height = window_size['height']
            
            # 随机移动鼠标3-5次
            actions = ActionChains(self.driver)
            for _ in range(random.randint(3, 5)):
                x = random.randint(100, width - 100)
                y = random.randint(100, height - 100)
                
                # 移动到随机位置
                actions.move_to_element_with_offset(
                    self.driver.find_element(By.TAG_NAME, "body"), 
                    x - width//2, 
                    y - height//2
                ).perform()
                
                self.human_like_delay(0.1, 0.3)
                
        except Exception as e:
            logger.debug(f"鼠标移动失败: {e}")
    
    def random_scroll(self):
        """随机滚动页面"""
        # 随机滚动2-4次
        for _ in range(random.randint(2, 4)):
            # 随机滚动距离
            scroll_distance = random.randint(100, 500)
            
            # 随机向上或向下
            if random.choice([True, False]):
                self.driver.execute_script(f"window.scrollBy(0, {scroll_distance})")
            else:
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_distance})")
            
            self.human_like_delay(0.5, 1.5)
    
    def fetch_page_and_screenshot(self, post_index_to_fetch=None):
        """
        获取页面内容并截图
        
        Args:
            post_index_to_fetch (int, optional): 要采集的帖子索引（从0开始，不包括置顶帖子）。
                                                 None表示采集第一个非置顶帖子。
        """
        driver = self.init_driver()
        
        try:
            # 检查是否已经在目标页面
            if driver.current_url.startswith(config.TARGET_URL):
                logger.info("刷新当前页面")
                driver.refresh()
            else:
                logger.info(f"导航到: {config.TARGET_URL}")
                driver.get(config.TARGET_URL)
            
            # 等待页面加载
            self.human_like_delay(2, 4)
            
            # 随机行为
            self.random_mouse_movement()
            self.random_scroll()
            
            # 滚动回顶部
            driver.execute_script("window.scrollTo(0, 0)")
            self.human_like_delay(1, 2)
            
            # 等待帖子加载
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS['post'])))
            
            # 额外等待图片加载
            self.human_like_delay(1, 2)
            
            # 查找所有帖子
            posts = driver.find_elements(By.CSS_SELECTOR, config.SELECTORS['post'])
            
            # 收集所有非置顶的帖子
            non_pinned_posts = []
            non_pinned_indices = []  # 记录原始索引
            
            for i, post in enumerate(posts):
                try:
                    # 检查是否有置顶标记
                    pinned_elements = post.find_elements(By.CSS_SELECTOR, config.SELECTORS['pinned_indicator'])
                    if pinned_elements:
                        pinned_text = pinned_elements[0].text
                        if "Pinned" in pinned_text:
                            logger.info(f"跳过置顶帖子 (原始索引: {i})")
                            continue
                except:
                    pass
                
                # 这是一个非置顶帖子
                non_pinned_posts.append(post)
                non_pinned_indices.append(i)
                logger.info(f"找到非置顶帖子 (原始索引: {i}, 非置顶索引: {len(non_pinned_posts)-1})")
            
            # 检查是否有足够的非置顶帖子
            if not non_pinned_posts:
                logger.error("未找到任何非置顶的帖子")
                return None, None
            
            # 确定要采集的帖子
            if post_index_to_fetch is None:
                # 默认采集第一个非置顶帖子
                target_index = 0
            else:
                target_index = post_index_to_fetch
            
            # 检查索引是否有效
            if target_index >= len(non_pinned_posts):
                logger.error(f"请求的帖子索引 {target_index} 超出范围，只有 {len(non_pinned_posts)} 个非置顶帖子")
                return None, None
            
            # 选择目标帖子
            post_element = non_pinned_posts[target_index]
            original_index = non_pinned_indices[target_index]
            logger.info(f"选择帖子 (非置顶索引: {target_index}, 原始索引: {original_index})")
            
            # 滚动到帖子位置
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
            self.human_like_delay(0.5, 1)
            
            # 生成临时截图文件名
            temp_screenshot_path = config.SCREENSHOTS_DIR / f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            # 截图
            try:
                post_element.screenshot(str(temp_screenshot_path))
                logger.info(f"帖子截图已保存到临时文件: {temp_screenshot_path}")
            except Exception as e:
                logger.error(f"截图失败: {e}")
                temp_screenshot_path = None
            
            # 获取页面HTML
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 将选择的帖子索引信息传递给解析函数
            # 可以在soup对象上附加额外信息
            soup._selected_post_index = target_index
            
            logger.info("页面获取成功")
            return soup, str(temp_screenshot_path) if temp_screenshot_path else None
            
        except TimeoutException:
            logger.error("页面加载超时")
            return None, None
        except Exception as e:
            logger.error(f"获取页面失败: {e}")
            return None, None
    
    def cleanup(self):
        """清理资源"""
        if self.driver:
            logger.info("关闭浏览器")
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# 从原来的 scraper.py 复制的解析函数
def extract_post_info(soup, post_index_to_fetch=None):
    """
    从页面中提取指定的非置顶帖子信息
    
    Args:
        soup (BeautifulSoup): 解析后的页面
        post_index_to_fetch (int, optional): 要采集的非置顶帖子索引（从0开始）
    """
    try:
        # 如果soup对象有附加的索引信息，优先使用
        if hasattr(soup, '_selected_post_index'):
            post_index_to_fetch = soup._selected_post_index
        
        # 找到所有帖子
        all_posts = soup.select(config.SELECTORS['post'])
        if not all_posts:
            logger.error("未找到任何帖子")
            return None
        
        # 收集所有非置顶的帖子
        non_pinned_posts = []
        
        for i, p in enumerate(all_posts):
            # 检查是否包含置顶标记
            pinned_indicator = p.select_one(config.SELECTORS['pinned_indicator'])
            if pinned_indicator:
                pinned_text = pinned_indicator.get_text(strip=True)
                if "Pinned" in pinned_text:
                    logger.info(f"跳过置顶帖子 (索引: {i})")
                    continue
            
            # 这是一个非置顶帖子
            non_pinned_posts.append(p)
        
        if not non_pinned_posts:
            logger.error("未找到任何非置顶的帖子")
            return None
        
        # 确定要处理的帖子
        if post_index_to_fetch is None:
            target_index = 0
        else:
            target_index = post_index_to_fetch
        
        # 检查索引是否有效
        if target_index >= len(non_pinned_posts):
            logger.error(f"请求的帖子索引 {target_index} 超出范围，只有 {len(non_pinned_posts)} 个非置顶帖子")
            return None
        
        # 选择目标帖子
        post = non_pinned_posts[target_index]
        logger.info(f"处理帖子 (非置顶索引: {target_index})")
        
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
            "video_url": video_url,
            "post_index": target_index  # 添加帖子索引信息
        }
        
    except Exception as e:
        logger.error(f"提取帖子信息失败: {str(e)}")
        return None

def process_post(post_info, screenshot_path=None):
    """处理帖子信息，下载媒体文件并保存结果"""
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
            "screenshot": str(final_screenshot_path) if final_screenshot_path else None
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
    """保存帖子数据到JSON文件"""
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

# 全局实例
_scraper = None

def get_scraper():
    """获取全局scraper实例"""
    global _scraper
    if _scraper is None:
        _scraper = UndetectedScraper()
    return _scraper

def cleanup_browser():
    """清理浏览器资源"""
    global _scraper
    if _scraper:
        _scraper.cleanup()
        _scraper = None

# 注册退出时的清理函数
atexit.register(cleanup_browser)

def scrape_latest_post(post_index=None):
    """
    抓取指定索引的帖子信息并处理（包括截图）
    
    Args:
        post_index (int, optional): 要采集的非置顶帖子索引（从0开始）。
                                   None表示采集第一个非置顶帖子。
    """
    # 确保配置初始化
    config.init()
    
    scraper = get_scraper()
    
    # 获取页面和截图
    soup, temp_screenshot_path = scraper.fetch_page_and_screenshot(post_index_to_fetch=post_index)
    if not soup:
        return None
        
    # 提取帖子信息
    post_info = extract_post_info(soup, post_index_to_fetch=post_index)
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
    
    # 测试采集第三个帖子（索引为2，因为从0开始）
    print("采集第三个非置顶帖子...")
    result = scrape_latest_post(post_index=2)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get('screenshot'):
            print(f"截图已保存: {result['screenshot']}")
    else:
        print("抓取失败")
