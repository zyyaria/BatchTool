# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

from . import pdf_resize, pdf_merge, pdf_compress, pdf_convert, pdf_scanned, pdf_outline, pdf_organize
from . import img_convert, img_resize, img_compress, img_stitch, img_split, img_gifmaker
from . import video_merge, video_cut, video_gifmaker

PDF_FEATURES = [
    {"name": "压缩PDF文件", "module": pdf_compress},
    {"name": "调整PDF尺寸", "module": pdf_resize},
    {"name": "合并PDF页面", "module": pdf_merge},
    {"name": "组织PDF页面", "module": pdf_organize},
    {"name": "PDF格式转换", "module": pdf_convert},
    {"name": "PDF添加书签", "module": pdf_outline},
    {"name": "PDF转扫描效果", "module": pdf_scanned},
]

IMG_FEATURES = [
    {"name": "转换图片格式", "module": img_convert},
    {"name": "调整图片大小", "module": img_resize},
    {"name": "压缩图片文件", "module": img_compress},
    {"name": "图片拼接合并", "module": img_stitch},
    {"name": "图片分切裁剪", "module": img_split},
    {"name": "多图合成GIF", "module": img_gifmaker},
]

VIDEO_FEATURES = [
    {"name": "视频拼接合并", "module": video_merge},
    {"name": "视频片段截取", "module": video_cut},
    {"name": "视频转GIF图片", "module": video_gifmaker},
]