# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QCheckBox, QPushButton
)
from core.utils import ensure_image_mode


try:
    from PIL import Image, ImageSequence
except ImportError:
    Image = None
    ImageSequence = None


class CompressPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        group = QWidget()
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(0, 0, 0, 0)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预设:"))
        self.btn_light = QPushButton("轻度")
        self.btn_medium = QPushButton("中等")
        self.btn_strong = QPushButton("强力")
        self.btn_extreme = QPushButton("极限")
        self.btn_light.clicked.connect(lambda: self._apply_preset(85, 100, False, 256, 1, True))
        self.btn_medium.clicked.connect(lambda: self._apply_preset(75, 90, False, 128, 1, True))
        self.btn_strong.clicked.connect(lambda: self._apply_preset(60, 80, False, 64, 2, True))
        self.btn_extreme.clicked.connect(lambda: self._apply_preset(40, 60, False, 32, 3, True))
        preset_row.addWidget(self.btn_light, 1)
        preset_row.addWidget(self.btn_medium, 1)
        preset_row.addWidget(self.btn_strong, 1)
        preset_row.addWidget(self.btn_extreme, 1)
        group_layout.addLayout(preset_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("输出格式:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "JPG", "PNG", "WEBP", "GIF"])
        format_row.addWidget(self.format_combo, 1)
        group_layout.addLayout(format_row)

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(75)
        self.quality_spin.setSuffix(" %")
        quality_row.addWidget(self.quality_spin, 1)
        self.gray_check = QCheckBox("转为灰度")
        quality_row.addWidget(self.gray_check)
        group_layout.addLayout(quality_row)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("缩放:"))
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(50, 100)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix(" %")
        scale_row.addWidget(self.scale_spin, 1)
        group_layout.addLayout(scale_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("最大颜色数:"))
        self.color_spin = QSpinBox()
        self.color_spin.setRange(2, 256)
        self.color_spin.setValue(256)
        color_row.addWidget(self.color_spin, 1)
        group_layout.addLayout(color_row)

        frame_row = QHBoxLayout()
        frame_row.addWidget(QLabel("抽帧间隔:"))
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 10)
        self.frame_spin.setValue(1)
        frame_row.addWidget(self.frame_spin, 1)
        self.keep_anim_check = QCheckBox("保留动画")
        self.keep_anim_check.setChecked(True)
        frame_row.addWidget(self.keep_anim_check)
        group_layout.addLayout(frame_row)

        layout.addWidget(group)
        layout.addStretch()

        self.quality_spin.valueChanged.connect(self.changed)
        self.scale_spin.valueChanged.connect(self.changed)
        self.gray_check.stateChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.color_spin.valueChanged.connect(self.changed)
        self.frame_spin.valueChanged.connect(self.changed)
        self.keep_anim_check.stateChanged.connect(self.changed)

    def _apply_preset(self, quality, scale, gray, colors, frame_interval, keep_anim):
        self.quality_spin.setValue(quality)
        self.scale_spin.setValue(scale)
        self.gray_check.setChecked(gray)
        self.color_spin.setValue(colors)
        self.frame_spin.setValue(frame_interval)
        self.keep_anim_check.setChecked(keep_anim)
        self.changed.emit()


def build_panel() -> QWidget:
    return CompressPanel()


def collect_settings(panel: CompressPanel) -> dict:
    fmt = panel.format_combo.currentText().lower()
    if fmt == "原格式":
        fmt = None
    return {
        "quality": panel.quality_spin.value(),
        "scale": panel.scale_spin.value() / 100.0,
        "grayscale": panel.gray_check.isChecked(),
        "target_format": fmt,
        "max_colors": panel.color_spin.value(),
        "frame_interval": panel.frame_spin.value(),
        "keep_animation": panel.keep_anim_check.isChecked(),
    }


def prepare_preview(items, settings: dict):
    quality = settings.get("quality", 75)
    scale = settings.get("scale", 1.0)
    gray = settings.get("grayscale", False)
    fmt = settings.get("target_format")
    fmt_display = fmt.upper() if fmt else "原格式"
    colors = settings.get("max_colors", 256)
    interval = settings.get("frame_interval", 1)
    keep = settings.get("keep_animation", True)
    desc = f"质量:{quality}%, 缩放:{int(scale*100)}%"
    if gray:
        desc += ", 灰度"
    if fmt_display != "原格式":
        desc += f", 格式:{fmt_display}"
    if colors < 256:
        desc += f", 颜色数:{colors}"
    if interval > 1:
        desc += f", 抽帧:{interval}"
    if not keep:
        desc += ", 仅首帧"
    
    for it in items:
        if fmt:
            base = os.path.splitext(it.output_name)[0]
            it.output_name = base + "." + fmt
        it.preview_extra = {"A": desc}


def run_task(file_item, settings: dict):
    if Image is None:
        raise RuntimeError("缺少 Pillow 库，请安装: pip install Pillow")

    src = file_item.input_path
    quality = settings.get("quality", 75)
    scale = settings.get("scale", 1.0)
    grayscale = settings.get("grayscale", False)
    target_fmt = settings.get("target_format")
    max_colors = settings.get("max_colors", 256)
    frame_interval = settings.get("frame_interval", 1)
    keep_animation = settings.get("keep_animation", True)

    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    if target_fmt:
        ext = target_fmt
    else:
        ext = os.path.splitext(src)[1][1:].lower()
        if not ext:
            ext = "png"

    base_name = os.path.splitext(file_item.output_name)[0]
    final_name = f"{base_name}.{ext}"
    file_item.output_name = final_name
    out_path = os.path.join(out_dir, final_name)

    try:
        im = Image.open(src)
    except Exception as e:
        raise RuntimeError(f"无法打开图片: {e}")

    is_animated_gif = (im.format == "GIF" and getattr(im, "is_animated", False))

    if (target_fmt and target_fmt != "gif") or (not keep_animation):
        try:
            im.seek(0)
        except EOFError:
            pass
        im = _process_single_frame(im, scale, grayscale, target_fmt, quality, max_colors)
        im = ensure_image_mode(im, ext, fill_white=True)
        save_format = _get_save_format(ext)
        save_kwargs = _get_save_kwargs(save_format, quality)
        im.save(out_path, format=save_format, **save_kwargs)
        im.close()
        file_item.status = "完成"
        return

    if is_animated_gif and keep_animation and (target_fmt is None or target_fmt == "gif"):
        out_ext = "gif"
        final_name = f"{base_name}.gif"
        file_item.output_name = final_name
        out_path = os.path.join(out_dir, final_name)

        frames = []
        durations = []
        try:
            for i, frame in enumerate(ImageSequence.Iterator(im)):
                if i % frame_interval != 0:
                    continue
                frame = frame.copy()
                if scale != 1.0:
                    new_w = int(frame.width * scale)
                    new_h = int(frame.height * scale)
                    frame = frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
                if grayscale:
                    frame = frame.convert("L")
                if max_colors < 256:
                    if frame.mode == "RGBA":
                        frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)
                    else:
                        frame = frame.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
                if frame.mode not in ("P", "L"):
                    frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)
                frames.append(frame)
                try:
                    duration = im.info.get("duration", 100)
                except:
                    duration = 100
                durations.append(duration)
        except EOFError:
            pass
        finally:
            im.close()

        if not frames:
            raise RuntimeError("未提取到任何帧")

        save_kwargs = {
            "save_all": True,
            "append_images": frames[1:],
            "duration": durations,
            "loop": 0,
            "optimize": True,
        }
        frames[0].save(out_path, format="GIF", **save_kwargs)
        file_item.status = "完成"
        return

    im = _process_single_frame(im, scale, grayscale, target_fmt, quality, max_colors)
    save_format = _get_save_format(ext)
    save_kwargs = _get_save_kwargs(save_format, quality)
    im.save(out_path, format=save_format, **save_kwargs)
    im.close()
    file_item.status = "完成"


def _process_single_frame(im, scale, grayscale, target_fmt, quality, max_colors):
    if scale != 1.0:
        new_w = int(im.width * scale)
        new_h = int(im.height * scale)
        im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

    if grayscale:
        im = im.convert("L")

    if target_fmt in (None, "gif") and im.format == "GIF":
        if max_colors < 256:
            if im.mode == "RGBA":
                im = im.convert("P", palette=Image.Palette.ADAPTIVE, colors=max_colors)
            else:
                im = im.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)

    if target_fmt == "jpg":
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
    elif target_fmt == "png":
        if im.mode == "RGBA" and not im.getchannel("A").getextrema()[1]:
            im = im.convert("RGB")
    return im


def _get_save_format(ext):
    fmt = ext.upper()
    if fmt == "JPG":
        return "JPEG"
    return fmt


def _get_save_kwargs(save_format, quality):
    kwargs = {}
    if save_format == "JPEG":
        kwargs["quality"] = quality
        kwargs["optimize"] = True
    elif save_format == "WEBP":
        kwargs["quality"] = quality
        kwargs["lossless"] = False
    elif save_format == "PNG":
        compress_level = int((100 - quality) / 100 * 9)
        kwargs["compress_level"] = compress_level
        kwargs["optimize"] = True
    return kwargs