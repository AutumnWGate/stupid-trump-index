# downloader.py
import os
import logging
import requests
from pathlib import Path
from urllib.parse import urlparse

# 导入配置
import config

# 获取logger
logger = logging.getLogger(__name__)

def download_image(image_url, content_id, image_id=0):
    """
    下载图片并按指定格式保存
    
    Args:
        image_url (str): 图片URL
        content_id (str): 内容ID
        image_id (int, optional): 图片ID，默认为0
    
    Returns:
        str: 保存的图片本地路径，失败返回None
    """
    try:
        # 提取文件扩展名
        parsed_url = urlparse(image_url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        if not file_extension:
            file_extension = '.jpg'  # 默认扩展名
        
        # 构建文件名
        filename = f"{content_id}_image{image_id}{file_extension}"
        file_path = config.PICS_DIR / filename
        
        # 下载图片
        logger.info(f"开始下载图片: {image_url}")
        response = requests.get(image_url, headers=config.HEADERS, timeout=config.REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        # 保存图片
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"图片下载成功: {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"下载图片失败: {image_url}, 错误: {str(e)}")
        return None

def download_video(video_url, content_id):
    """
    下载视频并按指定格式保存
    
    Args:
        video_url (str): 视频URL
        content_id (str): 内容ID
    
    Returns:
        str: 保存的视频本地路径，失败返回None
    """
    try:
        # 提取文件扩展名
        parsed_url = urlparse(video_url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        if not file_extension:
            file_extension = '.mp4'  # 默认扩展名
            
        # 构建文件名
        filename = f"{content_id}{file_extension}"
        file_path = config.MOVS_DIR / filename
        
        # 下载视频
        logger.info(f"开始下载视频: {video_url}")
        response = requests.get(video_url, headers=config.HEADERS, timeout=config.REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        
        # 保存视频
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"视频下载成功: {file_path}")
        return str(file_path)
    
    except Exception as e:
        logger.error(f"下载视频失败: {video_url}, 错误: {str(e)}")
        return None

def download_media(content_id, image_urls=None, video_url=None):
    """
    下载与内容关联的所有媒体文件
    
    Args:
        content_id (str): 内容ID
        image_urls (list, optional): 图片URL列表
        video_url (str, optional): 视频URL
        
    Returns:
        tuple: (图片路径列表, 视频路径)
    """
    image_paths = []
    video_path = None
    
    # 下载图片
    if image_urls:
        for i, url in enumerate(image_urls):
            path = download_image(url, content_id, i)
            if path:
                image_paths.append(path)
    
    # 下载视频
    if video_url:
        video_path = download_video(video_url, content_id)
    
    return image_paths, video_path

# 简单测试
if __name__ == "__main__":
    config.init()
    test_image_url = "https://static-assets-1.truthsocial.com/tmtg:prime-ts-assets/media_attachments/files/114/447/455/475/331/043/small/e880cd99b73425d0.jpg"
    test_video_url = "https://1a-1791.com/video/fww1/f8/s8/2/X/R/v/H/XRvHy.caa.mp4"
    
    test_content_id = "test123"
    
    images, video = download_media(
        test_content_id, 
        image_urls=[test_image_url], 
        video_url=test_video_url
    )
    
    print(f"下载的图片: {images}")
    print(f"下载的视频: {video}")