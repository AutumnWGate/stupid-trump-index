# wechat_publisher.py
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from article_generator import ArticleGenerator

class WechatPublisher:
    def __init__(self):
        self.appid = os.getenv('WECHAT_APPID')
        self.appsecret = os.getenv('WECHAT_APPSECRET')
        self.token_file = config.DATA_DIR / "wechat_token.json"
        self.base_url = "https://api.weixin.qq.com/cgi-bin"
        
    def get_access_token(self):
        """获取access_token，实现缓存机制"""
        # 检查缓存的token是否有效
        if self.token_file.exists():
            with open(self.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            # 检查是否过期（提前5分钟刷新）
            expire_time = datetime.fromisoformat(token_data['expire_time'])
            if datetime.now() < expire_time - timedelta(minutes=5):
                print("使用缓存的access_token")
                return token_data['access_token']
        
        # 获取新的token
        print("获取新的access_token...")
        url = f"{self.base_url}/token"
        params = {
            'grant_type': 'client_credential',
            'appid': self.appid,
            'secret': self.appsecret
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'access_token' in data:
                # 保存token和过期时间
                expire_time = datetime.now() + timedelta(seconds=data['expires_in'])
                token_data = {
                    'access_token': data['access_token'],
                    'expire_time': expire_time.isoformat(),
                    'expires_in': data['expires_in']
                }
                
                with open(self.token_file, 'w', encoding='utf-8') as f:
                    json.dump(token_data, f, ensure_ascii=False, indent=2)
                
                print(f"获取access_token成功，有效期：{data['expires_in']}秒")
                return data['access_token']
            else:
                error_msg = f"获取access_token失败: {data}"
                print(error_msg)
                
                # 处理特定错误码
                errcode = data.get('errcode')
                if errcode == 40164:
                    print("错误：IP地址不在白名单中，请在公众号后台添加服务器IP到白名单")
                elif errcode == 40001:
                    print("错误：AppSecret错误，请检查配置")
                elif errcode == 89503:
                    print("错误：此IP调用需要管理员确认")
                
                return None
                
        except Exception as e:
            print(f"请求失败: {str(e)}")
            return None
    
    def upload_image(self, image_path, access_token):
        """上传图片到微信服务器（永久素材）"""
        url = f"{self.base_url}/material/add_material"
        params = {
            'access_token': access_token,
            'type': 'image'
        }
        
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, params=params, files=files)
        
        data = response.json()
        if 'media_id' in data:
            print(f"图片上传成功（永久素材），media_id: {data['media_id']}")
            return data['media_id']
        else:
            print(f"图片上传失败: {data}")
            return None
    
    def upload_news_image(self, image_path, access_token):
        """上传图文消息内的图片"""
        url = f"{self.base_url}/media/uploadimg"
        params = {'access_token': access_token}
        
        with open(image_path, 'rb') as f:
            files = {'media': f}
            response = requests.post(url, params=params, files=files)
        
        data = response.json()
        if 'url' in data:
            print(f"图文内图片上传成功，URL: {data['url']}")
            return data['url']
        else:
            print(f"图文内图片上传失败: {data}")
            return None
    
    def create_draft(self, article_data, access_token):
        """新建草稿"""
        url = f"{self.base_url}/draft/add"
        params = {'access_token': access_token}
        
        # 构建图文消息
        articles = [{
            "title": article_data['title'],
            "author": article_data.get('author', 'AI投资分析师'),
            "digest": article_data['digest'],
            "content": article_data['content'],
            "content_source_url": article_data.get('source_url', ''),
            "thumb_media_id": article_data['thumb_media_id'],
            "need_open_comment": 0,
            "only_fans_can_comment": 0
        }]
        
        data = {"articles": articles}
        
        response = requests.post(url, params=params, 
                               data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                               headers={'Content-Type': 'application/json; charset=utf-8'})
        
        result = response.json()
        if 'media_id' in result:
            print(f"草稿创建成功，media_id: {result['media_id']}")
            return result['media_id']
        else:
            print(f"草稿创建失败: {result}")
            return None
    
    def publish_draft(self, media_id, access_token):
        """发布草稿"""
        url = f"{self.base_url}/freepublish/submit"
        params = {'access_token': access_token}
        
        data = {"media_id": media_id}
        
        response = requests.post(url, params=params,
                               data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                               headers={'Content-Type': 'application/json; charset=utf-8'})
        
        result = response.json()
        if result.get('errcode', 0) == 0:
            print(f"发布任务提交成功，publish_id: {result.get('publish_id')}")
            return result.get('publish_id')
        else:
            print(f"发布任务提交失败: {result}")
            # 处理特定错误码
            errcode = result.get('errcode')
            if errcode == 53503:
                print("错误：该草稿未通过发布检查")
            elif errcode == 53504:
                print("错误：需前往公众平台官网使用草稿")
            elif errcode == 53505:
                print("错误：请手动保存成功后再发表")
            return None
    
    def get_publish_status(self, publish_id, access_token):
        """轮询发布状态"""
        url = f"{self.base_url}/freepublish/get"
        params = {'access_token': access_token}
        
        data = {"publish_id": publish_id}
        
        response = requests.post(url, params=params,
                               data=json.dumps(data, ensure_ascii=False).encode('utf-8'),
                               headers={'Content-Type': 'application/json; charset=utf-8'})
        
        return response.json()
    
    def wait_for_publish_complete(self, publish_id, access_token, max_wait_seconds=300):
        """等待发布完成，最多等待max_wait_seconds秒"""
        start_time = time.time()
        check_interval = 5  # 每5秒检查一次
        
        print(f"\n开始轮询发布状态...")
        
        while time.time() - start_time < max_wait_seconds:
            result = self.get_publish_status(publish_id, access_token)
            
            publish_status = result.get('publish_status', -1)
            
            if publish_status == 0:
                # 发布成功
                print(f"\n✓ 发布成功！")
                article_id = result.get('article_id')
                article_detail = result.get('article_detail', {})
                
                print(f"文章ID: {article_id}")
                
                # 打印文章链接
                items = article_detail.get('item', [])
                for item in items:
                    print(f"文章链接: {item.get('article_url')}")
                
                return True, result
                
            elif publish_status == 1:
                # 发布中
                elapsed = int(time.time() - start_time)
                print(f"\r发布中... 已等待 {elapsed} 秒", end='', flush=True)
                
            elif publish_status in [2, 3, 4]:
                # 发布失败
                print(f"\n✗ 发布失败！状态码: {publish_status}")
                
                status_msg = {
                    2: "原创审核不通过",
                    3: "常规失败",
                    4: "平台审核不通过"
                }
                print(f"失败原因: {status_msg.get(publish_status, '未知')}")
                
                fail_idx = result.get('fail_idx', [])
                if fail_idx:
                    print(f"失败的文章序号: {fail_idx}")
                
                return False, result
                
            elif publish_status == 5:
                print(f"\n✗ 成功后用户删除所有文章")
                return False, result
                
            elif publish_status == 6:
                print(f"\n✗ 成功后系统封禁所有文章")
                return False, result
            
            time.sleep(check_interval)
        
        print(f"\n✗ 发布超时（等待超过{max_wait_seconds}秒）")
        return False, None
    
    def publish_article(self, content_id):
        """发布文章的主流程 - 创建草稿并自动发布"""
        print("=== 开始微信公众号发布流程 ===")
        
        # 1. 获取access_token
        access_token = self.get_access_token()
        if not access_token:
            print("获取access_token失败，无法继续")
            return False
        
        # 2. 生成文章
        print("\n生成文章...")
        generator = ArticleGenerator()
        try:
            html_file, screenshot_path = generator.generate_article(content_id)
        except Exception as e:
            print(f"生成文章失败: {e}")
            return False
        
        # 3. 上传封面图（永久素材）
        print("\n上传封面图...")
        thumb_media_id = self.upload_image(screenshot_path, access_token)
        if not thumb_media_id:
            print("上传封面图失败")
            return False
        
        # 4. 上传文章内的截图
        print("\n上传文章内图片...")
        screenshot_url = self.upload_news_image(screenshot_path, access_token)
        if not screenshot_url:
            print("上传文章内图片失败")
            return False
        
        # 5. 读取并处理HTML内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 替换截图占位符为实际URL
        html_content = html_content.replace(f'cid:{content_id}.png', screenshot_url)
        
        # 6. 准备文章数据
        # 读取帖子数据获取摘要
        summary_file = config.RESULT_DIR / f"{content_id}_all_ai_results.json"
        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        post_text = data['post_data'].get('text', '')[:50] + "..." if data['post_data'].get('text') else "特朗普最新言论"
        
        article_data = {
            'title': f"特朗普最新言论AI投资分析 - {datetime.now().strftime('%m月%d日')}",
            'digest': f"{post_text}\n三大AI深度解析对A股市场的影响",
            'content': html_content,
            'thumb_media_id': thumb_media_id,
            'author': 'AI投资分析师'
        }
        
        # 7. 创建草稿
        print("\n创建草稿...")
        draft_media_id = self.create_draft(article_data, access_token)
        if not draft_media_id:
            print("创建草稿失败")
            return False
        
        # 8. 发布草稿
        print("\n提交发布任务...")
        publish_id = self.publish_draft(draft_media_id, access_token)
        if not publish_id:
            print("发布任务提交失败")
            return False
        
        # 9. 等待发布完成
        success, publish_result = self.wait_for_publish_complete(publish_id, access_token)
        
        # 10. 保存发布记录
        publish_record = {
            'content_id': content_id,
            'draft_media_id': draft_media_id,
            'publish_id': publish_id,
            'title': article_data['title'],
            'create_time': datetime.now().isoformat(),
            'status': 'published' if success else 'failed',
            'publish_result': publish_result
        }
        
        records_file = config.DATA_DIR / "publish_records.json"
        records = []
        if records_file.exists():
            with open(records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        
        records.append(publish_record)
        
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        
        if success:
            print(f"\n=== 发布成功！ ===")
            print(f"文章标题: {article_data['title']}")
            print(f"发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            if publish_result and 'article_detail' in publish_result:
                items = publish_result['article_detail'].get('item', [])
                if items:
                    print(f"文章链接: {items[0].get('article_url')}")
        else:
            print(f"\n=== 发布失败 ===")
            print("请检查草稿内容或在公众号后台查看详细错误信息")
        
        return success

if __name__ == "__main__":
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    # 测试
    publisher = WechatPublisher()
    
    # 获取最新的content_id
    with open(config.HISTORY_FILE, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    if history:
        content_id = history[-1]['contentID']
        publisher.publish_article(content_id)
    else:
        print("没有可发布的内容")