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


class VideoCutPanel(QWidget):
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
    return {
        "start_h": panel.start_h.value(),
        "start_m": panel.start_m.value(),
        "start_s": panel.start_s.value(),
        "end_h": panel.end_h.value(),
        "end_m": panel.end_m.value(),
        "end_s": panel.end_s.value(),
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

    subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')


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