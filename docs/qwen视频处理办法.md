视频理解
部分通义千问VL模型支持对视频内容的理解，文件形式包括图像列表（视频帧）或视频文件。

视频文件图像列表
qwen-vl-max、qwen-vl-max-latest、qwen-vl-max-1119、qwen-vl-max-0125及之后的模型、qwen-vl-plus、qwen-vl-plus-0125及之后的模型、qwen2.5-vl-32b-instruct、qwen2.5-vl-72b-instruct可直接传入视频文件。

传入视频URL时：Qwen2.5-VL系列模型支持传入的视频大小不超过1 GB，其他模型不超过150MB。

传入本地文件时：使用OpenAI SDK方式，经Base64编码后的视频需小于10MB；使用DashScope SDK方式，视频本身需小于100MB。详情请参见传入本地文件。

视频文件格式： MP4、AVI、MKV、MOV、FLV、WMV 等。

视频时长：Qwen2.5-VL系列模型支持的视频时长为2秒至10分钟，其他模型为2秒至40秒。

视频尺寸：无限制，但是视频文件会被调整到约 60万 像素数，更大尺寸的视频文件不会有更好的理解效果。

暂时不支持对视频文件的音频进行理解。

传入视频URL时：Qwen2.5-VL系列模型支持传入的视频大小不超过1 GB，其他模型不超过150MB。

传入本地文件时：使用OpenAI SDK方式，经Base64编码后的视频需小于10MB；使用DashScope SDK方式，视频本身需小于100MB。详情请参见传入本地文件。

视频文件格式： MP4、AVI、MKV、MOV、FLV、WMV 等。

视频时长：Qwen2.5-VL系列模型支持的视频时长为2秒至10分钟，其他模型为2秒至40秒。

视频尺寸：无限制，但是视频文件会被调整到约 60万 像素数，更大尺寸的视频文件不会有更好的理解效果。

暂时不支持对视频文件的音频进行理解。

通义千问VL模型进行视频理解前，会对视频文件进行抽帧，抽取若干图像后再对内容进行理解，您可以设置fps参数来控制抽帧的频率：

仅支持在使用DashScope SDK调用时设置，表示对视频文件每隔1/fps秒抽取一张图像。较大的fps适合高速运动的场景（如体育赛事、动作电影等），较小的fps适合长视频或内容偏静态的场景

使用OpenAI SDK调用则无法设置抽帧频率，视频文件统一每隔0.5秒抽取一帧

使用本地文件（输入Base64编码或本地路径）
下面是传入本地图像或视频文件的示例代码，使用OpenAI SDK或HTTP方式时，需要将本地文件编码为Base64格式后再传入；使用DashScope SDK时，直接传入本地文件的路径即可。

使用DashScope SDK处理本地视频文件时，需要传入文件路径，传入方式请参见传入本地文件路径。

```Python
import os
from dashscope import MultiModalConversation
# 将xxxx/test.mp4替换为你本地视频的绝对路径
local_path = "xxx/test.mp4"
video_path = f"file://{local_path}"
messages = [{'role': 'system',
                'content': [{'text': 'You are a helpful assistant.'}]},
                {'role':'user',
                # fps参数控制视频抽帧数量，表示每隔1/fps 秒抽取一帧
                'content': [{'video': video_path,"fps":2},
                            {'text': '这段视频描绘的是什么景象?'}]}]
response = MultiModalConversation.call(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    model='qwen-vl-max-latest',  
    messages=messages)
print(response["output"]["choices"][0]["message"].content[0]["text"])
```

enable_search boolean （可选）

模型在生成文本时是否使用互联网搜索结果进行参考。取值如下：

true：启用互联网搜索，模型会将搜索结果作为文本生成过程中的参考信息，但模型会基于其内部逻辑判断是否使用互联网搜索结果。

如果模型没有搜索互联网，建议优化Prompt，或设置search_options中的forced_search参数开启强制搜索。
false（默认）：关闭互联网搜索。

启用互联网搜索功能可能会增加 Token 的消耗。
若您通过 Python SDK调用，请通过extra_body配置。配置方式为：extra_body={"enable_search": True}。