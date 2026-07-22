# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
from PySide6.QtCore import Signal, QTime, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QSizePolicy, QTimeEdit
)
from core.utils import get_ffmpeg_path, save_app_config


class VideoToGifPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_time = QHBoxLayout()
        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm:ss")
        self.start_time.setTime(QTime(0, 0, 0))
        self.start_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        to_label = QLabel("至")
        to_label.setAlignment(Qt.AlignCenter)
        to_label.setFixedWidth(12)
        to_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)        
        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm:ss")
        self.end_time.setTime(QTime(0, 0, 0))
        self.end_time.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        row_time.addWidget(QLabel("截取时间:"))
        row_time.addWidget(self.start_time, 1)
        row_time.addWidget(to_label)
        row_time.addWidget(self.end_time, 1)
        layout.addLayout(row_time)

        row_fps = QHBoxLayout()
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(10)
        self.fps_spin.setSuffix(" fps")
        self.fps_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_fps.addWidget(QLabel("帧率:"))
        row_fps.addWidget(self.fps_spin, 1)
        layout.addLayout(row_fps)

        row_size = QHBoxLayout()        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(16, 1920)
        self.width_spin.setValue(320)
        self.width_spin.setSuffix(" px")
        self.width_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        x_label = QLabel(" × ")
        x_label.setFixedWidth(12)
        x_label.setAlignment(Qt.AlignCenter)     
        x_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(16, 1080)
        self.height_spin.setValue(240)
        self.height_spin.setSuffix(" px")
        self.height_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_size.addWidget(QLabel("目标尺寸:"))
        row_size.addWidget(self.width_spin, 1)
        row_size.addWidget(x_label)
        row_size.addWidget(self.height_spin, 1)
        layout.addLayout(row_size)

        row_color = QHBoxLayout()
        self.color_spin = QSpinBox()
        self.color_spin.setRange(16, 256)
        self.color_spin.setValue(128)
        self.color_spin.setSuffix(" 色")
        self.color_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.aspect_ratio_check = QCheckBox("保持比例")
        self.aspect_ratio_check.setChecked(True)
        self.aspect_ratio_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_color.addWidget(QLabel("颜色数:"))
        row_color.addWidget(self.color_spin, 1)
        row_color.addWidget(self.aspect_ratio_check)
        layout.addLayout(row_color)

        row_ffmpeg = QHBoxLayout()    
        self.ffmpeg_label = QLabel(self.ffmpeg_path if self.ffmpeg_path else "未找到")
        self.ffmpeg_label.setStyleSheet("color: #555;")
        self.ffmpeg_label.setWordWrap(False)
        self.ffmpeg_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        if self.ffmpeg_path:
            self.ffmpeg_label.setToolTip(self.ffmpeg_path)
        row_ffmpeg.addWidget(QLabel("FFmpeg 路径:"))
        row_ffmpeg.addWidget(self.ffmpeg_label, 1)
        layout.addLayout(row_ffmpeg)

        self.ffmpeg_btn = QPushButton("手动指定 FFmpeg 路径")
        self.ffmpeg_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
        layout.addWidget(self.ffmpeg_btn, 1)

        layout.addStretch()

        self.start_time.timeChanged.connect(self.changed)
        self.end_time.timeChanged.connect(self.changed)
        self.fps_spin.valueChanged.connect(self.changed)
        self.width_spin.valueChanged.connect(self.changed)
        self.height_spin.valueChanged.connect(self.changed)
        self.color_spin.valueChanged.connect(self.changed)
        self.aspect_ratio_check.stateChanged.connect(self.changed)
        self.ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)

    def select_ffmpeg_path(self):
        """选择 FFmpeg 路径"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 FFmpeg 可执行文件", "",
            "FFmpeg 可执行文件 (ffmpeg.exe);;所有文件 (*.*)"
        )
        if path:
            try:
                subprocess.run([path, "-version"], capture_output=True, text=True,
                               encoding='utf-8', errors='ignore', check=True)
                save_app_config("ffmpeg_path", path)
                self.ffmpeg_path = path
                self.ffmpeg_label.setText(path)
                self.ffmpeg_label.setToolTip(path)
                QMessageBox.information(self, "成功", "FFmpeg 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 FFmpeg 可执行文件：{e}")


def build_panel() -> QWidget:
    """构建面板实例"""
    return VideoToGifPanel()


def collect_settings(panel: VideoToGifPanel) -> dict:
    """收集面板设置"""
    start = panel.start_time.time()
    end = panel.end_time.time()
    return {
        "start_h": start.hour(),
        "start_m": start.minute(),
        "start_s": start.second(),
        "end_h": end.hour(),
        "end_m": end.minute(),
        "end_s": end.second(),
        "fps": panel.fps_spin.value(),
        "width": panel.width_spin.value(),
        "height": panel.height_spin.value(),
        "colors": panel.color_spin.value(),
        "aspect_ratio": panel.aspect_ratio_check.isChecked(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
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
    aspect_ratio = settings.get("aspect_ratio", True)
    start_str = f"{sh:02d}:{sm:02d}:{ss:02d}"
    end_str = f"{eh:02d}:{em:02d}:{es:02d}"
    for it in items:
        it.preview_extra = {
            "A": f"转GIF {start_str}→{end_str}，{fps}fps，{width}x{height}，{'保持比例' if aspect_ratio else '拉伸'}，颜色{colors}"
        }


def _to_seconds(h, m, s):
    """将时分秒转换为总秒数"""
    return h * 3600 + m * 60 + s


def video_to_gif(input_path, output_path, start_sec, duration_sec, fps, width, height, colors, aspect_ratio):
    """使用 FFmpeg 将视频片段转换为 GIF"""
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
    if aspect_ratio:
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
    subprocess.run(
        cmd_palette,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    cmd_gif = [
        ffmpeg, "-ss", str(start_sec), "-t", str(duration_sec),
        "-i", input_path,
        "-i", temp_palette,
        "-lavfi", gif_filter,
        "-y", output_path
    ]
    subprocess.run(
        cmd_gif,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )
    if os.path.exists(temp_palette):
        os.remove(temp_palette)


def run_task(file_item, settings):
    """执行单个视频转 GIF 任务"""
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
    aspect_ratio = settings.get("aspect_ratio", True)
    start_sec = _to_seconds(sh, sm, ss)
    end_sec = _to_seconds(eh, em, es)
    if end_sec <= start_sec:
        raise ValueError("结束时间必须大于开始时间")
    duration_sec = end_sec - start_sec
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    video_to_gif(src, out_path, start_sec, duration_sec, fps, width, height, colors, aspect_ratio)
    file_item.status = "完成"