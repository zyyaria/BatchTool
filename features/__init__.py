# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import img_compress, img_convert, img_merge, img_resize, img_split, img_to_gif
from . import pdf_compress, pdf_convert, pdf_merge, pdf_organize, pdf_outline, pdf_resize, pdf_scanned
from . import video_cut, video_to_gif, video_merge


IMG_FEATURES = [
    {"name": "压缩图片文件", "module": img_compress},
    {"name": "转换图片格式", "module": img_convert},
    {"name": "图片拼接合并", "module": img_merge},     
    {"name": "调整图片大小", "module": img_resize},
    {"name": "图片分切裁剪", "module": img_split},    
    {"name": "GIF 合成拼接", "module": img_to_gif},    
]

PDF_FEATURES = [
    {"name": "压缩 PDF 文件", "module": pdf_compress},
    {"name": "PDF 格式转换", "module": pdf_convert},
    {"name": "合并 PDF 文件", "module": pdf_merge},
    {"name": "组织 PDF 页面", "module": pdf_organize},
    {"name": "PDF 添加书签", "module": pdf_outline},
    {"name": "调整 PDF 尺寸", "module": pdf_resize},
    {"name": "PDF 转扫描效果", "module": pdf_scanned},
]

VIDEO_FEATURES = [
    {"name": "视频片段截取", "module": video_cut},
    {"name": "视频转 GIF", "module": video_to_gif},
    {"name": "视频拼接合并", "module": video_merge},
]