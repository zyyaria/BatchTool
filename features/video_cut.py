# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
from PySide6.QtCore import Signal, QTime, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QCheckBox, QSizePolicy, QTimeEdit
)
from core.utils import get_ffmpeg_path, save_app_config


class VideoCutPanel(QWidget):
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

        row_format = QHBoxLayout()   
        self.format_combo = QComboBox()
        self.format_combo.addItems(["原格式", "mp4", "mkv", "avi", "mov"])
        self.format_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reencode_check = QCheckBox("重新编码")
        self.reencode_check.setChecked(False)
        self.reencode_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)    
        row_format.addWidget(QLabel("目标格式:"))
        row_format.addWidget(self.format_combo, 1)
        row_format.addWidget(self.reencode_check) 
        layout.addLayout(row_format)

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
        self.format_combo.currentIndexChanged.connect(self.changed)
        self.reencode_check.stateChanged.connect(self.changed)
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
    return VideoCutPanel()


def collect_settings(panel: VideoCutPanel) -> dict:
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
        "format": panel.format_combo.currentText(),
        "reencode": panel.reencode_check.isChecked(),
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 0)
    fmt = settings.get("format", "原格式")
    reencode = settings.get("reencode", False)
    start_str = f"{sh:02d}:{sm:02d}:{ss:02d}"
    end_str = f"{eh:02d}:{em:02d}:{es:02d}"
    for it in items:
        base = os.path.splitext(os.path.basename(it.input_path))[0]
        it.preview_extra = {
            "A": f"截取 {start_str} → {end_str}，输出{fmt if fmt!='原格式' else '原格式'}，{'重新编码' if reencode else '直接复制'}"
        }


def _to_seconds(h, m, s):
    """将时分秒转换为总秒数"""
    return h * 3600 + m * 60 + s


def cut_video(input_path, output_path, start_sec, duration_sec, reencode=False):
    """使用 FFmpeg 截取视频片段"""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        raise RuntimeError("未找到 FFmpeg，请安装并添加到 PATH，或手动指定路径")
    cmd = [ffmpeg, "-ss", str(start_sec), "-i", input_path]
    if duration_sec > 0:
        cmd.extend(["-t", str(duration_sec)])
    if not reencode:
        cmd.extend(["-c", "copy"])
    else:
        cmd.extend(["-c:v", "libx264", "-preset", "fast", "-c:a", "aac", "-b:a", "128k"])
    cmd.extend(["-y", output_path])
    subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )


def run_task(file_item, settings):
    """执行单个视频截取任务"""
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 0)
    start_sec = _to_seconds(sh, sm, ss)
    end_sec = _to_seconds(eh, em, es)
    if end_sec <= start_sec:
        raise ValueError("结束时间必须大于开始时间")
    duration_sec = end_sec - start_sec
    format = settings.get("format", "原格式")
    reencode = settings.get("reencode", False)
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    cut_video(src, out_path, start_sec, duration_sec, reencode)
    file_item.status = "完成"