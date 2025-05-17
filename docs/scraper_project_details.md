目标网页： https://truthsocial.com/@realDonaldTrump

生产环境：ubuntu 24.04LTS
开发环境：windows11、cursor

第一步访问https://truthsocial.com/@realDonaldTrump
第二步识别网页中内容发布的时间，采集距离当前时间最近的；网页中时间标签示例：<time title="May 03, 2025, 1:47 PM"
第三步采集该时间对应的内容，包括文本；如果遇到图片则下载保存该图片到本地，保存位置为./pics，文件名为"内容ID+图片ID"；如果遇到内容是视频，则下载该视频到本地，保存位置为./movs，文件名为"内容ID"。

内容保存为jason，内容格式排序：内容ID、时间、文本内容、图片本地位置、视频本地位置。

技术栈：
1. 编程语言：Python
2. 网页抓取与解析：Requests 和 BeautifulSoup 
3. 时间处理：DateTime 
4. 目标网页html采集目标：div data-index="0"，，需要先判断在这个标签下的各个目标内容对应标签如下：
      1. 时间：<time title="May 04, 2025, 11:47 AM"
      2. 文本：在<div class="relative">中的<p>
      3. 图片：在<div data-testid="still-image-container"中的<img src="https://static-assets-1.truthsocial.com/tmtg:prime-ts-assets/media_attachments/files/114/447/455/475/331/043/small/e880cd99b73425d0.jpg"
      4. 视频<source src="https://1a-1791.com/video/fww1/f8/s8/2/X/R/v/H/XRvHy.caa.mp4?b=1&amp;u=ummtf" type="video/mp4" data-quality="480p">。注意选择data-quality="480p"对应的url下载，该网站一般会提供多质量版本的视频，注意区分。
5. 数据保存：工具：JSON 和 OS/Shutil
   1. JSON： 将提取的数据保存为 JSON 文件，格式为 {内容ID, 时间, 文本内容, 图片本地位置, 视频本地位置}。  
   2. OS 和 Shutil： 创建目录（如 ./pics 和 ./movs），并保存下载的图片和视频。    
   3. 注意： 确保文件路径跨平台兼容，使用 os.path 或 pathlib 处理路径分隔符。需要处理可能的多张图片和视频，确保命名唯一，避免覆盖。同时媒体内容有可能只是文本，也有可能是文本+图片，也有可能是文本+视频，也有可能只有图片，也有可能是只有视频。注意对媒体内容进行判断，对没有的内容表示为null。
   4. 保存示例：
        ```json
        {
            "contentID": content_id,
            "time": formatted_time,
            "text": text_content,
            "url": url_link,
            "image_urls": image_urls,
            "video_url": video_url
        }
        ```

6. 项目文件结构
      stupid_trump_index/
      │
      ├── main.py                  # 主程序入口点
      ├── scraper.py               # 网页抓取和内容提取
      ├── downloader.py            # 媒体文件下载器
      ├── config.py                # 配置参数和常量
      │
      ├── pics/                    # 图片保存目录
      ├── movs/                    # 视频保存目录
      ├── data/                    # JSON数据保存目录
      │   └── history.json         # 历史记录追踪
      │
      ├── venv/                    # 虚拟环境(已创建)
      └── docs/                    # 文档
      └── project_details.md   # 项目详情

main.py调度整个流程
scraper.py专注于网页内容解析
downloader.py处理媒体下载
config.py便于集中管理URLs和其他配置

7. 开发顺序
      1. 首先编写config.py：
            - 定义URL常量
            - 指定文件路径和目录结构
            - 设置请求头和其他全局参数
      2. 然后是downloader.py：
            - 创建下载图片和视频的功能
            - 设计文件保存结构
      3. 接着编写scraper.py：
            - 实现网页解析的核心逻辑
            - 利用downloader模块处理媒体
      4. 最后完成main.py：
            - 整合所有组件
            - 实现主要执行流程











