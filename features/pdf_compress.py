# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import glob
import shutil
import platform
import subprocess
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QSpinBox, QSizePolicy
)
from core.utils import load_app_config, save_app_config


class CompressPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_preset = QHBoxLayout()
        self.light_btn = QPushButton("轻微")
        self.light_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.medium_btn = QPushButton("中等")
        self.medium_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.strong_btn = QPushButton("强力")
        self.strong_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.extreme_btn = QPushButton("极限")
        self.extreme_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_preset.addWidget(QLabel("预设:"))
        row_preset.addWidget(self.light_btn, 1)
        row_preset.addWidget(self.medium_btn, 1)
        row_preset.addWidget(self.strong_btn, 1)
        row_preset.addWidget(self.extreme_btn, 1)
        layout.addLayout(row_preset)

        row_dpi = QHBoxLayout()
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 300)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" ppi")
        self.dpi_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_dpi.addWidget(QLabel("目标分辨率:"))
        row_dpi.addWidget(self.dpi_spin, 1)
        layout.addLayout(row_dpi) 

        row_quality = QHBoxLayout()
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(10, 100)
        self.quality_spin.setValue(75)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  
        row_quality.addWidget(QLabel("JPEG 质量:"))
        row_quality.addWidget(self.quality_spin, 1)        
        layout.addLayout(row_quality)  

        row_color = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["彩色", "灰度", "黑白"])
        self.color_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)         
        row_color.addWidget(QLabel("颜色模式:"))
        row_color.addWidget(self.color_combo, 1)
        layout.addLayout(row_color)

        row_gs = QHBoxLayout()
        self.gs_label = QLabel(GS_PATH if GS_PATH else "未找到")
        self.gs_label.setWordWrap(False)
        self.gs_label.setStyleSheet("color: #555;")
        self.gs_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        if GS_PATH:
            self.gs_label.setToolTip(GS_PATH)
        row_gs.addWidget(QLabel("Ghostscript 路径:"))
        row_gs.addWidget(self.gs_label, 1)
        layout.addLayout(row_gs)

        self.gs_btn = QPushButton("手动指定 Ghostscript 路径")
        self.gs_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)    
        layout.addWidget(self.gs_btn, 1)

        layout.addStretch()

        self.light_btn.clicked.connect(lambda: self._set_preset(150, 85))
        self.medium_btn.clicked.connect(lambda: self._set_preset(150, 75))
        self.strong_btn.clicked.connect(lambda: self._set_preset(96, 50))
        self.extreme_btn.clicked.connect(lambda: self._set_preset(72, 30))
        self.dpi_spin.valueChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.color_combo.currentIndexChanged.connect(self.changed)
        self.gs_btn.clicked.connect(self.select_gs_path)

    def _set_preset(self, dpi, quality):
        """应用预设参数"""
        self.dpi_spin.blockSignals(True)
        self.quality_spin.blockSignals(True)
        self.dpi_spin.setValue(dpi)
        self.quality_spin.setValue(quality)
        self.dpi_spin.blockSignals(False)
        self.quality_spin.blockSignals(False)
        self.changed.emit()

    def select_gs_path(self):
        """选择 Ghostscript 路径"""
        if platform.system() == "Windows":
            file_filter = "Ghostscript 可执行文件 (gswin64c.exe gswin32c.exe);;所有文件 (*.*)"
        else:
            file_filter = "Ghostscript 可执行文件 (gs);;所有文件 (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择 Ghostscript 可执行文件", "", file_filter)
        if path:
            try:
                subprocess.run([path, "--version"], capture_output=True, text=True,
                               encoding='utf-8', errors='ignore', check=True)
                save_app_config("gs_path", path)
                global GS_PATH
                globals()['GS_PATH'] = path
                self.gs_label.setText(path)
                self.gs_label.setToolTip(path)
                QMessageBox.information(self, "成功", "Ghostscript 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 Ghostscript 可执行文件：{e}")


def build_panel() -> QWidget:
    """构建面板实例"""
    return CompressPanel()


def collect_settings(panel: CompressPanel) -> dict:
    """收集面板设置"""
    color_map = {"彩色": "color", "灰度": "gray", "黑白": "mono"}
    return {
        "mode": "custom",
        "dpi": panel.dpi_spin.value(),
        "quality": panel.quality_spin.value(),
        "color": color_map[panel.color_combo.currentText()]
    }


def prepare_preview(items, settings):
    """生成预览信息"""
    dpi = settings.get("dpi", 150)
    quality = settings.get("quality", 75)
    color = settings.get("color", "color")
    color_map = {"color": "彩色", "gray": "灰度", "mono": "黑白"}
    color_text = color_map.get(color, color)
    hint = f"DPI={dpi}，JPEG质量={quality}%，颜色={color_text}"
    for it in items:
        it.preview_extra = {"A": hint}


def run_task(file_item, settings: dict):
    """执行单个 PDF 压缩任务"""
    global GS_PATH
    if GS_PATH is None or not os.path.exists(GS_PATH):
        GS_PATH = find_ghostscript()
        if GS_PATH is None:
            raise RuntimeError("未找到 Ghostscript，请先安装或在压缩面板中设置路径。")
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    original_size = os.path.getsize(src)
    compress_pdf(src, out_path, settings["dpi"], settings["quality"], settings["color"])
    compressed_size = os.path.getsize(out_path)
    reduction = (1 - compressed_size / original_size) * 100
    file_item.status = "完成"


def is_ghostscript_available():
    """检测系统是否安装 Ghostscript"""
    for cmd in ['gswin64c', 'gswin32c', 'gs']:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True,
                                    encoding='utf-8', errors='ignore', shell=True)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass
    common_paths = [
        r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
        r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
        r"D:\Program Files\Ghostscript\bin\gswin64c.exe"
    ]
    for pattern in common_paths:
        matches = glob.glob(pattern)
        if matches:
            return True
    return False


def ensure_ghostscript(parent_widget=None):
    """确保 Ghostscript 可用，否则提示用户安装，返回路径或 None"""
    gs_path = find_ghostscript()
    if gs_path:
        return gs_path
    QMessageBox.information(
        parent_widget, "缺少 Ghostscript",
        "PDF 压缩需要 Ghostscript。\n\n"
        "请从以下地址下载安装：\n"
        "https://www.ghostscript.com/releases/gsdnld.html\n\n"
        "安装后重启本工具即可。"
    )
    return None


def find_ghostscript():
    """自动查找 Ghostscript 可执行文件路径"""
    saved_path = load_app_config("gs_path")
    if saved_path and os.path.exists(saved_path):
        return saved_path
    if platform.system() == "Windows":
        gs_names = ["gswin64c.exe", "gswin32c.exe", "gs.exe"]
    else:
        gs_names = ["gs"]
    for name in gs_names:
        gs_path = shutil.which(name)
        if gs_path:
            return gs_path
    common_paths = [
        r"C:\Program Files\gs\gs*\bin\gswin64c.exe",
        r"C:\Program Files (x86)\gs\gs*\bin\gswin32c.exe",
        r"D:\Program Files\Ghostscript\bin\gswin64c.exe"
    ]
    for pattern in common_paths:
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches, reverse=True)[0]
    return None


GS_PATH = find_ghostscript()


def _run_gs(input_path, output_path, dpi, quality, color_combo):
    """执行 Ghostscript 压缩命令"""
    if GS_PATH is None:
        raise RuntimeError("未找到 Ghostscript，请先安装或手动设置 Ghostscript 路径。")
    cmd = [
        GS_PATH,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        "-dPDFSETTINGS=/printer",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        "-dDetectDuplicateImages=true",
        f"-dColorImageResolution={dpi}",
        f"-dGrayImageResolution={dpi}",
        f"-dMonoImageResolution={dpi*2}",
        "-dColorImageDownsampleThreshold=1.0",
        "-dGrayImageDownsampleThreshold=1.0",
        "-dMonoImageDownsampleThreshold=1.0",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dMonoImageDownsampleType=/Subsample",
        "-dColorImageFilter=/DCTEncode",
        "-dGrayImageFilter=/DCTEncode",
        f"-dJPEGQ={quality}",
        f"-sOutputFile={output_path}",
        input_path
    ]
    if color_combo == "gray":
        cmd.insert(1, "-sColorConversionStrategy=Gray")
        cmd.insert(2, "-dProcessColorModel=/DeviceGray")
    elif color_combo == "mono":
        cmd.insert(1, "-sColorConversionStrategy=Gray")
        cmd.insert(2, "-dProcessColorModel=/DeviceGray")
        cmd.insert(3, "-dGrayImageResolution=150")
        cmd.insert(4, "-dMonoImageResolution=300")
    try:
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0
        subprocess.run(cmd, check=True, capture_output=True,
                       text=True, encoding='utf-8', errors='ignore',
                       startupinfo=startupinfo,
                       creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ghostscript 压缩失败: {e.stderr}")


def compress_pdf(input_path, output_path, dpi, quality, color_combo):
    """压缩 PDF 文件"""
    _run_gs(input_path, output_path, dpi, quality, color_combo)