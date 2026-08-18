# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import io
import numpy as np
from PIL import Image
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
    QComboBox, QSizePolicy
)

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


class ScanPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_color = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["彩色", "黑白"])
        self.color_combo.setCurrentText("彩色")
        self.color_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_color.addWidget(QLabel("颜色模式:"))
        row_color.addWidget(self.color_combo, 1)
        layout.addLayout(row_color)

        row_dpi_quality = QHBoxLayout()
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 300)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" ppi")
        self.dpi_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(60, 100)
        self.quality_spin.setValue(92)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_dpi_quality.addWidget(QLabel("DPI:"))
        row_dpi_quality.addWidget(self.dpi_spin, 1)
        row_dpi_quality.addWidget(QLabel("质量:"))
        row_dpi_quality.addWidget(self.quality_spin, 1)
        layout.addLayout(row_dpi_quality)

        row_brightness = QHBoxLayout()
        self.brightness_spin = QSpinBox()
        self.brightness_spin.setRange(0, 200)
        self.brightness_spin.setValue(100)
        self.brightness_spin.setSuffix(" %")
        self.brightness_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.contrast_spin = QSpinBox()
        self.contrast_spin.setRange(0, 200)
        self.contrast_spin.setValue(100)
        self.contrast_spin.setSuffix(" %")
        self.contrast_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_brightness.addWidget(QLabel("亮度:"))
        row_brightness.addWidget(self.brightness_spin, 1)
        row_brightness.addWidget(QLabel("对比度:"))
        row_brightness.addWidget(self.contrast_spin, 1)
        layout.addLayout(row_brightness)

        row_blur = QHBoxLayout()
        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(0, 100)
        self.blur_spin.setValue(0)
        self.blur_spin.setSuffix(" %")
        self.blur_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.noise_spin = QSpinBox()
        self.noise_spin.setRange(0, 100)
        self.noise_spin.setValue(0)
        self.noise_spin.setSuffix(" %")
        self.noise_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_blur.addWidget(QLabel("模糊:"))
        row_blur.addWidget(self.blur_spin, 1)
        row_blur.addWidget(QLabel("噪点:"))
        row_blur.addWidget(self.noise_spin, 1)
        layout.addLayout(row_blur)

        row_yellow = QHBoxLayout()
        self.yellow_spin = QSpinBox()
        self.yellow_spin.setRange(0, 100)
        self.yellow_spin.setValue(0)
        self.yellow_spin.setSuffix(" %")
        self.yellow_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_yellow.addWidget(QLabel("发黄:"))
        row_yellow.addWidget(self.yellow_spin, 1)
        layout.addLayout(row_yellow)

        layout.addStretch()

        self.color_combo.currentTextChanged.connect(self.changed)
        self.dpi_spin.valueChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.brightness_spin.valueChanged.connect(self.changed)
        self.contrast_spin.valueChanged.connect(self.changed)
        self.blur_spin.valueChanged.connect(self.changed)
        self.noise_spin.valueChanged.connect(self.changed)
        self.yellow_spin.valueChanged.connect(self.changed)


def build_panel():
    """构建面板实例"""
    return ScanPanel()


def collect_settings(panel):
    """收集面板设置"""
    return {
        "color": panel.color_combo.currentText(),
        "dpi": panel.dpi_spin.value(),
        "quality": panel.quality_spin.value(),
        "brightness": panel.brightness_spin.value() / 100.0,
        "contrast": panel.contrast_spin.value() / 100.0,
        "blur": panel.blur_spin.value() / 100.0,
        "noise": panel.noise_spin.value() / 100.0,
        "yellow": panel.yellow_spin.value() / 100.0,
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    mode = "黑白" if settings.get("color") == "黑白" else "彩色"
    dpi = settings.get("dpi", 150)
    quality = settings.get("quality", 92)
    brightness = settings.get("brightness", 1.0) * 100
    contrast = settings.get("contrast", 1.0) * 100
    blur = settings.get("blur", 0.0) * 100
    noise = settings.get("noise", 0.0) * 100
    yellow = settings.get("yellow", 0.0) * 100
    desc = f"扫描({mode})，DPI={dpi}，输出质量{quality}%"
    desc += f"，亮度{brightness:.0f}%，对比{contrast:.0f}%"
    if blur > 0:
        desc += f"，模糊{blur:.0f}%"
    if noise > 0:
        desc += f"，噪点{noise:.0f}%"
    if yellow > 0:
        desc += f"，发黄{yellow:.0f}%"
    for it in items:
        it.preview_extra = {"A": desc}


def _apply_yellow_tint(img, intensity):
    """为图像添加发黄效果"""
    if intensity <= 0:
        return img
    img_np = np.array(img).astype(np.float32)
    img_np[:, :, 0] += intensity * 30
    img_np[:, :, 1] += intensity * 15
    img_np[:, :, 2] -= intensity * 10
    img_np = np.clip(img_np, 0, 255)
    return Image.fromarray(img_np.astype(np.uint8))


def _generate_paper_texture(width, height):
    """生成极细腻的灰度纹理"""
    import numpy as np
    from PIL import Image, ImageFilter
    small_w = max(4, width // 12)
    small_h = max(4, height // 12)
    base = np.random.randn(small_h, small_w).astype(np.float32)
    tex = Image.fromarray(((base + 1) * 127.5).astype(np.uint8), 'L')
    tex = tex.resize((width, height), Image.Resampling.BICUBIC)
    tex = tex.filter(ImageFilter.GaussianBlur(radius=3.0))
    tex_arr = np.array(tex).astype(np.float32) / 255.0 - 0.5
    tex_arr = tex_arr / np.std(tex_arr)
    return tex_arr


def _apply_scan_effects(img, settings):
    """应用扫描效果"""
    import numpy as np
    from PIL import Image, ImageFilter, ImageEnhance
    img = img.convert('RGB')
    w, h = img.size
    brightness = settings.get("brightness", 1.0)
    if brightness != 1.0:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
    contrast = settings.get("contrast", 1.0)
    if contrast != 1.0:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
    blur = settings.get("blur", 0.0)
    if blur > 0:
        radius = blur * 3
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
    arr = np.array(img).astype(np.float32)
    texture = _generate_paper_texture(w, h)
    strength = 0.0005
    offset = texture * strength * 255.0
    arr += offset[:, :, np.newaxis]
    noise_level = settings.get("noise", 0.0)
    if noise_level > 0:
        noise = np.random.randn(h, w) * noise_level * 30
        for c in range(3):
            arr[:, :, c] += noise
    yellow = settings.get("yellow", 0.0)
    if yellow > 0:
        img_temp = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        img_temp = _apply_yellow_tint(img_temp, yellow)
        arr = np.array(img_temp).astype(np.float32)
    arr = np.clip(arr, 0, 255)
    result = Image.fromarray(arr.astype(np.uint8))
    result = result.convert('RGB')
    return result


def _pdf_to_scanned_images(input_pdf, settings, progress_callback=None):
    from PySide6.QtWidgets import QApplication
    if pdfium is None:
        raise RuntimeError("pypdfium2 未安装，请执行: pip install pypdfium2")
    pdf = pdfium.PdfDocument(input_pdf)
    images = []
    page_sizes = []
    dpi = settings.get("dpi", 150)
    scale = dpi / 72.0
    total = len(pdf)
    for i in range(total):
        if progress_callback:
            progress_callback(i+1, total)
        if i % 2 == 0:
            QApplication.processEvents()
        page = pdf[i]
        if hasattr(page, 'get_size'):
            w, h = page.get_size()
        elif hasattr(page, 'get_rect'):
            rect = page.get_rect()
            w, h = rect[2] - rect[0], rect[3] - rect[1]
        elif hasattr(page, 'rect'):
            rect = page.rect
            w, h = rect[2] - rect[0], rect[3] - rect[1]
        else:
            raise AttributeError("无法获取页面尺寸，请检查 pypdfium2 版本")
        page_sizes.append((w, h))
        bitmap = page.render(scale=scale, rotation=0)
        img = bitmap.to_pil()
        if settings.get("color") == "黑白":
            img = img.convert("L").convert("RGB")
        img = _apply_scan_effects(img, settings)
        images.append(img)
    pdf.close()
    return images, page_sizes


def run_task(file_item, settings):
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_name = file_item.output_name or os.path.basename(src)
    if not out_name.lower().endswith('.pdf'):
        out_name += '.pdf'
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name
    images, page_sizes = _pdf_to_scanned_images(src, settings)
    if not images:
        raise RuntimeError("未生成任何图片")
    try:
        import fitz
    except ImportError:
        raise RuntimeError("需要 PyMuPDF (fitz) 来保存 PDF，请安装: pip install PyMuPDF")
    doc = fitz.open()
    quality = settings.get("quality", 92)
    for idx, img in enumerate(images):
        img = img.convert('RGB')
        w, h = page_sizes[idx]
        page = doc.new_page(width=w, height=h)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality, optimize=True, subsampling=0)
        img.close()
        page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(out_path)
    doc.close()
    file_item.status = "完成"