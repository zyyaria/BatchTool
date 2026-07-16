# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import subprocess
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QCheckBox, QSizePolicy
)
from core.utils import get_ffmpeg_path, load_app_config, save_app_config


class VideoToGifPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 10, 0, 10)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("开始时间:"))
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(2)
        self.start_h = QSpinBox()
        self.start_h.setRange(0, 99)
        self.start_h.setValue(0)
        self.start_h.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_h.setMinimumWidth(40)
        row2.addWidget(self.start_h, 1)
        row2.addWidget(QLabel(":"))
        self.start_m = QSpinBox()
        self.start_m.setRange(0, 59)
        self.start_m.setValue(0)
        self.start_m.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_m.setMinimumWidth(40)
        row2.addWidget(self.start_m, 1)
        row2.addWidget(QLabel(":"))
        self.start_s = QSpinBox()
        self.start_s.setRange(0, 59)
        self.start_s.setValue(0)
        self.start_s.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_s.setMinimumWidth(40)
        row2.addWidget(self.start_s, 1)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("结束时间:"))
        row3.addStretch()
        layout.addLayout(row3)

        row4 = QHBoxLayout()
        row4.setSpacing(2)
        self.end_h = QSpinBox()
        self.end_h.setRange(0, 99)
        self.end_h.setValue(0)
        self.end_h.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.end_h.setMinimumWidth(40)
        row4.addWidget(self.end_h, 1)
        row4.addWidget(QLabel(":"))
        self.end_m = QSpinBox()
        self.end_m.setRange(0, 59)
        self.end_m.setValue(0)
        self.end_m.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.end_m.setMinimumWidth(40)
        row4.addWidget(self.end_m, 1)
        row4.addWidget(QLabel(":"))
        self.end_s = QSpinBox()
        self.end_s.setRange(0, 59)
        self.end_s.setValue(0)
        self.end_s.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.end_s.setMinimumWidth(40)
        row4.addWidget(self.end_s, 1)
        layout.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("帧率:"))
        self.fps = QSpinBox()
        self.fps.setRange(1, 60)
        self.fps.setValue(10)
        self.fps.setSuffix(" fps（越高越流畅）")
        self.fps.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.fps.setMinimumWidth(40)
        row5.addWidget(self.fps, 1)
        layout.addLayout(row5)

        row6 = QHBoxLayout()
        row6.addWidget(QLabel("尺寸:"))
        self.width = QSpinBox()
        self.width.setRange(16, 1920)
        self.width.setValue(320)
        self.width.setSuffix(" px")
        self.width.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.width.setMinimumWidth(50)
        row6.addWidget(self.width, 1)
        row6.addWidget(QLabel(" × "))
        self.height = QSpinBox()
        self.height.setRange(16, 1080)
        self.height.setValue(240)
        self.height.setSuffix(" px")
        self.height.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.height.setMinimumWidth(50)
        row6.addWidget(self.height, 1)
        layout.addLayout(row6)

        row7 = QHBoxLayout()
        row7.addWidget(QLabel("颜色数:"))
        self.colors = QSpinBox()
        self.colors.setRange(16, 256)
        self.colors.setValue(128)
        self.colors.setSuffix(" 色（越多越丰富）")
        self.colors.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.colors.setMinimumWidth(50)
        row7.addWidget(self.colors, 1)
        self.keep_aspect = QCheckBox("保持比例")
        self.keep_aspect.setChecked(True)
        row7.addWidget(self.keep_aspect)
        layout.addLayout(row7)

        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.addWidget(QLabel("FFmpeg 路径:"))
        self.ffmpeg_path_label = QLabel(self.ffmpeg_path if self.ffmpeg_path else "未找到")
        self.ffmpeg_path_label.setWordWrap(False)
        self.ffmpeg_path_label.setStyleSheet("color: #555;")
        if self.ffmpeg_path:
            self.ffmpeg_path_label.setToolTip(self.ffmpeg_path)
        ffmpeg_row.addWidget(self.ffmpeg_path_label, 1)
        layout.addLayout(ffmpeg_row)

        self.ffmpeg_btn = QPushButton("手动指定 FFmpeg 路径")
        self.ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)
        layout.addWidget(self.ffmpeg_btn)

        layout.addStretch()

        self.start_h.valueChanged.connect(self.changed)
        self.start_m.valueChanged.connect(self.changed)
        self.start_s.valueChanged.connect(self.changed)
        self.end_h.valueChanged.connect(self.changed)
        self.end_m.valueChanged.connect(self.changed)
        self.end_s.valueChanged.connect(self.changed)
        self.fps.valueChanged.connect(self.changed)
        self.width.valueChanged.connect(self.changed)
        self.height.valueChanged.connect(self.changed)
        self.colors.valueChanged.connect(self.changed)
        self.keep_aspect.stateChanged.connect(self.changed)

    def select_ffmpeg_path(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 FFmpeg 可执行文件", "",
            "FFmpeg 可执行文件 (ffmpeg.exe);;所有文件 (*.*)"
        )
        if path:
            try:
                subprocess.run([path, "-version"], capture_output=True, check=True, encoding='utf-8')
                save_app_config("ffmpeg_path", path)
                self.ffmpeg_path = path
                self.ffmpeg_path_label.setText(path)
                self.ffmpeg_path_label.setToolTip(path)
                QMessageBox.information(self, "成功", "FFmpeg 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 FFmpeg 可执行文件：{e}")


def build_panel() -> QWidget:
    return VideoToGifPanel()


def collect_settings(panel: VideoToGifPanel) -> dict:
    return {
        "start_h": panel.start_h.value(),
        "start_m": panel.start_m.value(),
        "start_s": panel.start_s.value(),
        "end_h": panel.end_h.value(),
        "end_m": panel.end_m.value(),
        "end_s": panel.end_s.value(),
        "fps": panel.fps.value(),
        "width": panel.width.value(),
        "height": panel.height.value(),
        "colors": panel.colors.value(),
        "keep_aspect": panel.keep_aspect.isChecked(),
    }


def prepare_preview(items, settings):
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 5)
    fps = settings.get("fps", 10)
    width = settings.get("width", 320)
    height = settings.get("height", 240)
    colors = settings.get("colors", 128)
    keep = settings.get("keep_aspect", True)

    start_str = f"{sh:02d}:{sm:02d}:{ss:02d}"
    end_str = f"{eh:02d}:{em:02d}:{es:02d}"

    for it in items:
        base = os.path.splitext(os.path.basename(it.input_path))[0]
        it.output_name = base + ".gif"
        it.preview_extra = {"A": f"转GIF {start_str}→{end_str} {fps}fps {width}x{height} {'保持比例' if keep else ''} 颜色{colors}"}


def _to_seconds(h, m, s):
    return h * 3600 + m * 60 + s


def video_to_gif(input_path, output_path, start_sec, duration_sec, fps, width, height, colors, keep_aspect):
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg，请安装并添加到 PATH，或手动指定路径")

    if duration_sec <= 0:
        raise ValueError("持续时间必须大于0")

    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    out_dir = os.path.dirname(output_path)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    scale_filter = f"scale={width}:{height}"
    if keep_aspect:
        scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"

    palette_filter = f"fps={fps},{scale_filter},palettegen=max_colors={colors}"
    gif_filter = f"fps={fps},{scale_filter},paletteuse"

    temp_palette = output_path + ".palette.png"

    cmd_palette = [
        ffmpeg, "-ss", str(start_sec), "-t", str(duration_sec),
        "-i", input_path,
        "-vf", palette_filter,
        "-y", temp_palette
    ]
    try:
        subprocess.run(cmd_palette, check=True, capture_output=True, text=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"生成调色板失败: {e.stderr}")

    cmd_gif = [
        ffmpeg, "-ss", str(start_sec), "-t", str(duration_sec),
        "-i", input_path,
        "-i", temp_palette,
        "-lavfi", gif_filter,
        "-y", output_path
    ]
    try:
        subprocess.run(cmd_gif, check=True, capture_output=True, text=True, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        if os.path.exists(temp_palette):
            os.remove(temp_palette)
        raise RuntimeError(f"生成 GIF 失败: {e.stderr}")

    if os.path.exists(temp_palette):
        os.remove(temp_palette)


def run_task(file_item, settings):
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 5)

    fps = settings.get("fps", 10)
    width = settings.get("width", 320)
    height = settings.get("height", 240)
    colors = settings.get("colors", 128)
    keep_aspect = settings.get("keep_aspect", True)

    start_sec = _to_seconds(sh, sm, ss)
    end_sec = _to_seconds(eh, em, es)

    if end_sec <= start_sec:
        raise ValueError("结束时间必须大于开始时间")

    duration_sec = end_sec - start_sec

    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(file_item.output_name)[0]
    out_name = base_name + ".gif"
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name

    video_to_gif(src, out_path, start_sec, duration_sec, fps, width, height, colors, keep_aspect)
    file_item.status = "完成"