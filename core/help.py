# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

GENERAL_HELP_TEXT = """

<h2>📌 通用操作</h2>

<br><b>1. 文件管理</b><br><br>
• 添加文件：点击「添加文件」按钮选择文件，或将文件 / 文件夹拖入列表<br>
• 移除文件：选中行后点击「移除选中」；点击「清空列表」移除全部<br>
• 调整顺序：拖拽行上下移动；点击「输入文件名」列头按名称排序<br><br>

<b>2. 输出设置</b><br><br>
• 双击「输出文件名」列修改输出名称（批处理模式修改分组名称）<br>
• 命名设置：点击「编辑」按钮自由组合规则（插入 / 用户输入），支持调整执行顺序<br>
• 输出位置：原文件夹或自定义文件夹（点击浏览选择）<br>
• 处理后替换为输出文件：将输出文件自动加入列表<br>
• 处理后删除源文件：处理完成后自动删除原文件（谨慎使用）<br><br>

<b>3. 处理控制</b><br><br>
• 取消「选择」列的勾选可跳过该文件<br>
• 点击「开始处理」执行当前选中的功能<br>
• 任务运行中可点击「终止任务」按钮停止后续处理（已完成文件不会丢失）<br>
• 进度条显示当前处理进度（第 N / 总数），日志窗口实时输出信息<br>
• 点击「打开输出目录」快速定位输出文件夹<br><br>

<b>4. 快捷键</b><br><br>
• Delete 键：快速移除选中的文件<br>
• ESC 键：终止正在运行的任务<br><br>

<b>5. 帮助</b><br><br>
• 点击「帮助」按钮打开帮助对话框<br>
• 左侧目录可切换查看：功能说明 / 通用操作 / 关于程序<br>

<p style="text-align:center; color:#888; font-size:12px;">
© 张小鱼（Aria）· contact@arianote.top
</p>
"""


def get_about_text():
    return """
    <h2>📄 关于程序</h2>
    <br>
    • 兼容性：Windows 7/10/11（64 位），无需安装 Python<br>
    • 开发语言：Python + PySide6<br>
    • 开源协议：AGPL-3.0-or-later<br>
    • 项目地址：<a href="https://github.com/zyyaria/BatchTool" style="color: #2196F3; text-decoration: none;">github.com/zyyaria/BatchTool</a><br>
    
    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>
    """


def get_pdf_help_text():
    return """
    <h2>📄 PDF 批量处理工具</h2>

    <br><b>1. 压缩 PDF 文件</b><br><br>
    ● 预设：轻微、中等、较强、最大<br>
    ● DPI：72~300 ppi，控制图片分辨率<br>
    ● JPEG 质量：10~100%，平衡画质与体积<br>
    ● 色彩模式：彩色、灰度、黑白（灰度减约 30%，黑白减 70% 以上）<br>
    ● GS 路径：需安装 <a href="https://www.ghostscript.com/releases/gsdnld.html">Ghostscript</a>，程序自动检测，可手动指定路径<br><br>
    
    <b>2. PDF 格式转换</b><br><br>
    ● 转换为 PDF：DOC、DOCX、XLS、XLSX、PPT、PPTX、JPG、PNG、BMP、WEBP<br>
    ● PDF 转换至：DOCX、XLSX、PPTX、JPG、PNG、TXT、HTML<br>
    ● Office 文档互转：doc ↔ docx、xls ↔ xlsx、ppt ↔ pptx<br>
    ● 依赖：文档转换需安装 Microsoft Office 或 LibreOffice<br><br>

    <b>3. 合并 PDF 页面</b><br><br>
    ● 分组方式：按文件名前缀长度、每 N 个一组、按文件夹、所有文件<br><br>

    <b>4. 组织 PDF 页面</b><br><br>
    ● 提取页面：按页面范围提取，留空=全部；勾选「提取后删除页面」同时生成剩余部分<br>
    ● 插入页面：插入页面到指定位置；勾选「按序插入」第 N 页对应插入第 N 个文件（页码总数=左侧文件数）<br>
    ● 替换页面：使用局部或全部页面替换左侧文件的页面（替换页面数=使用页面数）<br>
    ● 拆分页面：按固定页数或指定页码范围拆分为多个文件<br>
    ● 重排页面：将指定页面范围插入至某页之前或之后<br>
    ● 删除页面：删除指定页面范围（至少保留 1 页）<br>
    ● 检测页码：查看文件总页数<br><br>    

    <b>5. PDF 添加书签</b><br><br>
    ● 操作模式：插入书签 / 插入书签 + 目录 / 提取 + 插入目录（目录插入到第一页之前）<br>
    ● 自动编号：无编号、仅一级标题、多级标题，支持 3 种编号样式<br>
    ● 全局书签列表：每行 `层级 标题 页码`（Tab 或空格分隔），支持从文本文件导入<br>
    ● 页码偏移量：正文从第 N 页开始时填入 N-1，如正文从第 3 页开始填 2<br>
    ● 单文件编辑：双击「设置」列独立编辑单个文件的书签<br>
    ● 检测与清除：一键检测页码与书签结构，一键清除所有书签<br><br>    

    <b>6. 调整 PDF 尺寸</b><br><br>
    ● 预设尺寸：A0–A6、Letter、Legal、自定义（cm）<br>
    ● 内容位置：居中、左上、右上、左下、右下<br>
    ● 智能保持方向：勾选自动识别页面横竖，避免旋转变形<br>
    ● 检测页面尺寸：自动读取页面尺寸并匹配标准规格<br><br>

    <b>7. PDF 转扫描效果</b><br><br>
    ● 预设：高清扫描、彩色打印、黑白打印<br>
    ● 基本设置：颜色模式（彩色 / 黑白）、分辨率（72~300 ppi）<br>
    ● 图片调节：亮度、对比度、模糊、噪点各 0~100%，发黄 0~100%（模拟旧纸张）<br>
    ● 一键重置：恢复默认参数<br>

    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """


def get_img_help_text():
    return """
    <h2>🖼️ IMG 批量处理工具</h2>

    <br><b>1. 压缩图片文件</b><br><br>
    ● 预设：轻度、中等、强力、极限<br>
    ● 目标格式：原格式、JPG、PNG、WEBP、GIF<br>
    ● 质量：1~100%，JPG/WEBP 值越大文件越大，PNG 值越大文件越小<br>
    ● 转为灰度：勾选显著减小体积<br>
    ● 缩放：50~100%，按比例缩小<br>
    ● 最大颜色数：2~256，值越小文件越小（仅 GIF）<br>
    ● 抽帧间隔：1~10，值越大文件越小，动画越卡（仅 GIF）<br>
    ● 保留动画：勾选保留所有帧，不勾选只保留第一帧（仅 GIF）<br><br>

    <b>2. 转换图片格式</b><br><br>
    ● 目标格式：PNG、JPG、WEBP、BMP、TIFF、GIF、ICO<br>
    ● 压缩质量：1~100%，JPG/WEBP 控制画质，PNG 控制压缩级别（越小越清晰）<br>
    ● 填充白色背景：勾选避免透明区域变黑<br><br>

    <b>3. 图片拼接合并</b><br><br>
    ● 分组方式：按文件名前缀长度、每 N 个一组、按文件夹、所有文件<br>
    ● 拼接方式：垂直、水平、网格（自定义列数）、台词拼接<br>
    ● 台词拼接偏移量：负值向上偏移（去除黑边），正值向下偏移（保留黑边）<br>
    ● 间距 / 背景：间距 0~200 px，自定义背景色（HEX）<br>
    ● 目标格式：PNG、JPG、WEBP<br>
    ● 标签设置：勾选添加序号或添加文件名生效，显示在上方或下方，自定义高度和字体大小<br>
    ● 标题设置：标题不为空时生效，显示在顶部或底部，自定义高度和字体大小<br><br>

    <b>4. 调整图片大小</b><br><br>
    ● 操作模式：仅调整尺寸、仅修改 DPI、调整尺寸 + DPI<br>
    ● 目标尺寸：像素（精确宽高）、百分比（按比例缩放）、短边约束（短边固定，长边自适应）、长边约束（长边固定，短边自适应）<br>
    ● 保持比例：勾选保持比例，不勾选则拉伸<br>
    ● 目标 DPI：1~3000，修改打印密度（仅 DPI 模式生效）<br>
    ● 目标格式：原格式、PNG、JPG、WEBP、BMP、TIFF、GIF、ICO<br><br>

    <b>5. 图片分切裁剪</b><br><br>
    ● 分切模式：横向（上下切）、竖向（左右切）、网格（自定义行列数）<br>
    ● 目标格式：原格式、PNG、JPG、WEBP<br><br>

    <b>6. GIF 合成拼接</b><br><br>
    ● 两种模式：多图合成 GIF（每张图作为一帧）、多个 GIF 拼接（多个 GIF 合成一个）<br>
    ● 分组方式：按文件名前缀长度、每 N 个一组、按文件夹、所有文件<br>
    ● 播放速度：10~5000 ms，控制每帧播放延时<br>
    ● 循环次数：0=无限循环<br>
    ● 排列方式（拼接模式）：顺序播放（一个接一个播放）、同时叠加（多个 GIF 同时播放，拼在一个画面里）<br>
    ● 拼接方式（同时叠加）：水平、垂直、网格（自定义行列数）<br>
    ● 对齐方式（同时叠加）：按最短时长截断（短的播完就停，长的被截断）或按最长时长循环（长的播完才停，短的循环补齐）<br>
    ● 背景色 / 边距 / 间距（同时叠加）：自定义背景色（HEX）、边距、间距<br>
    ● 目标尺寸：保持原尺寸或自定义宽高，勾选「保持比例」避免变形<br>

    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """


def get_video_help_text():
    return """
    <h2>🎬 视频批量处理工具</h2>

    <br>FFmpeg 路径：需安装 <a href="https://ffmpeg.org/download.html#build-windows">FFmpeg</a>，程序自动检测，可手动指定路径<br>

    <br><b>1. 视频片段截取</b><br><br>
    ● 开始时间 / 结束时间：按设置时间截取视频片段<br>
    ● 目标格式：原格式、mp4、mkv、avi、mov<br>
    ● 重新编码：重新编码兼容性更好<br><br>

    <br><b>2. 视频转 GIF</b><br><br>    
    ● 开始时间 / 结束时间：按设置时间截取截取视频片段转为 GIF<br>
    ● 帧率：1~60 fps，越高越流畅（文件越大）<br>
    ● 尺寸：自定义宽高，支持保持比例<br>
    ● 颜色数：16~256 色，越多色彩越丰富（文件越大）<br>

    <br><b>3. 视频拼接合并</b><br><br>
    ● 分组方式：按文件名前缀长度、每 N 个一组、按文件夹、所有文件<br>
    ● 目标格式：mp4、mkv、avi、mov<br>
    ● 编码方式：直接合并（快速，要求视频参数一致）、重新编码（兼容，处理不同格式）<br>
    ● 编码器：libx264（推荐）、libx265（文件更小）、h264_nvenc、hevc_nvenc（显卡加速）<br>
    ● 预设：快速、平衡、高质量<br>

    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """