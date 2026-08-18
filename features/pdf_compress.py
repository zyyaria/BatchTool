# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import glob
import platform
import subprocess
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QFileDialog, QMessageBox, QSpinBox, QDoubleSpinBox, 
    QSizePolicy, QLineEdit, QButtonGroup, QCheckBox
)
from core.utils import save_app_config, resource_path, get_ghostscript_path


class CompressPanel(QWidget):
    changed = Signal()

    def __init__(self):
        """初始化设置面板"""
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        row_mode = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.btn_fixed = QPushButton("常规压缩")
        self.btn_fixed.setCheckable(True)
        self.btn_fixed.setChecked(True)
        self.btn_fixed.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_target = QPushButton("指定大小")
        self.btn_target.setCheckable(True)
        self.btn_target.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.mode_group.addButton(self.btn_fixed)
        self.mode_group.addButton(self.btn_target)
        row_mode.addWidget(QLabel("模式:"))
        row_mode.addWidget(self.btn_fixed, 1)
        row_mode.addWidget(self.btn_target, 1)
        layout.addLayout(row_mode)

        self.fixed_widget = QWidget()
        fixed_layout = QVBoxLayout(self.fixed_widget)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setSpacing(8)

        row_preset = QHBoxLayout()
        self.light_btn = QPushButton("轻度")
        self.light_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.medium_btn = QPushButton("中等")
        self.medium_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.strong_btn = QPushButton("强力")
        self.strong_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.extreme_btn = QPushButton("极强")
        self.extreme_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_preset.addWidget(QLabel("预设:"))
        row_preset.addWidget(self.light_btn, 1)
        row_preset.addWidget(self.medium_btn, 1)
        row_preset.addWidget(self.strong_btn, 1)
        row_preset.addWidget(self.extreme_btn, 1)
        fixed_layout.addLayout(row_preset)

        row_dpi = QHBoxLayout()
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(36, 600)
        self.dpi_spin.setValue(150)
        self.dpi_spin.setSuffix(" ppi")
        self.dpi_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_dpi.addWidget(QLabel("目标分辨率:"))
        row_dpi.addWidget(self.dpi_spin, 1)
        fixed_layout.addLayout(row_dpi)

        row_quality = QHBoxLayout()
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(10, 100)
        self.quality_spin.setValue(75)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_quality.addWidget(QLabel("JPEG 质量:"))
        row_quality.addWidget(self.quality_spin, 1)
        fixed_layout.addLayout(row_quality)

        layout.addWidget(self.fixed_widget)

        self.target_widget = QWidget()
        target_layout = QVBoxLayout(self.target_widget)
        target_layout.setContentsMargins(0, 0, 0, 0)
        target_layout.setSpacing(8)

        row_target = QHBoxLayout()
        self.target_spin = QDoubleSpinBox()
        self.target_spin.setRange(0.1, 9999.9)
        self.target_spin.setValue(2.0)
        self.target_spin.setSingleStep(0.1)
        self.target_spin.setDecimals(1)
        self.target_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.target_unit = QComboBox()
        self.target_unit.addItems(["MB", "KB"])
        self.target_unit.setCurrentIndex(0)
        self.target_unit.setFixedWidth(70)
        self.target_unit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        row_target.addWidget(QLabel("目标大小:"))
        row_target.addWidget(self.target_spin, 1)
        row_target.addWidget(self.target_unit)
        target_layout.addLayout(row_target)

        row_tolerance = QHBoxLayout()
        self.tolerance_spin = QSpinBox()
        self.tolerance_spin.setRange(1, 20)
        self.tolerance_spin.setValue(5)
        self.tolerance_spin.setSuffix(" %")
        self.tolerance_spin.setToolTip("达到目标 ±5% 内即停止")
        self.tolerance_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_tolerance.addWidget(QLabel("精度范围:"))
        row_tolerance.addWidget(self.tolerance_spin, 1)
        target_layout.addLayout(row_tolerance)

        layout.addWidget(self.target_widget)

        row_shared = QHBoxLayout()
        self.gs_edit = QLineEdit()
        self.gs_edit.setText(GS_PATH if GS_PATH else "")
        self.gs_edit.setReadOnly(True)
        self.gs_edit.setPlaceholderText("未找到 GS，点击右侧图标选择")
        self.gs_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gs_action = QAction(self)
        self.gs_action.setIcon(QIcon(resource_path("assets/folder.png")))
        self.gs_action.setToolTip("选择 Ghostscript 可执行文件")
        self.gs_action.triggered.connect(self.select_gs_path)
        self.gs_edit.addAction(self.gs_action, QLineEdit.TrailingPosition)
        self.grayscale_check = QCheckBox("转为灰度")
        self.grayscale_check.setChecked(False)
        self.grayscale_check.setToolTip("将整份 PDF 转换为灰度图像，可减小文件体积")
        self.grayscale_check.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)        
        row_shared.addWidget(QLabel("GS 路径:"))
        row_shared.addWidget(self.gs_edit, 1)
        row_shared.addWidget(self.grayscale_check)
        layout.addLayout(row_shared)

        self.detect_size_btn = QPushButton("检测文件大小")
        self.detect_size_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.detect_size_btn.clicked.connect(self._detect_file_sizes)
        layout.addWidget(self.detect_size_btn)

        layout.addStretch()

        self.btn_fixed.toggled.connect(self._on_mode_changed)
        self.btn_target.toggled.connect(self._on_mode_changed)
        self.light_btn.clicked.connect(lambda: self._load_preset("light"))
        self.medium_btn.clicked.connect(lambda: self._load_preset("medium"))
        self.strong_btn.clicked.connect(lambda: self._load_preset("strong"))
        self.extreme_btn.clicked.connect(lambda: self._load_preset("extreme"))
        self.dpi_spin.valueChanged.connect(self.changed)
        self.quality_spin.valueChanged.connect(self.changed)
        self.target_spin.valueChanged.connect(self.changed)
        self.tolerance_spin.valueChanged.connect(self.changed)
        self.grayscale_check.stateChanged.connect(self.changed)

        self._load_preset("medium")
        self._on_mode_changed()

    def _on_mode_changed(self):
        """操作模式切换"""
        is_fixed = self.btn_fixed.isChecked()
        self.fixed_widget.setVisible(is_fixed)
        self.target_widget.setVisible(not is_fixed)
        self.changed.emit()

    def _load_preset(self, preset_name):
        """应用预设参数"""
        presets = {
            "light": {"dpi": 150, "quality": 85},
            "medium": {"dpi": 150, "quality": 75},
            "strong": {"dpi": 96, "quality": 50},
            "extreme": {"dpi": 72, "quality": 30},
        }
        p = presets.get(preset_name)
        if not p:
            return
        self.dpi_spin.setValue(p["dpi"])
        self.quality_spin.setValue(p["quality"])
        self.changed.emit()

    def select_gs_path(self):
        """选择 Ghostscript 可执行文件路径"""
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
                self.gs_edit.setText(path)
                self.gs_edit.setToolTip(path)
                self.gs_action.setToolTip(f"Ghostscript 路径: {path}")
                QMessageBox.information(self, "成功", "Ghostscript 路径已设置并保存。")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"所选文件不是有效的 Ghostscript 可执行文件：{e}")

    def _detect_file_sizes(self):
        """检测文件大小并输出到日志"""
        parent = self.parent()
        while parent and not hasattr(parent, 'preview_mgr'):
            parent = parent.parent()
        if not parent:
            QMessageBox.warning(self, "提示", "无法获取文件列表")
            return
        items = parent.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加文件")
            return
        parent.append_log("")
        parent.append_log("========== 文件大小检测 ==========")
        total = 0
        for idx, item in enumerate(items, 1):
            size = os.path.getsize(item.input_path)
            total += size
            parent.append_log(f"{idx}. {os.path.basename(item.input_path)}: {self._format_size(size)}")
        parent.append_log("")
        parent.append_log(f"总计: {self._format_size(total)}")
        parent.append_log("========== 检测完成 ==========")

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"


def build_panel() -> QWidget:
    """构建面板实例"""
    return CompressPanel()


def collect_settings(panel: CompressPanel) -> dict:
    """收集面板设置"""
    mode = "fixed" if panel.btn_fixed.isChecked() else "target"
    result = {"mode": mode, "grayscale": panel.grayscale_check.isChecked()}
    if mode == "fixed":
        result["dpi"] = panel.dpi_spin.value()
        result["quality"] = panel.quality_spin.value()
    else:
        value = panel.target_spin.value()
        unit = panel.target_unit.currentText()
        if unit == "MB":
            result["target_bytes"] = int(value * 1024 * 1024)
        else:
            result["target_bytes"] = int(value * 1024)
        result["tolerance"] = panel.tolerance_spin.value()
    return result


def prepare_preview(items, settings):
    """生成预览信息"""
    mode = settings.get("mode", "fixed")
    grayscale = settings.get("grayscale", False)
    if mode == "fixed":
        dpi = settings.get("dpi", 150)
        quality = settings.get("quality", 75)
        hint = f"DPI={dpi}，质量={quality}%"
    else:
        target_bytes = settings.get("target_bytes", 2 * 1024 * 1024)
        if target_bytes >= 1024 * 1024:
            target_mb = target_bytes / (1024 * 1024)
            target_display = f"{target_mb:.1f}MB"
        else:
            target_kb = target_bytes / 1024
            target_display = f"{target_kb:.0f}KB"
        tol = settings.get("tolerance", 5)
        hint = f"目标{target_display}（±{tol}%）"
    if grayscale:
        hint += "，灰度"
    for it in items:
        it.preview_extra = {"A": hint}


def run_task(file_item, settings: dict):
    """执行单个 PDF 压缩任务"""
    global GS_PATH
    if GS_PATH is None or not os.path.exists(GS_PATH):
        GS_PATH = get_ghostscript_path()
        if GS_PATH is None:
            raise RuntimeError("未找到 Ghostscript，请先安装或在压缩面板中设置路径。")
    src = file_item.input_path
    out_dir = file_item.output_dir or os.path.dirname(src)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, file_item.output_name)
    grayscale = settings.get("grayscale", False)
    mode = settings.get("mode", "fixed")
    if mode == "fixed":
        dpi = settings.get("dpi", 150)
        quality = settings.get("quality", 75)
        _run_gs(src, out_path, dpi, dpi, dpi, quality, grayscale)
    else:
        target_bytes = settings.get("target_bytes", 2 * 1024 * 1024)
        tolerance = settings.get("tolerance", 5) / 100.0
        _compress_to_target(src, out_path, target_bytes, tolerance, grayscale)
    file_item.status = "完成"


def _compress_to_target(input_path, output_path, target_bytes, tolerance, grayscale):
    """循环压缩到目标大小，在不超过目标的前提下尽量保持清晰度"""
    from PySide6.QtWidgets import QApplication
    original_size = os.path.getsize(input_path)
    if original_size <= target_bytes:
        import shutil
        shutil.copy2(input_path, output_path)
        return
    dpi = 150
    quality = 85
    min_dpi = 72
    min_quality = 50
    temp_path = output_path + ".temp.pdf"
    best_path = None
    best_size = original_size
    best_dpi = dpi
    best_quality = quality
    try:
        for attempt in range(10):
            QApplication.processEvents()
            _run_gs(input_path, temp_path, dpi, dpi, dpi, quality, grayscale)
            size = os.path.getsize(temp_path)
            if size <= target_bytes:
                best_path = temp_path
                best_size = size
                best_dpi = dpi
                best_quality = quality
                if size >= target_bytes * 0.85:
                    os.replace(temp_path, output_path)
                    return
                if dpi < 150 and quality < 85:
                    if dpi + 10 <= 150 and quality + 5 <= 85:
                        dpi = min(150, dpi + 10)
                        quality = min(85, quality + 5)
                        continue
                break
            if size > target_bytes:
                if quality > min_quality + 10:
                    quality = max(min_quality, quality - 12)
                else:
                    dpi = max(min_dpi, dpi - 12)
        if best_path and os.path.exists(best_path):
            os.replace(best_path, output_path)
            return
        _run_gs(input_path, temp_path, min_dpi, min_dpi, min_dpi, min_quality, grayscale)
        size = os.path.getsize(temp_path)
        if size <= target_bytes:
            os.replace(temp_path, output_path)
            return
        import shutil
        shutil.copy2(input_path, output_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass


def _run_gs(input_path, output_path, color_dpi, gray_dpi, mono_dpi, quality, grayscale):
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
        f"-dColorImageResolution={color_dpi}",
        f"-dGrayImageResolution={gray_dpi}",
        f"-dMonoImageResolution={mono_dpi}",
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
    if grayscale:
        cmd.insert(1, "-sColorConversionStrategy=Gray")
        cmd.insert(2, "-dProcessColorModel=/DeviceGray")
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
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Ghostscript 压缩失败: {e.stderr}")


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
    gs_path = get_ghostscript_path()
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


GS_PATH = get_ghostscript_path()