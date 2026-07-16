import os
import sys
import json
import time
import glob
import ctypes
import shutil
import platform
import subprocess
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QFormLayout, 
    QComboBox, QPushButton, QFileDialog, QMessageBox, QSpinBox, QSlider, 
    QCheckBox
)
from core.utils import load_app_config, save_app_config


def is_ghostscript_available():
    for cmd in ['gswin64c', 'gswin32c', 'gs']:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True, shell=True)
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


def _run_gs(input_path, output_path, dpi, quality, color_mode):
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
    if color_mode == "gray":
        cmd.insert(1, "-sColorConversionStrategy=Gray")
        cmd.insert(2, "-dProcessColorModel=/DeviceGray")
    elif color_mode == "mono":
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
        subprocess.run(cmd, check=True, capture_output=True, startupinfo=startupinfo,
                       creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
        return True
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ghostscript 压缩失败: {e.stderr.decode()}")


def compress_pdf(input_path, output_path, dpi, quality, color_mode):
    _run_gs(input_path, output_path, dpi, quality, color_mode)


class CompressPanel(QWidget):
    changed = Signal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("预设："))
        self.btn_light = QPushButton("轻微")
        self.btn_medium = QPushButton("中等")
        self.btn_strong = QPushButton("较强")
        self.btn_max = QPushButton("最大")
        self.btn_light.clicked.connect(lambda: self._set_preset(150, 85))
        self.btn_medium.clicked.connect(lambda: self._set_preset(150, 75))
        self.btn_strong.clicked.connect(lambda: self._set_preset(96, 50))
        self.btn_max.clicked.connect(lambda: self._set_preset(72, 30))
        preset_row.addWidget(self.btn_light)
        preset_row.addWidget(self.btn_medium)
        preset_row.addWidget(self.btn_strong)
        preset_row.addWidget(self.btn_max)
        preset_row.addStretch()
        main_layout.addLayout(preset_row)

        dpi_row = QHBoxLayout()
        dpi_row.addWidget(QLabel("DPI（图片分辨率）:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 300)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" ppi")
        dpi_row.addWidget(self.dpi_spin, 1)
        main_layout.addLayout(dpi_row)

        quality_row = QHBoxLayout()
        quality_row.addWidget(QLabel("JPEG 质量:"))
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(10, 100)
        self.quality_spin.setValue(75)
        self.quality_spin.setSuffix(" %")
        quality_row.addWidget(self.quality_spin, 1)
        main_layout.addLayout(quality_row)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("色彩模式:"))
        self.color_combo = QComboBox()
        self.color_combo.addItems(["彩色", "灰度", "黑白"])
        color_row.addWidget(self.color_combo, 1)
        main_layout.addLayout(color_row)

        gs_row = QHBoxLayout()
        self.gs_path_label = QLabel("GS 路径:")
        self.gs_path_value = QLabel(GS_PATH if GS_PATH else "未找到")
        self.gs_path_value.setWordWrap(False)
        self.gs_path_value.setStyleSheet("color: #555;")
        if GS_PATH:
            self.gs_path_value.setToolTip(GS_PATH)
        self.gs_path_value.setMinimumWidth(200)
        gs_row.addWidget(self.gs_path_label)
        gs_row.addWidget(self.gs_path_value, 1)
        main_layout.addLayout(gs_row)

        self.gs_select_btn = QPushButton("手动指定 Ghostscript 路径")
        self.gs_select_btn.clicked.connect(self.select_gs_path)
        main_layout.addWidget(self.gs_select_btn)

        main_layout.addStretch()

        self.dpi_spin.valueChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.color_combo.currentIndexChanged.connect(self.changed)

    def _set_preset(self, dpi, quality):
        self.dpi_spin.setValue(dpi)
        self.quality_spin.setValue(quality)
        self.changed.emit()

    def select_gs_path(self):
        if platform.system() == "Windows":
            file_filter = "Ghostscript 可执行文件 (gswin64c.exe gswin32c.exe);;所有文件 (*.*)"
        else:
            file_filter = "Ghostscript 可执行文件 (gs);;所有文件 (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择 Ghostscript 可执行文件", "", file_filter)
        if path:
            try:
                subprocess.run([path, "--version"], capture_output=True, check=True)
                save_app_config("gs_path", path)
                global GS_PATH
                globals()['GS_PATH'] = path
                self.gs_path_value.setText(path)
                self.gs_path_value.setToolTip(path)
                QMessageBox.information(self, "成功", "Ghostscript 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 Ghostscript 可执行文件：{e}")


def build_panel() -> QWidget:
    return CompressPanel()


def collect_settings(panel: CompressPanel) -> dict:
    color_map = {"彩色": "color", "灰度": "gray", "黑白": "mono"}
    return {
        "mode": "custom",
        "dpi": panel.dpi_spin.value(),
        "quality": panel.quality_spin.value(),
        "color": color_map[panel.color_combo.currentText()]
    }


def prepare_preview(items, settings):
    hint = f"DPI={settings['dpi']}, 质量={settings['quality']}%, 色彩={settings['color']}"
    for it in items:
        it.preview_extra = {"A": hint}


def run_task(file_item, settings: dict):
    global GS_PATH
    if GS_PATH is None or not os.path.exists(GS_PATH):
        GS_PATH = find_ghostscript()
        if GS_PATH is None:
            raise RuntimeError("未找到 Ghostscript，请先安装或在压缩面板中设置路径。")
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.splitext(file_item.output_name)[0] if file_item.output_name else os.path.splitext(os.path.basename(src))[0]
    out_name = base_name + ".pdf"
    out_path = os.path.join(out_dir, out_name)
    file_item.output_name = out_name
    original_size = os.path.getsize(src)
    compress_pdf(src, out_path, settings["dpi"], settings["quality"], settings["color"])
    compressed_size = os.path.getsize(out_path)
    reduction = (1 - compressed_size / original_size) * 100
    file_item.status = "完成"