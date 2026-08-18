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
    ●【常规压缩】<br>
    &nbsp;&nbsp;&nbsp;预设：轻度 / 中等 / 强力 / 极强<br>
    &nbsp;&nbsp;&nbsp;目标分辨率：36~600 ppi，值越大越清晰，文件也越大<br>
    &nbsp;&nbsp;&nbsp;JPEG 质量：10~100%，值越大质量越高，文件也越大<br>
    ●【指定大小】<br>
    &nbsp;&nbsp;&nbsp;目标大小：输入期望的文件体积（支持 MB / KB）<br>
    &nbsp;&nbsp;&nbsp;精度范围：1~20%，达到目标 ± 精度值内即停止压缩，避免过度压缩<br>
    ● 转为灰度：勾选后转为灰度图像，减少文件体积；不勾选保留彩色<br>
    ● Ghostscript 路径：需安装 <a href="https://www.ghostscript.com/releases/gsdnld.html">Ghostscript</a>，程序自动检测，可手动指定路径<br>
    ● 检测文件大小：检测当前列表所有文件的体积大小<br><br>
    
    <b>2. PDF 格式转换</b><br><br>
    ●【PDF 转换】<br>
    &nbsp;&nbsp;&nbsp;目标格式：PDF / DOCX / XLSX / PPTX / JPG / PNG / TXT / HTML<br>
    &nbsp;&nbsp;&nbsp;页面范围：适用于 DOCX / XLSX / PPTX / JPG / PNG / TXT / HTML 格式（留空即全部）<br>
    &nbsp;&nbsp;&nbsp;合并所有表：适用于 XLSX 格式，勾选后多表合并为一张<br>
    &nbsp;&nbsp;&nbsp;DPI：72~600 ppi，适用于 JPG / PNG 格式<br>
    ●【Office 互转】<br>
    &nbsp;&nbsp;&nbsp;目标格式：DOC / DOCX / XLS / XLSX / PPT / PPTX<br>
    &nbsp;&nbsp;&nbsp;需安装 Microsoft Office 或 Libre Office<br><br>

    <b>3. 合并 PDF 页面</b><br><br>
    ● 分组方式：按文件名前缀长度 / 每 N 个一组 / 按文件夹 / 所有文件<br><br>

    <b>4. 组织 PDF 页面</b><br><br>
    ●【提取】<br>
    &nbsp;&nbsp;&nbsp;页面范围：指定需要提取的页面范围（留空即全部）<br>
    &nbsp;&nbsp;&nbsp;反向提取：勾选后提取除指定页面外的所有页面，生成一个新文件<br>
    ●【插入】<br>
    &nbsp;&nbsp;&nbsp;插入文件：选择需要插入的 PDF 文件<br>
    &nbsp;&nbsp;&nbsp;按序插入：勾选后将插入文件第 N 页对应插入第 N 个文件（页码总数 = 左侧文件数）<br>
    &nbsp;&nbsp;&nbsp;插入位置：插入至第 N 页之前或之后<br>
    ●【替换】<br>
    &nbsp;&nbsp;&nbsp;替换来源：选择来源 PDF 文件，并指定用于替换的页面范围（来源页数 = 目标页数）<br>
    &nbsp;&nbsp;&nbsp;替换目标：指定左侧文件列表中被替换的页面范围<br>
    ●【拆分】<br>
    &nbsp;&nbsp;&nbsp;拆分方式：按固定页数 / 按指定页面范围 / 按一级书签拆分<br>
    ●【重排】<br>
    &nbsp;&nbsp;&nbsp;页面范围：需要移动的页面范围（支持多个不连续范围）<br>
    &nbsp;&nbsp;&nbsp;插入位置：移动至第 N 页之前或之后<br>
    ●【删除】<br>
    &nbsp;&nbsp;&nbsp;页面范围：需要删除的页面范围（至少保留 1 页）<br>
    ● 检测页码：检测每个 PDF 文件的总页数<br><br>    

    <b>5. PDF 添加书签</b><br><br>
    ● 模式：插入书签 / 生成目录（基于已有书签生成目录页到第一页之前）/ 两者兼具<br>
    ● 编号范围：目录页自动编号，支持无编号、仅一级标题、多级标题<br>
    ● 编号样式：1 / 1.1 / 1.1.1 ｜ 一 /（一）/ 1. ｜ 第一章 / 第一节 / 第一条<br>
    ● 页码偏移量：正文从第 N 页开始时填入 N-1（如正文从第 3 页开始填 2）<br>
    ● 覆盖已有书签：勾选后覆盖现有书签，不勾选则追加<br>
    ● 全局书签列表：用 Tab 或空格分隔（层级 标题 页码），支持从文本文件导入<br>
    ● 双击「设置」列：可为单个文件独立编辑书签，留空则使用全局列表<br>
    ● 检测页码与书签：检测每个 PDF 的总页数和书签结构<br>
    ● 清除书签：清除每个 PDF 的书签内容<br><br>    

    <b>6. 调整 PDF 尺寸</b><br><br>
    ● 目标尺寸：A0 / A1 / A2 / A3 / A4 / A5 / A6 / Letter / Legal / 自定义（宽度 × 高度 cm）<br>
    ● 保持方向：勾选后自动识别页面横竖，避免内容变形<br>
    ● 内容位置：居中 / 左上 / 右上 / 左下 / 右下<br>
    ● 虚拟打印：勾选后通过 Ghostscript 重新生成 PDF，可修复签名和旋转问题<br>
    ● Ghostscript 路径：虚拟打印需安装 <a href="https://www.ghostscript.com/releases/gsdnld.html">Ghostscript</a>，程序自动检测，可手动指定路径<br>
    ● 检测页面尺寸：检测每个 PDF 的页面尺寸<br><br>

    <b>7. PDF 转扫描效果</b><br><br>
    ● 颜色模式：彩色 / 黑白<br>
    ● DPI：72~300 ppi，值越大越清晰，文件体积也越大<br>
    ● 质量：60~100%，值越大越清晰，文件体积也越大<br>
    ● 亮度：0~200%，控制画面明暗<br>
    ● 对比度：0~200%，控制画面层次<br>
    ● 模糊：0~100%，模拟扫描模糊效果<br>
    ● 噪点：0~100%，模拟扫描颗粒感<br>
    ● 发黄：0~100%，模拟纸张老化效果<br><br>

    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """


def get_img_help_text():
    return """
    <h2>🖼️ IMG 批量处理工具</h2>

    <br><b>1. 压缩图片文件</b><br><br>
    ● 预设：轻度 / 中等 / 强力 / 极强<br>
    ● 目标格式：原格式 / JPG / PNG / WEBP / GIF<br>
    ● 转为灰度：勾选后转为灰度图像，减少文件体积；不勾选保留彩色<br>
    ● 质量：1~100%，JPG / WEBP 值越大文件越大，PNG 值越大文件越小<br>   
    ● 缩放：50~100%，按比例缩小<br>    
    ● 最大颜色数：2~256，值越小文件越小，仅适用于 GIF 格式<br>
    ● 抽帧间隔：1~10，值越大文件越小，仅适用于 GIF 格式<br>
    ● 保留动画：勾选后保留所有帧，不勾选仅保留第一帧，仅适用于 GIF 格式<br><br>

    <b>2. 转换图片格式</b><br><br>
    ● 目标格式：PNG / JPG / WEBP / BMP / TIFF / GIF / ICO<br>
    ● 压缩等级：0~9，0 = 无压缩文件最大，9 = 最高压缩文件最小，仅适用于 PNG 格式<br>    
    ● 图片质量：1~100，值越大越清晰，仅适用于 JPG / WEBP 格式<br>    
    ● 填充白色背景：勾选后可避免透明区域变黑，仅适用于 JPG / BMP / ICO 格式<br>
    ● LZW 压缩：勾选后使用 LZW 无损压缩减小文件体积，仅适用于 TIFF 格式<br><br>

    <b>3. 图片拼接合并</b><br><br>
    ● 分组方式：按文件名前缀长度 / 每 N 个一组 / 按文件夹 / 所有文件<br>
    ● 目标格式：PNG / JPG / WEBP<br>    
    ● 目标尺寸：原尺寸 / 自定义（宽度 × 高度）<br>
    ● 保持比例：勾选后可避免变形<br>
    ● 拼接方式：垂直 / 水平 / 网格（列数）/ 台词（偏移）<br>
    ● 背景色：支持自定义背景色<br>
    ● 间距：0~200 px，控制拼接图片的间距<br>    
    ● 偏移：负值向上偏移（去除黑边），正值向下偏移（保留黑边）<br>
    ● 标签设置：勾选「添加序号」或「添加文件名」生效，可显示在上方或下方<br>
    ● 标题设置：标题不为空时生效，可显示在顶部或底部<br><br>

    <b>4. 调整图片大小</b><br><br>
    ● 重采样算法：高质量（LANCZOS）/ 均衡（BICUBIC）/ 快速（BILINEAR）<br>
    ● 目标格式：原格式 / PNG / JPG / WEBP / BMP / TIFF / GIF / ICO<br>
    ● 目标尺寸：原尺寸 / 尺寸（像素）/ 尺寸（%）/ 短边约束 / 长边约束<br>
    ● 保持比例：勾选后可避免变形<br>
    ● 目标分辨率：勾选「指定 DPI」后启用，可自定义 DPI 值；不勾选则保留原图 DPI<br><br>

    <b>5. 图片分切裁剪</b><br><br>
    ●【分切】<br>
    &nbsp;&nbsp;&nbsp;行数：水平方向切割的份数<br>
    &nbsp;&nbsp;&nbsp;列数：垂直方向切割的份数<br>
    ●【裁剪】<br>
    &nbsp;&nbsp;&nbsp;裁剪方式：比例 / 尺寸<br>
    &nbsp;&nbsp;&nbsp;裁剪比例：1:1 / 4:3 / 16:9 / 3:4 / 9:16 / 自定义（宽 : 高）<br>
    &nbsp;&nbsp;&nbsp;裁剪尺寸：小一寸 / 一寸 / 大一寸 / 小二寸 / 二寸 / 大二寸 / 自定义（宽 × 高 mm）<br>
    &nbsp;&nbsp;&nbsp;裁剪位置：居中 / 左上 / 左下 / 右上 / 右下<br>
    ● 目标格式：原格式 / PNG / JPG / WEBP<br><br>

    <b>6. GIF 合成拼接</b><br><br>
    ● 合成模式：多图合成 GIF / 多个 GIF 拼接<br>
    ● 分组方式：按文件名前缀长度 / 每 N 个一组 / 按文件夹 / 所有文件<br>
    ● 速度：10~5000 ms，控制每帧播放延时<br>
    ● 重复：循环次数，0 = 无限循环<br>
    ● 目标尺寸：保持原尺寸 / 自定义（宽度 × 高度）<br>
    ● 保持比例：勾选后可避免变形<br>
    ●【多个 GIF 拼接】<br>
    &nbsp;&nbsp;&nbsp;排列方式：顺序播放（逐个播放）/ 同时叠加（多个 GIF 同时播放，拼在一个画面里）<br>
    &nbsp;&nbsp;&nbsp;时间同步：按最短时长截断（短的播完即停）/ 按最长时长循环（长的播完才停）<br>
    &nbsp;&nbsp;&nbsp;拼接方式：水平 / 垂直 / 网格（行列数）<br>
    &nbsp;&nbsp;&nbsp;背景色：支持自定义背景色<br>
    &nbsp;&nbsp;&nbsp;边距：控制拼接内容与外部的距离<br>
    &nbsp;&nbsp;&nbsp;间距：控制拼接内容的间距<br>   
    
    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """


def get_video_help_text():
    return """
    <h2>🎬 视频批量处理工具</h2>

    <br>FFmpeg 路径：需安装 <a href="https://ffmpeg.org/download.html#build-windows">FFmpeg</a>，程序自动检测，可手动指定路径<br>
   
    <br><b>1. 视频章节编辑</b><br><br>
    ● 全局书签列表：用 Tab 或空格分隔（时间 标题），支持从文本文件导入<br>
    ● 双击「设置」列：可为单个文件独立编辑章节，留空则使用全局列表<br>
    ● 检测章节标记：检测每个视频文件现有的章节结构<br>
    ● 清除章节：清除视频文件中的所有章节标记<br><br>

    <br><b>2. 视频片段截取</b><br><br>
    ● 截取时间：设置开始时间和结束时间，截取指定片段<br>
    ● 目标格式：原格式 / mp4 / mkv / avi / mov<br>
    ● 重新编码：勾选后兼容性更好（速度较慢），不勾选直接复制（速度快，要求编码参数一致）<br><br>

    <br><b>3. 视频拼接合并</b><br><br>
    ● 分组方式：按文件名前缀长度 / 每 N 个一组 / 按文件夹 / 所有文件<br>
    ● 目标格式：mp4 / mkv / avi / mov<br>
    ● 保留章节标记：勾选后合并时自动生成章节，章节标题为源文件名<br>
    ● 编码方式：直接合并（快速，要求视频参数一致）/ 重新编码（兼容，处理不同格式）<br>
    ● 编码预设：快速 / 平衡 / 高质量<br>
    ● 视频编码器：libx264（推荐）/ libx265（文件更小）/ h264_nvenc / hevc_nvenc<br><br>

    <br><b>4. 视频转 GIF</b><br><br>    
    ● 截取时间：设置开始时间和结束时间，截取指定片段转为 GIF<br>
    ● 帧率：1~60 fps，值越高动画越流畅，文件也越大<br>
    ● 颜色数：16~256 色，值越高色彩越丰富，文件也越大<br>
    ● 目标尺寸：自定义宽度和高度（px）<br>
    ● 保持比例：勾选后按原始比例缩放，避免变形<br>

    <p style="text-align:center; color:#888; font-size:12px;">
    © 张小鱼（Aria）· contact@arianote.top
    </p>    
    """