# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import io
import fitz
import random
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox, 
    QPushButton, QSizePolicy
)


class ScanPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预设："))
        self.btn_hd = QPushButton("高清扫描")
        self.btn_print_color = QPushButton("彩色打印")
        self.btn_print_bw = QPushButton("黑白打印")
        self.btn_hd.clicked.connect(lambda: self._apply_preset("hd"))
        self.btn_print_color.clicked.connect(lambda: self._apply_preset("print_color"))
        self.btn_print_bw.clicked.connect(lambda: self._apply_preset("print_bw"))
        preset_row.addWidget(self.btn_hd, 1)
        preset_row.addWidget(self.btn_print_color, 1)
        preset_row.addWidget(self.btn_print_bw, 1)
        main_layout.addLayout(preset_row)

        label_basic = QLabel("基本设置：")
        label_basic.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        main_layout.addWidget(label_basic)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("颜色模式:"))
        self.color_mode = QComboBox()
        self.color_mode.addItems(["彩色", "黑白"])
        self.color_mode.setCurrentText("彩色")
        color_row.addWidget(self.color_mode, 1)
        main_layout.addLayout(color_row)

        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("分辨率:"))
        self.dpi = QSpinBox()
        self.dpi.setRange(72, 600)
        self.dpi.setValue(150)
        self.dpi.setSuffix(" ppi")
        dpi_row.addWidget(self.dpi, 1)
        main_layout.addLayout(dpi_row)

        label_adjust = QLabel("图片调节：")
        label_adjust.setStyleSheet("font-weight: 600; margin-top: 4px; margin-left: -3px;")
        main_layout.addWidget(label_adjust)

        brightness_row = QHBoxLayout()
        brightness_row.addWidget(QLabel("亮度:"))
        self.brightness = QSpinBox()
        self.brightness.setRange(0, 200)
        self.brightness.setValue(100)
        self.brightness.setSuffix(" %")
        brightness_row.addWidget(self.brightness, 1)
        main_layout.addLayout(brightness_row)

        contrast_row = QHBoxLayout()
        contrast_row.addWidget(QLabel("对比度:"))
        self.contrast = QSpinBox()
        self.contrast.setRange(0, 200)
        self.contrast.setValue(100)
        self.contrast.setSuffix(" %")
        contrast_row.addWidget(self.contrast, 1)
        main_layout.addLayout(contrast_row)

        blur_row = QHBoxLayout()
        blur_row.addWidget(QLabel("模糊:"))
        self.blur = QSpinBox()
        self.blur.setRange(0, 100)
        self.blur.setValue(10)
        self.blur.setSuffix(" %")
        blur_row.addWidget(self.blur, 1)
        main_layout.addLayout(blur_row)

        noise_row = QHBoxLayout()
        noise_row.addWidget(QLabel("噪点:"))
        self.noise = QSpinBox()
        self.noise.setRange(0, 100)
        self.noise.setValue(5)
        self.noise.setSuffix(" %")
        noise_row.addWidget(self.noise, 1)
        main_layout.addLayout(noise_row)

        yellow_row = QHBoxLayout()
        yellow_row.addWidget(QLabel("发黄:"))
        self.yellow = QSpinBox()
        self.yellow.setRange(0, 100)
        self.yellow.setValue(0)
        self.yellow.setSuffix(" %")
        yellow_row.addWidget(self.yellow, 1)
        main_layout.addLayout(yellow_row)

        main_layout.addStretch()

        self.btn_reset = QPushButton("重置为默认值")
        self.btn_reset.clicked.connect(self._apply_default)
        main_layout.addWidget(self.btn_reset)

        self.color_mode.currentTextChanged.connect(self.changed)
        self.dpi.valueChanged.connect(self.changed)
        self.brightness.valueChanged.connect(self.changed)
        self.contrast.valueChanged.connect(self.changed)
        self.blur.valueChanged.connect(self.changed)
        self.noise.valueChanged.connect(self.changed)
        self.yellow.valueChanged.connect(self.changed)

    def _apply_preset(self, preset_name: str):
        presets = {
            "hd":          {"color": "彩色", "dpi": 300, "brightness": 100, "contrast": 100, "blur": 0, "noise": 0, "yellow": 0},
            "print_color": {"color": "彩色", "dpi": 150, "brightness": 100, "contrast": 110, "blur": 5, "noise": 3, "yellow": 0},
            "print_bw":    {"color": "黑白", "dpi": 150, "brightness": 100, "contrast": 120, "blur": 5, "noise": 3, "yellow": 0},
        }
        p = presets.get(preset_name)
        if not p:
            return
        self.color_mode.setCurrentText(p["color"])
        self.dpi.setValue(p["dpi"])
        self.brightness.setValue(p["brightness"])
        self.contrast.setValue(p["contrast"])
        self.blur.setValue(p["blur"])
        self.noise.setValue(p["noise"])
        self.yellow.setValue(p["yellow"])
        self.changed.emit()

    def _apply_default(self):
        self.color_mode.setCurrentText("彩色")
        self.dpi.setValue(150)
        self.brightness.setValue(100)
        self.contrast.setValue(100)
        self.blur.setValue(10)
        self.noise.setValue(5)
        self.yellow.setValue(0)
        self.changed.emit()

    def get_settings(self):
        return {
            "color_mode": self.color_mode.currentText(),
            "dpi": self.dpi.value(),
            "brightness": self.brightness.value() / 100.0,
            "contrast": self.contrast.value() / 100.0,
            "blur": self.blur.value() / 100.0,
            "noise": self.noise.value() / 100.0,
            "yellow": self.yellow.value() / 100.0,
        }


def build_panel() -> QWidget:
    return ScanPanel()


def collect_settings(panel: ScanPanel) -> dict:
    return panel.get_settings()


def prepare_preview(items, settings):
    mode = "黑白" if settings.get("color_mode") == "黑白" else "彩色"
    dpi = settings.get("dpi", 150)
    blur = settings.get("blur", 0) * 100
    for it in items:
        it.preview_extra = {"A": f"扫描({mode})，DPI:{dpi}，模糊:{blur:.0f}%"}


def _apply_yellow_tint(img, intensity):
    if intensity <= 0:
        return img
    img_np = np.array(img).astype(np.float32)
    yellow_layer = np.full_like(img_np, (255, 255, 0), dtype=np.float32)
    img_np = img_np * (1 - intensity) + yellow_layer * intensity
    img_np = np.clip(img_np, 0, 255).astype(np.uint8)
    return Image.fromarray(img_np)


def _pdf_to_scanned_images(input_pdf: str, settings: dict):
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

        if settings["color_mode"] == "彩色" and settings["yellow"] > 0:
            img = _apply_yellow_tint(img, settings["yellow"])

        if settings["color_mode"] == "黑白":
            img = img.convert("L")

        images.append(img)

    doc.close()
    return images


def run_task(file_item, settings: dict):
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
        file_item.status = "完成"
    else:
        raise RuntimeError("未生成任何图片")