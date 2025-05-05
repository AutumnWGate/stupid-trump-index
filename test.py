import config
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)

def fetch_page():
    try:
        with sync_playwright() as p:
            # 1. 使用有界面模式(headless=False)启动浏览器
            browser = p.chromium.launch(
                headless=False,  # 保持浏览器可见
                proxy={"server": "socks5://127.0.0.1:10808"},
                slow_mo=500  # 放慢操作，更容易观察
            )
            
            # 2. 从用户配置文件加载浏览器上下文
            # 可以使用你已登录的Chrome用户数据目录
            # context = browser.new_context(
            #    user_data_dir="C:\\Users\\YourUsername\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
            # )
            # page = context.new_page()
            
            # 或者简单地创建新页面(用于手动登录)
            page = browser.new_page(ignore_https_errors=True)
            page.goto(config.TARGET_URL)
            
            # 暂停执行，等待手动登录(如需要)
            print("请在浏览器中完成必要的登录或验证步骤...")
            input("完成后按Enter键继续...")
            
            # 3. 等待内容加载
            try:
                page.wait_for_selector(config.SELECTORS['post'], timeout=10000)
                print("找到了帖子内容!")
            except Exception as e:
                print(f"未找到帖子: {e}")
                # 继续执行，我们仍然会保存页面内容
            
            # 4. 获取页面内容
            content = page.content()
            
            # 5. 保存截图
            page.screenshot(path="page_screenshot.png")
            
            # 可选：保持浏览器开着直到用户关闭
            input("检查完毕后按Enter键关闭浏览器...")
            
            browser.close()
            return content
    except Exception as e:
        logger.error(f"获取页面失败: {str(e)}")
        return None

config.init()
content = fetch_page()
if content:
    with open("test_page.html", "w", encoding="utf-8") as f:
        f.write(content)