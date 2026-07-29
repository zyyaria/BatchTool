# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
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


class ResizePanel(QWidget):
    changed = Signal()
    log_signal = Signal(str)

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF", "ICO"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        layout.addLayout(row_format)

        row_size = QHBoxLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(["原尺寸", "尺寸（像素）", "尺寸（%）", "短边约束", "长边约束"])
        self.size_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.aspect_check = QCheckBox("保持比例")
        self.aspect_check.setChecked(True)
        self.aspect_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_size.addWidget(QLabel("目标尺寸:"))
        row_size.addWidget(self.size_combo, 1)
        row_size.addWidget(self.aspect_check)
        layout.addLayout(row_size)

        self.csize_widget = QWidget()
        row_csize = QHBoxLayout(self.csize_widget)
        row_csize.setContentsMargins(0, 0, 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 99999)
        self.width_spin.setValue(1)
        self.width_spin.setSpecialValueText("")
        self.width_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 99999)
        self.height_spin.setValue(1)
        self.height_spin.setSpecialValueText("")
        self.height_spin.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_csize.addWidget(QLabel("宽度:"))
        row_csize.addWidget(self.width_spin, 1)
        row_csize.addWidget(QLabel("高度:"))
        row_csize.addWidget(self.height_spin, 1)
        layout.addWidget(self.csize_widget)

        row_dpi = QHBoxLayout()
        self.check_dpi = QCheckBox("修改分辨率")
        self.check_dpi.setChecked(False)
        self.check_dpi.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(1, 3000)
        self.dpi_spin.setValue(72)
        self.dpi_spin.setSuffix(" ppi")
        self.dpi_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dpi_spin.setEnabled(False)
        row_dpi.addWidget(QLabel("目标分辨率:"))
        row_dpi.addWidget(self.check_dpi)
        row_dpi.addWidget(self.dpi_spin, 1)
        layout.addLayout(row_dpi)

        layout.addStretch()

        self.format_combo.currentIndexChanged.connect(self.changed)
        self.size_combo.currentIndexChanged.connect(self._on_size_mode_changed)
        self.size_combo.currentIndexChanged.connect(self.changed)
        self.aspect_check.stateChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.check_dpi.stateChanged.connect(self._on_dpi_toggled)
        self.check_dpi.stateChanged.connect(self.changed)
        self.dpi_spin.valueChanged.connect(self.changed)

        self._on_size_mode_changed()

    def _on_size_mode_changed(self):
        """尺寸模式切换"""
        mode = self.size_combo.currentIndex()
        is_original = (mode == 0)
        self.csize_widget.setVisible(not is_original)
        if is_original:
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            self.width_spin.setSpecialValueText("忽略")
            self.height_spin.setSpecialValueText("忽略")
        else:
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
            self.width_spin.setSpecialValueText("")
            self.height_spin.setSpecialValueText("")
            if mode == 1:
                self.width_spin.setSuffix(" px")
                self.height_spin.setSuffix(" px")
                self.width_spin.setRange(1, 99999)
                self.height_spin.setRange(1, 99999)
                self.height_spin.setEnabled(True)
                self.height_spin.setSpecialValueText("")
            elif mode == 2:
                self.width_spin.setSuffix(" %")
                self.height_spin.setSuffix(" %")
                self.width_spin.setRange(1, 200)
                self.height_spin.setRange(1, 200)
                self.height_spin.setEnabled(True)
                self.height_spin.setSpecialValueText("")
            elif mode == 3:
                self.width_spin.setSuffix(" px")
                self.height_spin.setSuffix("")
                self.width_spin.setRange(1, 99999)
                self.height_spin.setRange(1, 99999)
                self.height_spin.setEnabled(False)
                self.height_spin.setSpecialValueText("自动计算")
                self.height_spin.setValue(0)
            elif mode == 4:
                self.width_spin.setSuffix(" px")
                self.height_spin.setSuffix("")
                self.width_spin.setRange(1, 99999)
                self.height_spin.setRange(1, 99999)
                self.height_spin.setEnabled(False)
                self.height_spin.setSpecialValueText("自动计算")
                self.height_spin.setValue(0)
        self.changed.emit()

    def _on_dpi_toggled(self):
        """分辨率复选框切换"""
        self.dpi_spin.setEnabled(self.check_dpi.isChecked())
        self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return ResizePanel()


def collect_settings(panel: ResizePanel) -> dict:
    """收集面板设置"""
    mode_names = ["original", "pixel", "percent", "short_edge", "long_edge"]
    size_mode = panel.size_combo.currentIndex()
    w_val = panel.width_spin.value()
    h_val = panel.height_spin.value()
    if size_mode in (3, 4):
        h_val = None
    format_text = panel.format_combo.currentText()
    target_format = format_text.lower() if format_text != "原格式" else None
    return {
        "mode": mode_names[size_mode],
        "width": w_val if w_val > 0 else None,
        "height": h_val if h_val is not None and h_val > 0 else None,
        "keep_aspect": panel.aspect_check.isChecked(),
        "target_format": target_format,
        "dpi": panel.dpi_spin.value(),
        "modify_dpi": panel.check_dpi.isChecked(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    mode = settings.get("mode", "original")
    w = settings.get("width")
    h = settings.get("height")
    keep = settings.get("keep_aspect", True)
    fmt = settings.get("target_format")
    modify_dpi = settings.get("modify_dpi", False)
    dpi = settings.get("dpi", 72)
    for it in items:
        if mode == "original":
            size_desc = "原尺寸（不调整）"
        elif mode == "pixel":
            size_desc = f"宽{w}px x 高{h}px" if (w and h) else "无效尺寸"
        elif mode == "percent":
            size_desc = f"宽{w}% x 高{h}%" if (w and h) else "无效百分比"
        elif mode == "short_edge":
            size_desc = f"短边{w}px，长边自动" if w else "无效"
        elif mode == "long_edge":
            size_desc = f"长边{w}px，短边自动" if w else "无效"
        else:
            size_desc = "未知模式"
        if keep and mode != "original":
            size_desc += "（保持比例）"
        elif mode != "original":
            size_desc += "（拉伸）"
        if modify_dpi:
            dpi_desc = f"DPI={dpi}"
        else:
            if not hasattr(it, "_orig_dpi_cache"):
                try:
                    with Image.open(it.input_path) as im:
                        dpi_orig = im.info.get("dpi", (None, None))
                        if isinstance(dpi_orig, tuple) and dpi_orig[0] is not None:
                            it._orig_dpi_cache = f"{dpi_orig[0]:.0f}" if dpi_orig[0] == dpi_orig[1] else f"{dpi_orig[0]:.0f}x{dpi_orig[1]:.0f}"
                        else:
                            it._orig_dpi_cache = "未知"
                except Exception:
                    it._orig_dpi_cache = "读取失败"
            dpi_desc = f"原DPI（{it._orig_dpi_cache}）"
        fmt_display = fmt.upper() if fmt else "原格式"
        it.preview_extra = {
            "A": f"尺寸：{size_desc}，{dpi_desc}，格式{fmt_display}"
        }


def run_task(file_item, settings):
    """执行单个图片尺寸调整任务"""
    if Image is None:
        raise RuntimeError("缺少 Pillow 库")
    src = file_item.input_path
    mode = settings.get("mode", "original")
    w_val = settings.get("width")
    h_val = settings.get("height")
    keep_aspect = settings.get("keep_aspect", True)
    target_fmt = settings.get("target_format")
    modify_dpi = settings.get("modify_dpi", False)
    dpi = settings.get("dpi", 72)
    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图像: {e}")
    orig_w, orig_h = im.size
    orig_dpi = im.info.get("dpi", (72, 72))
    if not isinstance(orig_dpi, tuple) or len(orig_dpi) < 2:
        orig_dpi = (72, 72)
    if mode == "original":
        im_resized = im.copy()
        new_w, new_h = orig_w, orig_h
    elif mode == "pixel":
        if w_val is None or h_val is None:
            raise RuntimeError("请输入有效的宽度和高度")
        new_w = int(w_val)
        new_h = int(h_val)
        if keep_aspect:
            ratio = orig_w / orig_h
            if new_w / new_h > ratio:
                new_w = int(new_h * ratio)
            else:
                new_h = int(new_w / ratio)
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    elif mode == "percent":
        if w_val is None or h_val is None:
            raise RuntimeError("请输入有效的百分比")
        pct_w = w_val / 100.0
        pct_h = h_val / 100.0
        if keep_aspect:
            new_w = int(orig_w * pct_w)
            new_h = int(new_w / (orig_w / orig_h))
        else:
            new_w = int(orig_w * pct_w)
            new_h = int(orig_h * pct_h)
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    elif mode == "short_edge":
        if w_val is None:
            raise RuntimeError("请输入短边长度")
        target_short = int(w_val)
        if orig_w <= orig_h:
            new_w = target_short
            new_h = int(target_short * orig_h / orig_w)
        else:
            new_h = target_short
            new_w = int(target_short * orig_w / orig_h)
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    elif mode == "long_edge":
        if w_val is None:
            raise RuntimeError("请输入长边长度")
        target_long = int(w_val)
        if orig_w >= orig_h:
            new_w = target_long
            new_h = int(target_long * orig_h / orig_w)
        else:
            new_h = target_long
            new_w = int(target_long * orig_w / orig_h)
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    else:
        im_resized = im.copy()
        new_w, new_h = orig_w, orig_h
    new_w = max(1, int(new_w))
    new_h = max(1, int(new_h))
    if mode != "original":
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if modify_dpi:
        final_dpi = (dpi, dpi)
    else:
        final_dpi = orig_dpi
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    ext = os.path.splitext(file_item.output_name)[1][1:].lower()
    if not ext:
        ext = "png"
    save_format = ext.upper()
    if save_format == "JPG":
        save_format = "JPEG"
    save_kwargs = {"dpi": final_dpi}
    if save_format == "JPEG":
        save_kwargs["quality"] = 95
        save_kwargs["optimize"] = True
    elif save_format == "WEBP":
        save_kwargs["quality"] = 90
        save_kwargs["lossless"] = False
    elif save_format == "PNG":
        save_kwargs["compress_level"] = 6
        save_kwargs["optimize"] = True
    im_resized = ensure_image_mode(im_resized, ext, fill_white=True)
    try:
        im_resized.save(out_path, format=save_format, **save_kwargs)
    except Exception as e:
        raise RuntimeError(f"保存失败: {e}")
    finally:
        im_resized.close()
        im.close()
    file_item.status = "完成"