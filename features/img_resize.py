# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
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


class ResizePanel(QWidget):
    changed = Signal()
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        action_row = QHBoxLayout()
        action_row.addWidget(QLabel("操作模式:"))
        self.action_mode = QComboBox()
        self.action_mode.addItems([
            "仅调整尺寸",
            "仅修改DPI",
            "调整尺寸+DPI"
        ])
        self.action_mode.currentIndexChanged.connect(self._on_action_mode_changed)
        action_row.addWidget(self.action_mode, 1)
        layout.addLayout(action_row)

        self.size_widget = QWidget()
        size_layout = QVBoxLayout(self.size_widget)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)

        size_row1 = QHBoxLayout()
        size_row1.addWidget(QLabel("目标尺寸:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["像素", "百分比", "短边约束", "长边约束"])
        self.mode_combo.currentIndexChanged.connect(self._on_size_mode_changed)
        size_row1.addWidget(self.mode_combo, 1)
        self.aspect_check = QCheckBox("保持比例")
        self.aspect_check.setChecked(True)
        size_row1.addWidget(self.aspect_check)
        size_layout.addLayout(size_row1)

        size_row2 = QHBoxLayout()
        size_row2.addWidget(QLabel("宽度:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 99999)
        self.width_spin.setValue(1)
        self.width_spin.setSpecialValueText("")
        self.width_spin.setMaximumWidth(112)
        size_row2.addWidget(self.width_spin, 1)

        size_row2.addWidget(QLabel("高度:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 99999)
        self.height_spin.setValue(1)
        self.height_spin.setSpecialValueText("")
        self.height_spin.setMaximumWidth(112)
        size_row2.addWidget(self.height_spin, 1)

        size_layout.addLayout(size_row2)

        layout.addWidget(self.size_widget)

        self.dpi_widget = QWidget()
        dpi_row = QHBoxLayout(self.dpi_widget)
        dpi_row.setContentsMargins(0, 0, 0, 0)
        dpi_row.addWidget(QLabel("目标 DPI:"))
        self.target_dpi_spin = QSpinBox()
        self.target_dpi_spin.setRange(1, 3000)
        self.target_dpi_spin.setValue(72)
        dpi_row.addWidget(self.target_dpi_spin, 1)
        layout.addWidget(self.dpi_widget)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF", "ICO"])
        fmt_row.addWidget(self.format_combo, 1)
        layout.addLayout(fmt_row)

        layout.addStretch()

        self.action_mode.currentIndexChanged.connect(self.changed)
        self.mode_combo.currentIndexChanged.connect(self._on_size_mode_changed)
        self.mode_combo.currentIndexChanged.connect(self.changed)
        self.aspect_check.stateChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.target_dpi_spin.valueChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)

        self._on_action_mode_changed()
        self._on_size_mode_changed()

    def _on_action_mode_changed(self):
        mode = self.action_mode.currentIndex()
        if mode == 1:
            self.size_widget.setVisible(False)
            self.dpi_widget.setVisible(True)
            self.width_spin.setEnabled(False)
            self.height_spin.setEnabled(False)
            self.width_spin.setSpecialValueText("忽略")
            self.height_spin.setSpecialValueText("忽略")
        elif mode == 0:
            self.size_widget.setVisible(True)
            self.dpi_widget.setVisible(False)
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
            self.width_spin.setSpecialValueText("")
            self.height_spin.setSpecialValueText("")
            self._on_size_mode_changed()
        else:
            self.size_widget.setVisible(True)
            self.dpi_widget.setVisible(True)
            self.width_spin.setEnabled(True)
            self.height_spin.setEnabled(True)
            self.width_spin.setSpecialValueText("")
            self.height_spin.setSpecialValueText("")
            self._on_size_mode_changed()

        self.changed.emit()

    def _on_size_mode_changed(self):
        mode = self.mode_combo.currentIndex()
        if mode == 0:
            self.width_spin.setSuffix(" px")
            self.height_spin.setSuffix(" px")
            self.width_spin.setRange(1, 99999)
            self.height_spin.setRange(1, 99999)
            self.height_spin.setEnabled(True)
            self.height_spin.setSpecialValueText("")
        elif mode == 1:
            self.width_spin.setSuffix(" %")
            self.height_spin.setSuffix(" %")
            self.width_spin.setRange(1, 200)
            self.height_spin.setRange(1, 200)
            self.height_spin.setEnabled(True)
            self.height_spin.setSpecialValueText("")
        elif mode == 2:
            self.width_spin.setSuffix(" px")
            self.height_spin.setSuffix("")
            self.width_spin.setRange(1, 99999)
            self.height_spin.setRange(1, 99999)
            self.height_spin.setEnabled(False)
            self.height_spin.setSpecialValueText("自动计算")
            self.height_spin.setValue(0)
        elif mode == 3:
            self.width_spin.setSuffix(" px")
            self.height_spin.setSuffix("")
            self.width_spin.setRange(1, 99999)
            self.height_spin.setRange(1, 99999)
            self.height_spin.setEnabled(False)
            self.height_spin.setSpecialValueText("自动计算")
            self.height_spin.setValue(0)
        self.changed.emit()


def build_panel() -> QWidget:
    return ResizePanel()


def collect_settings(panel: ResizePanel) -> dict:
    mode = panel.mode_combo.currentIndex()
    mode_names = ["pixel", "percent", "short_edge", "long_edge"]
    w_val = panel.width_spin.value()
    h_val = panel.height_spin.value()

    if mode in (2, 3):
        h_val = None

    format_text = panel.format_combo.currentText()
    target_format = format_text.lower() if format_text != "原格式" else None

    action = panel.action_mode.currentIndex()

    return {
        "mode": mode_names[mode],
        "width": w_val if w_val > 0 else None,
        "height": h_val if h_val is not None and h_val > 0 else None,
        "keep_aspect": panel.aspect_check.isChecked(),
        "target_format": target_format,
        "target_dpi": panel.target_dpi_spin.value(),
        "action": action,
    }


def prepare_preview(items, settings):
    mode = settings.get("mode", "pixel")
    w = settings.get("width")
    h = settings.get("height")
    keep = settings.get("keep_aspect", True)
    fmt = settings.get("target_format")
    fmt_display = fmt.upper() if fmt else "原格式"
    target_dpi = settings.get("target_dpi", 72)
    action = settings.get("action", 0)

    if action == 0:
        desc = "仅调整尺寸"
    elif action == 1:
        desc = "仅修改DPI"
    else:
        desc = "调整尺寸+DPI"

    if action != 1:
        desc += f", 模式: {mode}"
        if mode == "pixel":
            if w is not None and h is not None:
                desc += f", 宽={w}, 高={h}"
            else:
                desc += ", 请填写宽高"
        elif mode == "percent":
            if w is not None and h is not None:
                desc += f", 宽={w}%, 高={h}%"
            else:
                desc += ", 请填写百分比"
        elif mode == "short_edge":
            desc += f", 短边={w}" if w is not None else ", 请填写短边"
            desc += ", 长边=自动计算"
        elif mode == "long_edge":
            desc += f", 长边={w}" if w is not None else ", 请填写长边"
            desc += ", 短边=自动计算"
        desc += ", 保持比例" if keep else ", 拉伸"

    if action != 0:
        desc += f", DPI: {target_dpi}"
    desc += f", 格式: {fmt_display}"

    for it in items:
        if fmt:
            base = os.path.splitext(it.output_name)[0]
            it.output_name = base + "." + fmt

        if not hasattr(it, "_orig_dpi_cache"):
            try:
                with Image.open(it.input_path) as im:
                    dpi = im.info.get("dpi", (None, None))
                    if isinstance(dpi, tuple) and len(dpi) >= 2 and dpi[0] is not None:
                        if dpi[0] == dpi[1]:
                            it._orig_dpi_cache = f"{dpi[0]:.0f}"
                        else:
                            it._orig_dpi_cache = f"{dpi[0]:.0f}x{dpi[1]:.0f}"
                    else:
                        it._orig_dpi_cache = "未知"
            except Exception:
                it._orig_dpi_cache = "读取失败"
        it.preview_extra = {"A": f"{desc}（原DPI: {it._orig_dpi_cache}）"}


def run_task(file_item, settings):
    if Image is None:
        raise RuntimeError("缺少 Pillow 库")

    src = file_item.input_path
    mode = settings.get("mode", "pixel")
    w_val = settings.get("width")
    h_val = settings.get("height")
    keep_aspect = settings.get("keep_aspect", True)
    target_fmt = settings.get("target_format")
    target_dpi = settings.get("target_dpi", 72)
    action = settings.get("action", 0)

    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图像: {e}")

    orig_w, orig_h = im.size
    orig_dpi = im.info.get("dpi", (72, 72))
    if not isinstance(orig_dpi, tuple) or len(orig_dpi) < 2:
        orig_dpi = (72, 72)

    if action == 1:
        im_resized = im.copy()
        new_w, new_h = orig_w, orig_h
    else:
        new_w, new_h = None, None
        if mode == "pixel":
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

        new_w = max(1, int(new_w))
        new_h = max(1, int(new_h))
        im_resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if action == 0:
        final_dpi = orig_dpi
    else:
        final_dpi = (target_dpi, target_dpi)

    if target_fmt:
        ext = target_fmt
    else:
        ext = os.path.splitext(src)[1][1:].lower()
        if not ext:
            ext = "png"

    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(file_item.output_name)[0]
    final_name = f"{base_name}.{ext}"
    file_item.output_name = final_name
    out_path = os.path.join(out_dir, final_name)

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