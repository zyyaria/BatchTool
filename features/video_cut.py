# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
import subprocess
from PySide6.QtCore import Signal, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QCheckBox, QSizePolicy,
    QTimeEdit
)
from core.utils import get_ffmpeg_path, load_app_config, save_app_config


class VideoCutPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.ffmpeg_path = get_ffmpeg_path()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        time_row = QHBoxLayout()
        time_row.addWidget(QLabel("截取时间:"))

        self.start_time = QTimeEdit()
        self.start_time.setDisplayFormat("HH:mm:ss")
        self.start_time.setTime(QTime(0, 0, 0))
        self.start_time.setMinimumWidth(80)
        self.start_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        time_row.addWidget(self.start_time, 1)

        time_row.addWidget(QLabel(" 至 "))

        self.end_time = QTimeEdit()
        self.end_time.setDisplayFormat("HH:mm:ss")
        self.end_time.setTime(QTime(0, 0, 0))
        self.end_time.setMinimumWidth(80)
        self.end_time.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        time_row.addWidget(self.end_time, 1)

        layout.addLayout(time_row)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("输出格式:"))
        self.out_format = QComboBox()
        self.out_format.addItems(["原格式", "mp4", "mkv", "avi", "mov"])
        fmt_row.addWidget(self.out_format, 1)
        self.reencode_check = QCheckBox("重新编码")
        fmt_row.addWidget(self.reencode_check)
        layout.addLayout(fmt_row)

        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.addWidget(QLabel("FFmpeg 路径:"))
        self.ffmpeg_path_label = QLabel(self.ffmpeg_path if self.ffmpeg_path else "未找到")
        self.ffmpeg_path_label.setWordWrap(False)
        self.ffmpeg_path_label.setStyleSheet("color: #555;")
        if self.ffmpeg_path:
            self.ffmpeg_path_label.setToolTip(self.ffmpeg_path)
        self.ffmpeg_path_label.setMinimumWidth(200)
        ffmpeg_row.addWidget(self.ffmpeg_path_label, 1)
        layout.addLayout(ffmpeg_row)

        self.ffmpeg_btn = QPushButton("手动指定 FFmpeg 路径")
        self.ffmpeg_btn.clicked.connect(self.select_ffmpeg_path)
        layout.addWidget(self.ffmpeg_btn)

        layout.addStretch()

        self.start_time.timeChanged.connect(self.changed)
        self.end_time.timeChanged.connect(self.changed)
        self.out_format.currentIndexChanged.connect(self.changed)
        self.reencode_check.stateChanged.connect(self.changed)

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
    return VideoCutPanel()


def collect_settings(panel: VideoCutPanel) -> dict:
    start = panel.start_time.time()
    end = panel.end_time.time()
    return {
        "start_h": start.hour(),
        "start_m": start.minute(),
        "start_s": start.second(),
        "end_h": end.hour(),
        "end_m": end.minute(),
        "end_s": end.second(),
        "out_format": panel.out_format.currentText(),
        "reencode": panel.reencode_check.isChecked(),
    }


def prepare_preview(items, settings):
    sh = settings.get("start_h", 0)
    sm = settings.get("start_m", 0)
    ss = settings.get("start_s", 0)
    eh = settings.get("end_h", 0)
    em = settings.get("end_m", 0)
    es = settings.get("end_s", 0)
    fmt = settings.get("out_format", "原格式")

    start_str = f"{sh:02d}:{sm:02d}:{ss:02d}"
    end_str = f"{eh:02d}:{em:02d}:{es:02d}"

    for it in items:
        base = os.path.splitext(os.path.basename(it.input_path))[0]
        if fmt == "原格式":
            ext = os.path.splitext(it.input_path)[1]
        else:
            ext = "." + fmt.lower()
        it.output_name = base + "_截取" + ext
        it.preview_extra = {"A": f"截取 {start_str} → {end_str}"}


def _to_seconds(h, m, s):
    return h * 3600 + m * 60 + s


import subprocess
import sys  # 如果顶部没有导入，补上

def 截取视频(input_path, output_path, start_sec, duration_sec, reencode=False):
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
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )


def run_task(file_item, settings):
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

    out_format = settings.get("out_format", "原格式")
    reencode = settings.get("reencode", False)

    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)

    base_name = os.path.splitext(file_item.output_name)[0]
    if out_format == "原格式":
        ext = os.path.splitext(src)[1]
    else:
        ext = "." + out_format.lower()

    out_name = base_name + ext
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name

    截取视频(src, out_path, start_sec, duration_sec, reencode)
    file_item.status = "完成"