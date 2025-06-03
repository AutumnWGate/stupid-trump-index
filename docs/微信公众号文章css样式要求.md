🎨 一、支持的CSS样式
​​文本与字体样式​​
基础属性：font-size（字号）、color（文字颜色）、font-weight（加粗）、font-style（斜体）。
间距控制：line-height（行高）、letter-spacing（字间距）、text-indent（首行缩进）。
对齐与装饰：text-align（左/中/右对齐）、text-decoration（下划线等）。
​​布局与盒模型​​
边距设置：margin（外边距）、padding（内边距）。
边框效果：border（边框粗细/样式/颜色）、border-radius（圆角）。
背景样式：background-color（纯色背景），但渐变背景（linear-gradient）兼容性较差。
​​图片与多媒体​​
图片美化：支持border、box-shadow（阴影）、max-width:100%（自适应宽度）。
微信专用标签：需用<mpvideo>、<mpvoice>嵌入视频/音频，而非标准<video>/<audio>标签。
​​简单交互效果​​
支持:hover伪类（如按钮悬停变色），但复杂动画（@keyframes）被禁用。
⚠️ 二、关键限制与要求
​​样式必须内联​​
所有CSS必须写在元素的style属性中（如<p style="color:red;">），​​不支持​​<style>标签或外部CSS文件。
​​禁止的布局与交互​​
定位布局：position: absolute/fixed/relative、z-index会被过滤。
高级特性：媒体查询（@media）、CSS动画、Flex/Grid布局均无效。
脚本相关：禁用<script>、<iframe>及表单标签（<form>、<input>）。
​​兼容性注意​​
SVG图片需上传至微信素材库，外链或Base64格式可能失效。
外链（<a>标签）会触发微信安全提示。
💡 三、实用建议
​​简化设计​​：优先使用基础样式（如行高1.8、字号14px-16px），避免复杂布局