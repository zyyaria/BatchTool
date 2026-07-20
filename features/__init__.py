# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import img_convert, img_resize, img_compress, img_merge, img_split, img_gifmaker, img_gifmerge
from . import pdf_resize, pdf_merge, pdf_compress, pdf_convert, pdf_scanned, pdf_outline, pdf_organize
from . import video_merge, video_cut, video_gifmaker


IMG_FEATURES = [
    {"name": "压缩图片文件", "module": img_compress},
    {"name": "转换图片格式", "module": img_convert},
    {"name": "多图合成 GIF", "module": img_gifmaker},
    {"name": "动图拼接合并", "module": img_gifmerge},    
    {"name": "静图拼接合并", "module": img_merge},
    {"name": "调整图片大小", "module": img_resize},
    {"name": "图片分切裁剪", "module": img_split},
]

PDF_FEATURES = [
    {"name": "压缩 PDF 文件", "module": pdf_compress},
    {"name": "PDF 格式转换", "module": pdf_convert},
    {"name": "合并 PDF 页面", "module": pdf_merge},
    {"name": "组织 PDF 页面", "module": pdf_organize},
    {"name": "PDF 添加书签", "module": pdf_outline},
    {"name": "调整 PDF 尺寸", "module": pdf_resize},
    {"name": "PDF 转扫描效果", "module": pdf_scanned},
]

VIDEO_FEATURES = [
    {"name": "视频片段截取", "module": video_cut},
    {"name": "视频转 GIF", "module": video_gifmaker},
    {"name": "视频拼接合并", "module": video_merge},
]