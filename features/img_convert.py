# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import shutil
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QCheckBox
)
from core.utils import ensure_image_mode


try:
    from PIL import Image
except ImportError:
    Image = None


class ConvertPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("目标格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF", "ICO"])
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        fmt_row.addWidget(self.format_combo, 1)

        self.bg_check = QCheckBox("填充白色背景")
        self.bg_check.setChecked(True)
        fmt_row.addWidget(self.bg_check)

        layout.addLayout(fmt_row)

        quality_row = QHBoxLayout()
        self.quality_label = QLabel("压缩质量:")
        quality_row.addWidget(self.quality_label)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(100)
        quality_row.addWidget(self.quality_spin, 1)
        layout.addLayout(quality_row)

        layout.addStretch()

        self._on_format_changed()

        self.format_combo.currentIndexChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.bg_check.stateChanged.connect(self.changed)

    def _on_format_changed(self):
        fmt = self.format_combo.currentText()

        self.bg_check.setVisible(fmt in ("JPG", "BMP", "ICO"))

        show_quality = fmt in ("PNG", "JPG", "WEBP")
        self.quality_label.setVisible(show_quality)
        self.quality_spin.setVisible(show_quality)

        if show_quality:
            if fmt == "PNG":
                self.quality_label.setText("压缩级别:")
                self.quality_spin.setSuffix("（越小越清晰）")
                self.quality_spin.setValue(1)
            else:
                self.quality_label.setText("画质质量:")
                self.quality_spin.setSuffix(" %（越大越清晰）")
                self.quality_spin.setValue(100)
        else:
            self.quality_spin.setValue(0)

        self.changed.emit()


def build_panel() -> QWidget:
    return ConvertPanel()


def collect_settings(panel: ConvertPanel) -> dict:
    return {
        "target_format": panel.format_combo.currentText().lower(),
        "quality": panel.quality_spin.value(),
        "fill_white_bg": panel.bg_check.isChecked(),
    }


def prepare_preview(items, settings: dict):
    fmt = settings.get("target_format", "png").lower()
    quality = settings.get("quality", 90)
    fmt_display = fmt.upper()
    
    for it in items:
        base = os.path.splitext(it.output_name)[0]
        it.output_name = base + "." + fmt
        
        if fmt_display == "PNG":
            suffix = f"压缩级别:{quality}"
        elif fmt_display in ("JPG", "WEBP"):
            suffix = f"画质:{quality}%"
        else:
            suffix = "无损"
        it.preview_extra = {"A": f"→ {fmt_display}（{suffix}）"}


def run_task(file_item, settings: dict):
    if Image is None:
        raise RuntimeError("缺少 Pillow 库，请安装: pip install Pillow")

    src = file_item.input_path
    target_fmt = settings.get("target_format", "png")
    quality = settings.get("quality", 90)
    fill_white = settings.get("fill_white_bg", True)

    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(file_item.output_name)[0]
    final_name = f"{base_name}.{target_fmt}"
    file_item.output_name = final_name
    out_path = os.path.join(out_dir, final_name)

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