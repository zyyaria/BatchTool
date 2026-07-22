# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QCheckBox, QSizePolicy
)
from core.utils import ensure_image_mode

try:
    from PIL import Image
except ImportError:
    Image = None


class ConvertPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF", "ICO"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fill_check = QCheckBox("填充白色背景")
        self.fill_check.setChecked(True)
        self.fill_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        row_format.addWidget(self.fill_check)
        layout.addLayout(row_format)

        row_quality = QHBoxLayout()
        self.quality_label = QLabel("图片质量:")
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(100)
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_quality.addWidget(self.quality_label)
        row_quality.addWidget(self.quality_spin, 1)        
        layout.addLayout(row_quality)

        layout.addStretch()

        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.fill_check.stateChanged.connect(self.changed)

        self._on_format_changed()
        
    def _on_format_changed(self):
        """目标格式切换"""
        fmt = self.format_combo.currentText()
        self.fill_check.setVisible(fmt in ("JPG", "BMP", "ICO"))
        show_quality = fmt in ("PNG", "JPG", "WEBP")
        self.quality_label.setVisible(show_quality)
        self.quality_spin.setVisible(show_quality)
        if show_quality:
            if fmt == "PNG":
                self.quality_label.setText("图片质量:")
                self.quality_spin.setSuffix("（100=无压缩，1=极限压缩）")
                self.quality_spin.setValue(100)
            else:
                self.quality_label.setText("图片质量:")
                self.quality_spin.setSuffix(" %（越大越清晰）")
                self.quality_spin.setValue(100)
        else:
            self.quality_spin.setValue(0)
        self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例""" 
    return ConvertPanel()


def collect_settings(panel: ConvertPanel) -> dict:
    """收集面板设置"""
    return {
        "target_format": panel.format_combo.currentText().lower(),
        "quality": panel.quality_spin.value(),
        "fill_white_bg": panel.fill_check.isChecked(),
    }


def prepare_preview(items, settings: dict):
    """生成预览信息"""
    fmt = settings.get("target_format", "png").lower()
    for it in items:
        quality = settings.get("quality", 90)
        fill_bg = settings.get("fill_white_bg", True)
        if fmt in ("png", "jpg", "webp"):
            if fmt == "png":
                quality_desc = f"压缩等级{int((100-quality)/100*9)}"
            else:
                quality_desc = f"质量{quality}%"
        else:
            quality_desc = "无损"
        bg_desc = "白底" if fill_bg else "保留透明"
        it.preview_extra = {"A": f"→ {fmt.upper()}（{quality_desc}，{bg_desc}）"}


def run_task(file_item, settings: dict):
    """执行单个图片格式转换任务"""
    if Image is None:
        raise RuntimeError("缺少 Pillow 库，请安装: pip install Pillow")
    src = file_item.input_path
    target_fmt = settings.get("target_format", "png")
    quality = settings.get("quality", 90)
    fill_white = settings.get("fill_white_bg", True)
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    src_ext = os.path.splitext(src)[1][1:].lower()
    if src_ext == target_fmt and quality >= 90 and target_fmt not in ("gif", "ico", "bmp", "tiff"):
        shutil.copy2(src, out_path)
        file_item.status = "完成"
        return
    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图片: {e}")
    im = ensure_image_mode(im, target_fmt, fill_white=fill_white)
    save_kwargs = {}
    if target_fmt == "jpg":
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif target_fmt == "webp":
        save_kwargs["quality"] = quality
        save_kwargs["lossless"] = False
    elif target_fmt == "png":
        compress_level = int((100 - quality) / 100 * 9)
        save_kwargs["compress_level"] = compress_level
        save_kwargs["optimize"] = True
    elif target_fmt == "gif":
        save_kwargs["optimize"] = True
    save_format = target_fmt.upper()
    if save_format == "JPG":
        save_format = "JPEG"
    try:
        im.save(out_path, format=save_format, **save_kwargs)
    except Exception as e:
        raise RuntimeError(f"保存失败: {e}")
    finally:
        im.close()
    file_item.status = "完成"