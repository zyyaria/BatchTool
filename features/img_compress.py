# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox,
    QCheckBox, QPushButton, QSizePolicy
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
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_preset = QHBoxLayout()
        self.light_btn = QPushButton("轻度")
        self.light_btn.clicked.connect(lambda: self._apply_preset(85, 100, False, 256, 1, True))
        self.light_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.medium_btn = QPushButton("中等")
        self.medium_btn.clicked.connect(lambda: self._apply_preset(75, 90, False, 128, 1, True))
        self.medium_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.strong_btn = QPushButton("强力")
        self.strong_btn.clicked.connect(lambda: self._apply_preset(60, 80, False, 64, 2, True))
        self.strong_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.extreme_btn = QPushButton("极限")
        self.extreme_btn.clicked.connect(lambda: self._apply_preset(40, 60, False, 32, 3, True))
        self.extreme_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_preset.addWidget(QLabel("预设:"))
        row_preset.addWidget(self.light_btn, 1)
        row_preset.addWidget(self.medium_btn, 1)
        row_preset.addWidget(self.strong_btn, 1)
        row_preset.addWidget(self.extreme_btn, 1)
        layout.addLayout(row_preset)

        row_format = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "JPG", "PNG", "WEBP", "GIF"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gray_check = QCheckBox("转为灰度")
        self.gray_check.setChecked(False)   
        self.gray_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed) 
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        row_format.addWidget(self.gray_check)
        layout.addLayout(row_format)

        row_quality = QHBoxLayout()
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setValue(75)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.scale_spin = QSpinBox()
        self.scale_spin.setRange(50, 100)
        self.scale_spin.setValue(100)
        self.scale_spin.setSuffix(" %")
        self.scale_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_quality.addWidget(QLabel("质量:"))
        row_quality.addWidget(self.quality_spin, 1)
        row_quality.addWidget(QLabel("缩放:"))
        row_quality.addWidget(self.scale_spin, 1)
        layout.addLayout(row_quality)

        row_color = QHBoxLayout()
        self.color_spin = QSpinBox()
        self.color_spin.setRange(2, 256)
        self.color_spin.setValue(256)
        self.color_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_color.addWidget(QLabel("最大颜色数:"))
        row_color.addWidget(self.color_spin, 1)
        layout.addLayout(row_color)

        row_frame = QHBoxLayout()
        self.frame_spin = QSpinBox()
        self.frame_spin.setRange(1, 10)
        self.frame_spin.setValue(1)
        self.frame_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.animation_check = QCheckBox("保留动画")
        self.animation_check.setChecked(True)      
        self.animation_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  
        row_frame.addWidget(QLabel("抽帧间隔:"))
        row_frame.addWidget(self.frame_spin, 1)
        row_frame.addWidget(self.animation_check)        
        layout.addLayout(row_frame)

        layout.addStretch()

        self.quality_spin.valueChanged.connect(self.changed)
        self.scale_spin.valueChanged.connect(self.changed)
        self.gray_check.stateChanged.connect(self.changed)
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.color_spin.valueChanged.connect(self.changed)
        self.frame_spin.valueChanged.connect(self.changed)
        self.animation_check.stateChanged.connect(self.changed)

    def _apply_preset(self, quality, scale, gray, colors, frame_interval, keep_anim):
        """应用预设参数"""
        self.quality_spin.setValue(quality)
        self.scale_spin.setValue(scale)
        self.gray_check.setChecked(gray)
        self.color_spin.setValue(colors)
        self.frame_spin.setValue(frame_interval)
        self.animation_check.setChecked(keep_anim)
        self.changed.emit()


def build_panel() -> QWidget:
    """构建面板实例"""
    return CompressPanel()


def collect_settings(panel: CompressPanel) -> dict:
    """收集面板设置"""
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
        "keep_animation": panel.animation_check.isChecked(),
    }


def prepare_preview(items, settings: dict):
    """生成预览信息"""
    fmt = settings.get("target_format")
    for it in items:
        quality = settings.get("quality", 75)
        scale = settings.get("scale", 1.0)
        gray = settings.get("grayscale", False)
        colors = settings.get("max_colors", 256)
        interval = settings.get("frame_interval", 1)
        keep = settings.get("keep_animation", True)
        parts = [f"质量{quality}%", f"缩放{int(scale*100)}%"]
        if gray:
            parts.append("灰度")
        if fmt:
            parts.append(f"格式{fmt.upper()}")
        if colors < 256:
            parts.append(f"颜色数{colors}")
        if interval > 1:
            parts.append(f"抽帧间隔{interval}")
        if not keep:
            parts.append("仅首帧")
        it.preview_extra = {"A": "，".join(parts)}


def run_task(file_item, settings: dict):
    """执行单个图片压缩任务"""
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
    out_path = os.path.join(out_dir, file_item.output_name)
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
        im = ensure_image_mode(im, target_fmt or "png", fill_white=True)
        save_format = _get_save_format(target_fmt or "png")
        save_kwargs = _get_save_kwargs(save_format, quality)
        im.save(out_path, format=save_format, **save_kwargs)
        im.close()
        file_item.status = "完成"
        return
    if is_animated_gif and keep_animation and (target_fmt is None or target_fmt == "gif"):
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
        for f in frames:
            f.close()
        file_item.status = "完成"
        return
    im = _process_single_frame(im, scale, grayscale, target_fmt, quality, max_colors)
    save_format = _get_save_format(target_fmt or "png")
    save_kwargs = _get_save_kwargs(save_format, quality)
    im.save(out_path, format=save_format, **save_kwargs)
    im.close()
    file_item.status = "完成"


def _process_single_frame(im, scale, grayscale, target_fmt, quality, max_colors):
    """处理单帧图像"""
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
    """将扩展名转换为 PIL 保存格式名称"""
    fmt = ext.upper()
    if fmt == "JPG":
        return "JPEG"
    return fmt


def _get_save_kwargs(save_format, quality):
    """根据保存格式生成 PIL 保存参数"""
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