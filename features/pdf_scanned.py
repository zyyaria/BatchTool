# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import io
import fitz
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QSizePolicy
)


class ScanPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_preset = QHBoxLayout()
        self.scan_btn = QPushButton("高清扫描")
        self.scan_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.print_color_btn = QPushButton("彩色打印")
        self.print_color_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.print_bw_btn = QPushButton("黑白打印")
        self.print_bw_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_preset.addWidget(QLabel("预设:"))
        row_preset.addWidget(self.scan_btn, 1)
        row_preset.addWidget(self.print_color_btn, 1)
        row_preset.addWidget(self.print_bw_btn, 1)
        layout.addLayout(row_preset)

        basic_label = QLabel("基本设置:")
        basic_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        layout.addWidget(basic_label)

        row_color = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["彩色", "黑白"])
        self.color_combo.setCurrentText("彩色")
        self.color_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 600)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" ppi")
        self.dpi_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_color.addWidget(QLabel("颜色模式:"))
        row_color.addWidget(self.color_combo, 1)
        row_color.addWidget(QLabel("分辨率:"))
        row_color.addWidget(self.dpi_spin, 1)
        layout.addLayout(row_color)

        adjust_label = QLabel("图片调节:")
        adjust_label.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        layout.addWidget(adjust_label)

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
        self.blur_spin.setValue(10)
        self.blur_spin.setSuffix(" %")
        self.blur_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.noise_spin = QSpinBox()
        self.noise_spin.setRange(0, 100)
        self.noise_spin.setValue(5)
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

        self.reset_btn = QPushButton("重置为默认值")
        self.reset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.reset_btn, 1)

        layout.addStretch()
        
        self.scan_btn.clicked.connect(lambda: self._apply_preset("hd"))
        self.print_color_btn.clicked.connect(lambda: self._apply_preset("print_color"))
        self.print_bw_btn.clicked.connect(lambda: self._apply_preset("print_bw"))
        self.color_combo.currentTextChanged.connect(self.changed)
        self.dpi_spin.valueChanged.connect(self.changed)
        self.brightness_spin.valueChanged.connect(self.changed)
        self.contrast_spin.valueChanged.connect(self.changed)
        self.blur_spin.valueChanged.connect(self.changed)
        self.noise_spin.valueChanged.connect(self.changed)
        self.yellow_spin.valueChanged.connect(self.changed)
        self.reset_btn.clicked.connect(self._apply_default)

    def _apply_preset(self, preset_name: str):
        """应用预设参数"""
        presets = {
            "hd":          {"color": "彩色", "dpi": 300, "brightness": 100, "contrast": 100, "blur": 0, "noise": 0, "yellow": 0},
            "print_color": {"color": "彩色", "dpi": 150, "brightness": 100, "contrast": 110, "blur": 5, "noise": 3, "yellow": 0},
            "print_bw":    {"color": "黑白", "dpi": 150, "brightness": 100, "contrast": 120, "blur": 5, "noise": 3, "yellow": 0},
        }
        p = presets.get(preset_name)
        if not p:
            return
        self.color_combo.setCurrentText(p["color"])
        self.dpi_spin.setValue(p["dpi"])
        self.brightness_spin.setValue(p["brightness"])
        self.contrast_spin.setValue(p["contrast"])
        self.blur_spin.setValue(p["blur"])
        self.noise_spin.setValue(p["noise"])
        self.yellow_spin.setValue(p["yellow"])
        self.changed.emit()
        
    def _apply_default(self):
        """重置为默认值参数"""
        self.color_combo.setCurrentText("彩色")
        self.dpi_spin.setValue(150)
        self.brightness_spin.setValue(100)
        self.contrast_spin.setValue(100)
        self.blur_spin.setValue(10)
        self.noise_spin.setValue(5)
        self.yellow_spin.setValue(0)
        self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return ScanPanel()


def collect_settings(panel: ScanPanel) -> dict:
    """收集面板设置"""
    return {
        "color": panel.color_combo.currentText(),
        "dpi": panel.dpi_spin.value(),
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
    brightness = settings.get("brightness", 1.0) * 100
    contrast = settings.get("contrast", 1.0) * 100
    blur = settings.get("blur", 0.0) * 100
    noise = settings.get("noise", 0.0) * 100
    yellow = settings.get("yellow", 0.0) * 100
    desc = f"扫描({mode})，DPI={dpi}，亮度{brightness:.0f}%，对比{contrast:.0f}%，模糊{blur:.0f}%，噪点{noise:.0f}%"
    if yellow > 0:
        desc += f"，发黄{yellow:.0f}%"
    for it in items:
        it.preview_extra = {"A": desc}


def _apply_yellow_tint(img, intensity):
    """为图像添加发黄效果"""
    if intensity <= 0:
        return img
    img_np = np.array(img).astype(np.float32)
    yellow_layer = np.full_like(img_np, (255, 255, 0), dtype=np.float32)
    img_np = img_np * (1 - intensity) + yellow_layer * intensity
    img_np = np.clip(img_np, 0, 255).astype(np.uint8)
    return Image.fromarray(img_np)


def _pdf_to_scanned_images(input_pdf: str, settings: dict):
    """将 PDF 页面转换为扫描效果图片列表"""
    doc = fitz.open(input_pdf)
    images = []
    dpi = settings["dpi"]
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(settings["brightness"])
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(settings["contrast"])
        blur_radius = settings["blur"] * 2
        if blur_radius > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        noise_level = int(settings["noise"] * 50)
        if noise_level > 0:
            img_np = np.array(img)
            noise = np.random.randint(-noise_level, noise_level, img_np.shape, dtype='int16')
            img_np = np.clip(img_np.astype('int16') + noise, 0, 255).astype('uint8')
            img = Image.fromarray(img_np)
        if settings["color"] == "彩色" and settings["yellow"] > 0:
            img = _apply_yellow_tint(img, settings["yellow"])
        if settings["color"] == "黑白":
            img = img.convert("L")
        images.append(img)
    doc.close()
    return images


def run_task(file_item, settings: dict):
    """执行单个 PDF 扫描效果任务"""
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_name = file_item.output_name
    if not out_name:
        out_name = os.path.basename(src)
    if not out_name.lower().endswith('.pdf'):
        out_name += '.pdf'
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name
    images = _pdf_to_scanned_images(src, settings)
    if images:
        images[0].save(out_path, "PDF", save_all=True, append_images=images[1:])
        for img in images:
            img.close()
        file_item.status = "完成"
    else:
        raise RuntimeError("未生成任何图片")