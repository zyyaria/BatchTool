# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import re
import sys
import time
import fitz
import subprocess
from typing import List, Callable
from dataclasses import dataclass, field
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QIcon, QFont, QColor, QShortcut, QKeySequence, QAction
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QLabel, QProgressBar, QTextEdit, QComboBox,
    QLineEdit, QHeaderView, QMessageBox, QGroupBox, QInputDialog, QAbstractItemView,
    QSplitter, QScrollArea, QDialog, QCheckBox, QTextBrowser, QDialogButtonBox,
    QSpinBox, QListWidget, QMenu, QFrame, QStackedWidget, QButtonGroup,
    QGridLayout, QRadioButton, QStyle
)
from .utils import resource_path, sanitize_base_name, parse_page_range, NamingRules
from .help import GENERAL_HELP_TEXT, get_about_text


@dataclass
class FileItem:
    input_path: str
    output_name: str = ""
    output_dir: str = ""
    status: str = "待处理"
    preview_extra: dict = field(default_factory=dict)
    locked_name: bool = False
    custom_outlines: str = ""
    checked: bool = True
    output_paths: list = field(default_factory=list)

    def full_output_path(self):
        if not self.output_dir:
            self.output_dir = os.path.dirname(self.input_path)
        return os.path.join(self.output_dir, self.output_name)


class OutputPath:
    def __init__(self, mode="source", custom_dir=""):
        self.mode = mode
        self.custom_dir = custom_dir

    def get_dir(self, file_path: str) -> str:
        if self.mode == "custom" and self.custom_dir:
            return self.custom_dir
        return os.path.dirname(file_path)


class FileListModel:
    def __init__(self):
        self.items: List[FileItem] = []

    def add_files(self, paths: List[str]):
        for p in paths:
            item = FileItem(input_path=p)
            item.output_name = os.path.basename(p)
            self.items.append(item)

    def remove_selected(self, indices: List[int]):
        self.items = [item for i, item in enumerate(self.items) if i not in indices]

    def clear(self):
        self.items.clear()

    def update_output_name(self, index: int, new_name: str):
        if 0 <= index < len(self.items):
            self.items[index].output_name = new_name

    def update_preview(self, diff_data: List[dict]):
        for i, data in enumerate(diff_data):
            if i < len(self.items):
                self.items[i].preview_extra = data


class WorkerSignals(QObject):
    log = Signal(str)
    log_batch = Signal(list)
    progress = Signal(int, int)
    finished = Signal()


class Worker(QObject):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self, items: List[FileItem], task_func: Callable[[FileItem], None]):
        total = len(items)
        log_buffer = []

        for i, item in enumerate(items):
            if self._stop_requested:
                self.signals.log.emit("⛔ 用户终止任务")
                break

            try:
                msg = f"正在处理：{item.input_path}"
                log_buffer.append(msg)
                if len(log_buffer) >= 10:
                    self.signals.log_batch.emit(log_buffer)
                    log_buffer = []

                item.status = "处理中"
                task_func(item)
                item.status = "完成"
                log_buffer.append(f"✅ {item.input_path} 处理完成")
            except Exception as e:
                item.status = "错误"
                log_buffer.append(f"❌ {item.input_path} 错误：{e}")

            if len(log_buffer) >= 10:
                self.signals.log_batch.emit(log_buffer)
                log_buffer = []

            self.signals.progress.emit(i + 1, total)

        if log_buffer:
            self.signals.log_batch.emit(log_buffer)

        if not self._stop_requested:
            self.signals.log.emit("✅ 全部处理完成！")
        else:
            self.signals.log.emit("⛔ 任务已终止")
        self.signals.finished.emit()


class BatchWorker(QObject):
    finished = Signal(list)
    log_signal = Signal(str)
    progress_signal = Signal(int, int)

    def __init__(self, items, settings, get_output_dir, get_output_name_for_group, module):
        super().__init__()
        self.items = items
        self.settings = settings
        self.get_output_dir = get_output_dir
        self.get_output_name_for_group = get_output_name_for_group
        self.module = module

    def run(self):
        try:
            output_files = self.module.run_batch(
                self.items,
                self.settings,
                self.get_output_dir,
                self.get_output_name_for_group,
                log_callback=self.log_signal.emit,
                progress_callback=self.progress_signal.emit
            )
            self.finished.emit(output_files)
        except Exception as e:
            self.log_signal.emit(f"❌ 批处理失败：{e}")
            self.finished.emit([])


class BatchThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int, int)
    finished = Signal(list)

    def __init__(self, items, settings, get_output_dir, get_output_name_for_group, module):
        super().__init__()
        self.items = items
        self.settings = settings
        self.get_output_dir = get_output_dir
        self.get_output_name_for_group = get_output_name_for_group
        self.module = module
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def run(self):
        try:
            total = len(self.items)
            def progress_wrapper(p):
                current = int(p / 100 * total)
                self.progress_signal.emit(current, total)

            output_files = self.module.run_batch(
                self.items,
                self.settings,
                self.get_output_dir,
                self.get_output_name_for_group,
                log_callback=self.log_signal.emit,
                progress_callback=progress_wrapper,
                stop_check=lambda: self._stop_requested
            )
            self.finished.emit(output_files)
        except Exception as e:
            self.log_signal.emit(f"❌ 批处理失败：{e}")
            self.finished.emit([])


class UIMixin:
    def _build_top_bar(self):
        bar = QHBoxLayout()
        self.btn_add_file = QPushButton("添加文件")
        self.btn_add_file.setStyleSheet("background-color: #4CAF50; color: white; border: none; padding: 6px 12px; border-radius: 6px;")
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_add_folder.setStyleSheet("background-color: #4CAF50; color: white; border: none; padding: 6px 12px; border-radius: 6px;")
        self.btn_remove_sel = QPushButton("移除选中")
        self.btn_remove_sel.setStyleSheet("background-color: #607D8B; color: white; border: none; border-radius: 6px; padding: 6px 12px;")
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.setStyleSheet("background-color: #607D8B; color: white; border: none; border-radius: 6px; padding: 6px 12px;")
        bar.addWidget(self.btn_add_file)
        bar.addWidget(self.btn_add_folder)
        bar.addWidget(self.btn_remove_sel)
        bar.addWidget(self.btn_clear)
        bar.addStretch()

        self.btn_add_file.clicked.connect(self.add_files)
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_remove_sel.clicked.connect(self.remove_selected_rows)
        self.btn_clear.clicked.connect(self.clear_list)
        return bar

    def _build_table_panel(self):
        panel = QWidget()
        lay = QVBoxLayout(panel)

        title_row = QHBoxLayout()
        title = QLabel("文件管理与设置")
        f = QFont(title.font())
        f.setBold(True)
        title.setFont(f)
        title_row.addWidget(title)
        title_row.addStretch()

        self.replace_check = QCheckBox("处理后替换为输出文件")
        self.replace_check.setChecked(False)
        title_row.addWidget(self.replace_check)
        title_row.addSpacing(8)

        self.delete_source_check = QCheckBox("处理后删除源文件")
        self.delete_source_check.setChecked(False)
        title_row.addWidget(self.delete_source_check)
        title_row.addSpacing(12)

        self.btn_help_general = QPushButton("帮助")
        self.btn_help_general.setStyleSheet("background-color: #f5f5f5; color: #333; border: 1px solid #ccc; border-radius: 4px; padding: 4px 18px; font-size: 11px; min-height: 28px;")
        self.btn_help_general.clicked.connect(self.show_help_general)
        title_row.addWidget(self.btn_help_general)
        lay.addLayout(title_row)

        hint = QLabel("提示：双击“输出文件名”可修改，拖拽行调整顺序，支持拖曳添加文件")
        hint.setStyleSheet("color:#777;")
        lay.addWidget(hint)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["选择", "序号", "输入文件名", "设置", "输出文件名", "状态"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setAcceptDrops(True)
        self.table.setDragEnabled(True)
        self.table.setDragDropMode(QTableWidget.InternalMove)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(self.COL_CHECK, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_INDEX, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(self.COL_INPUT, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_PREVIEW, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_OUTNAME, QHeaderView.Stretch)
        hdr.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        hdr.setStretchLastSection(False)

        hdr.sectionClicked.connect(self._on_header_clicked)
        self.table.itemDoubleClicked.connect(self.on_cell_double_clicked)

        lay.addWidget(self.table, stretch=1)
        return panel

    def _build_log_panel(self):
        panel = QWidget()
        lay = QVBoxLayout(panel)

        header_row = QHBoxLayout()
        title = QLabel("操作日志")
        f = QFont(title.font())
        f.setBold(True)
        title.setFont(f)
        header_row.addWidget(title)
        header_row.addStretch()

        self.btn_stop_task = QPushButton("终止任务 (ESC)")
        self.btn_stop_task.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
                font-size: 11px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #d0d0d0;
                color: #888;
            }
        """)
        self.btn_stop_task.setEnabled(False)
        self.btn_stop_task.clicked.connect(self._stop_task)
        header_row.addWidget(self.btn_stop_task)

        lay.addLayout(header_row)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.document().setMaximumBlockCount(1000)
        self.progress = QProgressBar()

        lay.addWidget(self.log_box, stretch=1)
        lay.addWidget(self.progress)
        return panel

    def _build_right_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(380)
        root = QVBoxLayout(panel)

        grp_feature = QGroupBox("功能")
        v = QVBoxLayout(grp_feature)

        if len(self.categories) > 1:
            box_row = QHBoxLayout()
            box_row.setSpacing(8)
            self.category_box = QComboBox()
            cat_name_map = {"pdf": "PDF", "img": "图片", "video": "视频"}
            for cat in self.categories:
                display_name = cat_name_map.get(cat, cat)
                self.category_box.addItem(display_name, cat)
            self.category_box.currentIndexChanged.connect(self._on_category_changed)
            self.category_box.setFixedWidth(80)
            box_row.addWidget(self.category_box)

            self.feature_box = QComboBox()
            self._refresh_feature_box()
            box_row.addWidget(self.feature_box, 1)
            v.addLayout(box_row)
        else:
            self.feature_box = QComboBox()
            self._refresh_feature_box()
            v.addWidget(self.feature_box)

        root.addWidget(grp_feature)

        self.grp_specific = QGroupBox("特有设置")
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.layout_specific = QVBoxLayout(self.scroll_content)
        self.layout_specific.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.scroll_content)

        group_layout = QVBoxLayout(self.grp_specific)
        group_layout.addWidget(self.scroll_area)

        root.addWidget(self.grp_specific, stretch=1)

        grp_name = QGroupBox("命名设置")
        v = QVBoxLayout(grp_name)

        self.naming_rule_display = QLineEdit()
        self.naming_rule_display.setPlaceholderText("当前保留原名（点击右侧图标编辑规则）")
        self.naming_rule_display.setStyleSheet("background-color: #f5f5f5; color: #333;")
        self.naming_rule_display.setClearButtonEnabled(True)

        edit_action = QAction(self)
        edit_action.setIcon(QIcon(resource_path("assets/edit.png")))
        edit_action.setToolTip("编辑命名规则")
        edit_action.triggered.connect(self._show_naming_editor)
        self.naming_rule_display.addAction(edit_action, QLineEdit.TrailingPosition)

        v.addWidget(self.naming_rule_display)
        root.addWidget(grp_name)

        grp_out = QGroupBox("输出位置")
        v = QVBoxLayout(grp_out)

        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("当前原位置（点击右侧图标选择文件夹）")
        self.output_dir.setStyleSheet("background-color: #f5f5f5; color: #333;")
        self.output_dir.setClearButtonEnabled(True)
        self.output_dir.textChanged.connect(self.recompute_outputs)

        browse_action = QAction(self)
        browse_action.setIcon(QIcon(resource_path("assets/folder.png")))
        browse_action.setToolTip("选择输出目录")
        browse_action.triggered.connect(self.choose_output_dir)
        self.output_dir.addAction(browse_action, QLineEdit.TrailingPosition)

        v.addWidget(self.output_dir)
        root.addWidget(grp_out)

        root.addStretch()

        action_row = QHBoxLayout()
        self.btn_open_output = QPushButton("打开输出目录")
        self.btn_start = QPushButton("开始处理")
        self.btn_start.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; border: none; border-radius: 6px; padding: 8px 16px;")
        self.btn_quit = QPushButton("退出")
        self.btn_quit.setStyleSheet("background-color: #f44336; color: white; border: none; border-radius: 6px; padding: 6px 12px;")
        action_row.addWidget(self.btn_open_output)
        action_row.addSpacing(25)
        action_row.addWidget(self.btn_start)
        action_row.addWidget(self.btn_quit)
        root.addLayout(action_row)

        self.btn_open_output.clicked.connect(self.open_output_dir)
        self.btn_start.clicked.connect(self.start_task)
        self.btn_quit.clicked.connect(self.close)

        return panel


class BaseMainWindow(UIMixin, QMainWindow):
    COL_CHECK = 0
    COL_INDEX = 1
    COL_INPUT = 2
    COL_PREVIEW = 3
    COL_OUTNAME = 4
    COL_STATUS = 5

    def __init__(self, app_title: str, feature_modules: list, icon_path: str = "logo.ico", help_text: str = ""):
        super().__init__()
        self._help_text = help_text
        self.setWindowTitle(app_title)
        icon_full_path = resource_path(icon_path)
        if os.path.exists(icon_full_path):
            self.setWindowIcon(QIcon(icon_full_path))
        self.resize(1080, 680)

        self.setStyleSheet("""
            QPushButton { padding: 6px 12px; min-height: 32px; font-weight: 600; border: 1px solid #c9c9c9; border-radius: 6px; }
            QPushButton:hover { border-color: #888; background: #f5f5f5; }
            QGroupBox { font-weight: 600; margin-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
            QTableWidget {
                gridline-color: #e5e5e5;
                selection-background-color: #e0e0e0;
                selection-color: black;
                alternate-background-color: #fafafa;
            }
        """)

        self.preview_mgr = FileListModel()
        self.naming_rules = NamingRules()
        self.output_path = OutputPath()
        self.current_thread = None
        self.current_worker = None
        self.batch_thread = None
        self.group_custom_names = {}
        self.sort_reverse = False
        self.user_sorted = False
        self.is_processing = False
        self.last_progress_update = 0
        self.progress_update_interval = 0.1

        self.all_features = feature_modules
        self.categories = self._extract_categories(feature_modules)
        self.current_category = self.categories[0] if self.categories else None
        self.feature_modules = self._filter_features_by_category(self.current_category)
        self.feature_panels = []

        top_bar = self._build_top_bar()
        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.setChildrenCollapsible(False)
        left_splitter.addWidget(self._build_table_panel())
        left_splitter.addWidget(self._build_log_panel())
        left_splitter.setStretchFactor(0, 3)
        left_splitter.setStretchFactor(1, 2)

        right_panel = self._build_right_panel()

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(right_panel)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.addLayout(top_bar)
        root_layout.addWidget(main_splitter, stretch=1)
        self.setCentralWidget(root)

        self.output_dir.textChanged.connect(self.recompute_outputs)
        self.naming_rule_display.textChanged.connect(self._on_naming_rule_cleared)
        self.feature_box.currentIndexChanged.connect(self.on_feature_changed)

        self._init_feature_panels()

        self.setAcceptDrops(True)
        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self._stop_task)

    def _extract_categories(self, features):
        cats = set()
        for feat in features:
            if "category" in feat:
                cats.add(feat["category"])
        ordered = []
        if "pdf" in cats:
            ordered.append("pdf")
        if "img" in cats:
            ordered.append("img")
        for c in cats:
            if c not in ordered:
                ordered.append(c)
        return ordered

    def _filter_features_by_category(self, category):
        if category is None:
            return self.all_features
        return [f for f in self.all_features if f.get("category") == category]

    def _on_header_clicked(self, logicalIndex):
        if logicalIndex == self.COL_INPUT:
            self.sort_reverse = not self.sort_reverse
            self.user_sorted = True
            self._apply_sorting()
        elif logicalIndex == self.COL_CHECK:
            self._toggle_all_checkboxes()

    def _toggle_all_checkboxes(self):
        if not self.preview_mgr.items:
            return
        all_checked = all(item.checked for item in self.preview_mgr.items)
        new_state = not all_checked
        for item in self.preview_mgr.items:
            item.checked = new_state
        self.refresh_table()
        self.append_log(f"已{'全选' if new_state else '取消全选'}")

    def _apply_sorting(self):
        if not self.user_sorted:
            return
        if not self.preview_mgr.items:
            return
        self.preview_mgr.items.sort(key=lambda fi: os.path.basename(fi.input_path), reverse=self.sort_reverse)
        self.refresh_feature_preview()

    def show_help_general(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("帮助")
        dialog.resize(780, 550)
        dialog.setMinimumSize(600, 400)

        main_layout = QVBoxLayout(dialog)

        splitter = QSplitter(Qt.Horizontal)

        self.help_toc = QListWidget()
        self.help_toc.setFixedWidth(150)
        self.help_toc.addItem("📖 功能说明")
        self.help_toc.addItem("📌 通用操作")
        self.help_toc.addItem("📄 关于程序")
        self.help_toc.setCurrentRow(0)
        splitter.addWidget(self.help_toc)

        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(True)
        self.help_browser.setStyleSheet("""
            QTextBrowser {
                padding: 16px;
                background-color: #fafafa;
                border: none;
                line-height: 30px;
            }
        """)
        splitter.addWidget(self.help_browser)

        splitter.setSizes([120, 750])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)

        self.help_content = {
            "📖 功能说明": self._get_help_text(),
            "📌 通用操作": GENERAL_HELP_TEXT,
            "📄 关于程序": get_about_text(),
        }
        self.help_browser.setHtml(self.help_content["📖 功能说明"])
        
        self.help_toc.currentItemChanged.connect(self._on_help_toc_changed)

        btn_ok = QPushButton("确定")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(dialog.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        dialog.exec()

    def _on_help_toc_changed(self, current, previous):
        if current:
            title = current.text()
            if title in self.help_content:
                self.help_browser.setHtml(self.help_content[title])

    def _refresh_feature_box(self):
        self.feature_box.blockSignals(True)
        self.feature_box.clear()
        for feat in self.feature_modules:
            self.feature_box.addItem(feat["name"])
        self.feature_box.blockSignals(False)

    def _on_category_changed(self, idx):
        if idx < 0 or idx >= len(self.categories):
            return
        self.current_category = self.categories[idx]
        self.feature_modules = self._filter_features_by_category(self.current_category)
        self._refresh_feature_box()
        self._init_feature_panels()
        self.feature_box.setCurrentIndex(0)
        self.on_feature_changed(0)

    def _init_feature_panels(self):
        while self.layout_specific.count():
            item = self.layout_specific.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.feature_panels = []
        for feat in self.feature_modules:
            panel = feat["module"].build_panel()
            self.layout_specific.addWidget(panel)
            self.feature_panels.append(panel)
            panel.changed.connect(self.refresh_feature_preview)
            self._connect_extra_signals(feat, panel)

        if self.feature_panels:
            self._show_only_panel(self.feature_panels[0])
        self.refresh_feature_preview()

    def _connect_extra_signals(self, feat, panel):
        pass

    def _show_only_panel(self, panel_to_show):
        for panel in self.feature_panels:
            panel.setVisible(panel is panel_to_show)

    def _finalize_file_addition(self):
        self.sort_reverse = False
        self.recompute_outputs()

    def add_files(self, paths=None):
        if paths is not None and not isinstance(paths, (list, tuple)):
            paths = None
        if paths is None:
            paths, _ = QFileDialog.getOpenFileNames(self, "选择文件")
            if not paths:
                return
        self.preview_mgr.add_files(paths)
        for item in self.preview_mgr.items:
            item.locked_name = False
        self._finalize_file_addition()

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if not folder:
            return
        all_files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        if not all_files:
            return
        self.preview_mgr.add_files(all_files)
        for item in self.preview_mgr.items:
            item.locked_name = False
        self._finalize_file_addition()

    def remove_selected_rows(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "提示", "请先选中要移除的行")
            return
        self.preview_mgr.remove_selected(rows)
        self.refresh_feature_preview()

    def clear_list(self):
        self.preview_mgr.clear()
        self.refresh_feature_preview()
        self.group_custom_names.clear()

    def choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if path:
            self.output_dir.setText(path)

    def open_output_dir(self):
        if self.output_mode.currentIndex() == 1 and self.output_dir.text().strip():
            target = self.output_dir.text().strip()
        else:
            if not self.preview_mgr.items:
                QMessageBox.information(self, "提示", "列表为空，无法打开目录")
                return
            target = os.path.dirname(self.preview_mgr.items[0].input_path)
        if not os.path.isdir(target):
            QMessageBox.warning(self, "提示", "目录不存在")
            return
        if sys.platform.startswith("win"):
            os.startfile(target)
        elif sys.platform == "darwin":
            subprocess.run(["open", target])
        else:
            subprocess.run(["xdg-open", target])

    def on_feature_changed(self, idx: int):
        if idx < len(self.feature_panels):
            self._show_only_panel(self.feature_panels[idx])
        self.refresh_feature_preview()

    def _show_naming_editor(self):
        from .utils import NamingRules
        dlg = NamingRulesDialog(self.naming_rules, self)
        if dlg.exec() == QDialog.Accepted:
            self.naming_rules = dlg.get_rules()
            self.naming_rules.enabled = True
            preview_text = self.naming_rules.get_preview()
            if preview_text and preview_text != "保留原名":
                self.naming_rule_display.setText(preview_text)
            else:
                self.naming_rule_display.setText("")
                self.naming_rule_display.setPlaceholderText("保留原名（点击编辑按钮设置规则）")
            self.recompute_outputs()

    def _on_naming_rule_cleared(self, text):
        if not text:
            self.naming_rules = NamingRules()
            self.naming_rules.enabled = False
            self.naming_rule_display.setPlaceholderText("保留原名（点击编辑按钮设置规则）")
            self.recompute_outputs()

    def recompute_outputs(self):
        self.output_path.mode = "custom" if self.output_dir.text().strip() else "source"
        self.output_path.custom_dir = self.output_dir.text().strip()

        idx = self.feature_box.currentIndex()
        is_batch = False
        if idx >= 0 and idx < len(self.feature_modules):
            module = self.feature_modules[idx]["module"]
            is_batch = hasattr(module, "run_batch")

        custom_names = []
        if self.naming_rules.enabled:
            for rule in self.naming_rules.rules:
                if rule.rule_type == "user_input" and rule.enabled:
                    custom_names = rule.params.get("names", [])
                    break

        group_name_map = {}
        if is_batch and self.naming_rules.enabled and custom_names:
            groups = {}
            for item in self.preview_mgr.items:
                if item.checked:
                    gk = item.preview_extra.get("group_key", "")
                    if gk:
                        groups.setdefault(gk, []).append(item)
            group_keys = sorted(groups.keys(), key=lambda k: self.preview_mgr.items.index(groups[k][0]))
            for g_idx, gk in enumerate(group_keys):
                if g_idx < len(custom_names):
                    group_name_map[gk] = custom_names[g_idx]
                else:
                    group_name_map[gk] = gk

        for idx, item in enumerate(self.preview_mgr.items):
            item.output_dir = self.output_path.get_dir(item.input_path)
            base_name = os.path.splitext(os.path.basename(item.input_path))[0]

            if is_batch and item.checked:
                gk = item.preview_extra.get("group_key", "")
                if gk and gk in group_name_map:
                    base_name = group_name_map[gk]

            if self.naming_rules.enabled and any(r.enabled for r in self.naming_rules.rules):
                suggested = self.naming_rules.apply(base_name, idx)
            else:
                suggested = base_name

            if item.output_name:
                ext = os.path.splitext(item.output_name)[1]
            else:
                ext = os.path.splitext(item.input_path)[1]
            if not ext:
                ext = ".pdf"

            if not suggested.endswith(ext):
                suggested += ext

            if not getattr(item, "locked_name", False):
                item.output_name = os.path.basename(suggested)

        self.refresh_feature_preview()

    def refresh_feature_preview(self):
        if getattr(self, 'is_processing', False):
            return
        if not self.preview_mgr.items:
            self.refresh_table()
            return
        idx = self.feature_box.currentIndex()
        if idx < len(self.feature_modules):
            module = self.feature_modules[idx]["module"]
            settings = module.collect_settings(self.feature_panels[idx])
            module.prepare_preview(self.preview_mgr.items, settings)
        self.refresh_table()

    def refresh_table(self):
        if getattr(self, 'is_processing', False):
            return

        idx = self.feature_box.currentIndex()
        is_batch = False
        group_display_map = {}
        if idx >= 0 and idx < len(self.feature_modules):
            module = self.feature_modules[idx]["module"]
            is_batch = hasattr(module, "run_batch")

        if is_batch:
            groups = {}
            for it in self.preview_mgr.items:
                gk = it.preview_extra.get("group_key", "")
                if gk:
                    groups.setdefault(gk, []).append(it)
            group_keys = sorted(groups.keys(), key=lambda k: self.preview_mgr.items.index(groups[k][0]))
            for g_idx, gk in enumerate(group_keys):
                if gk in self.group_custom_names:
                    display_name = self.group_custom_names[gk]
                else:
                    if self.naming_rules.enabled:
                        display_name = self.naming_rules.apply(gk, g_idx)
                    else:
                        display_name = gk
                first_item = groups[gk][0]
                _, ext = os.path.splitext(first_item.output_name)
                if display_name and not display_name.endswith(ext):
                    display_name = display_name + ext
                group_display_map[gk] = display_name

        self.table.setRowCount(0)
        for i, item in enumerate(self.preview_mgr.items):
            self.table.insertRow(i)

            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(4, 0, 4, 0)
            check_layout.setSpacing(4)
            check_box = QCheckBox()
            check_box.setChecked(item.checked)
            check_box.stateChanged.connect(lambda state, row=i: self._on_checkbox_toggled(row, state))
            check_layout.addWidget(check_box)
            check_layout.addStretch()
            self.table.setCellWidget(i, self.COL_CHECK, check_widget)

            index_item = QTableWidgetItem(str(i + 1))
            index_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(i, self.COL_INDEX, index_item)

            input_item = QTableWidgetItem(os.path.basename(item.input_path))
            input_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            input_item.setData(Qt.UserRole, item.input_path)
            input_item.setToolTip(item.input_path)
            self.table.setItem(i, self.COL_INPUT, input_item)

            if is_batch:
                gk = item.preview_extra.get("group_key", "")
                display_name = group_display_map.get(gk, item.output_name)
            else:
                display_name = item.output_name
            name_it = QTableWidgetItem(display_name)
            name_it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)
            self.table.setItem(i, self.COL_OUTNAME, name_it)

            prev = (item.preview_extra or {}).get("A", "")
            prev_text = str(prev) if prev else ""
            prev_it = QTableWidgetItem(prev_text)
            prev_it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            prev_it.setToolTip(prev_text)
            self.table.setItem(i, self.COL_PREVIEW, prev_it)

            status_text = item.status
            if not item.checked and status_text == "待处理":
                status_text = "已跳过"
            status_it = QTableWidgetItem(status_text)
            status_it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(i, self.COL_STATUS, status_it)

        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.updateGeometry()

    def _on_checkbox_toggled(self, row: int, state: int):
        if row < 0 or row >= len(self.preview_mgr.items):
            return
        fi = self.preview_mgr.items[row]
        fi.checked = (state == Qt.Checked)

        status_item = self.table.item(row, self.COL_STATUS)
        if status_item:
            if not fi.checked:
                status_item.setText("已跳过")
            elif fi.status == "已跳过":
                fi.status = "待处理"
                status_item.setText("待处理")

    def _handle_drag_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragEnterEvent(self, event):
        self._handle_drag_event(event)

    def dragMoveEvent(self, event):
        self._handle_drag_event(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            if event.source() == self.table:
                event.acceptProposedAction()
                self.user_sorted = True
                self._sync_items_from_table()
                self.append_log("已调整文件顺序")
                return

            paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    paths.append(file_path)
                elif os.path.isdir(file_path):
                    for root, dirs, files in os.walk(file_path):
                        for f in files:
                            paths.append(os.path.join(root, f))

            if paths:
                self.add_files(paths)
                self.append_log(f"拖入 {len(paths)} 个文件")
            event.acceptProposedAction()
            return

        if event.source() == self.table:
            event.acceptProposedAction()
            self._sync_items_from_table()
            self.append_log("已调整文件顺序")

    def _sync_items_from_table(self):
        new_items = []
        for row in range(self.table.rowCount()):
            input_item = self.table.item(row, self.COL_INPUT)
            if input_item:
                full_path = input_item.data(Qt.UserRole)
                if full_path:
                    for fi in self.preview_mgr.items:
                        if fi.input_path == full_path:
                            new_items.append(fi)
                            break
        if len(new_items) == len(self.preview_mgr.items):
            self.preview_mgr.items = new_items

    def on_cell_double_clicked(self, item: QTableWidgetItem):
        row = item.row()
        fi = self.preview_mgr.items[row]
        col = item.column()

        idx = self.feature_box.currentIndex()
        if idx < 0:
            return
        module = self.feature_modules[idx]["module"]
        feature_name = self.feature_modules[idx]["name"]

        if col == self.COL_OUTNAME:
            if hasattr(module, "run_batch"):
                group_name = (fi.preview_extra or {}).get("group_key", "")
                if not group_name:
                    preview_text = (fi.preview_extra or {}).get("A", "")
                    match = re.search(r'组「([^」]+)」', preview_text)
                    if match:
                        group_name = match.group(1)
                    else:
                        return
                current_name = item.text()
                base, ext = os.path.splitext(current_name)
                new_base, ok = QInputDialog.getText(
                    self, "修改分组输出文件名",
                    f"分组「{group_name}」的输出文件名（不含扩展名）：",
                    QLineEdit.Normal, base
                )
                if ok and new_base:
                    new_base = sanitize_base_name(new_base)
                    if not new_base:
                        QMessageBox.warning(self, "提示", "文件名不能为空")
                        return
                    self.group_custom_names[group_name] = new_base

                    current_row = self.table.currentRow()
                    scroll_pos = self.table.verticalScrollBar().value()

                    self.refresh_table()
                    self.append_log(f"分组「{group_name}」输出文件名已改为: {new_base}")

                    if current_row >= 0 and current_row < self.table.rowCount():
                        self.table.selectRow(current_row)
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(10, lambda: self.table.scrollToItem(
                            self.table.item(current_row, 0),
                            QAbstractItemView.PositionAtCenter
                        ))
                    else:
                        self.table.verticalScrollBar().setValue(scroll_pos)
                return

            current_name = fi.output_name or os.path.basename(fi.input_path)
            base, ext = os.path.splitext(current_name)
            base = sanitize_base_name(base)

            dialog = QDialog(self)
            dialog.setWindowTitle("修改输出文件名（不含后缀）")

            layout = QVBoxLayout(dialog)
            layout.addWidget(QLabel("新文件名："))

            line_edit = QLineEdit()
            line_edit.setText(base)
            line_edit.selectAll()
            layout.addWidget(line_edit)

            text_width = len(base) * 10 + 60
            width = max(350, min(700, text_width))
            dialog.setFixedWidth(width)

            btn_box = QHBoxLayout()
            btn_ok = QPushButton("确定")
            btn_cancel = QPushButton("取消")
            btn_box.addStretch()
            btn_box.addWidget(btn_ok)
            btn_box.addWidget(btn_cancel)
            layout.addLayout(btn_box)

            btn_ok.clicked.connect(dialog.accept)
            btn_cancel.clicked.connect(dialog.reject)

            ok = dialog.exec() == QDialog.Accepted
            new_base = line_edit.text() if ok else ""

            if not ok:
                return
            new_base = sanitize_base_name(new_base)
            if not new_base:
                QMessageBox.warning(self, "提示", "文件名不能为空")
                return
            fi.output_name = new_base + ext
            fi.locked_name = True

            current_row = self.table.currentRow()
            scroll_pos = self.table.verticalScrollBar().value()

            self.refresh_table()

            if current_row >= 0 and current_row < self.table.rowCount():
                self.table.selectRow(current_row)
                self.table.scrollToItem(self.table.item(current_row, 0), QAbstractItemView.PositionAtCenter)
            else:
                self.table.verticalScrollBar().setValue(scroll_pos)
            return
        
    def start_task(self):
        idx = self.feature_box.currentIndex()
        if idx < 0:
            return
        module = self.feature_modules[idx]["module"]
        panel = self.feature_panels[idx]

        if self.current_thread and self.current_thread.isRunning():
            QMessageBox.warning(self, "提示", "已有任务正在运行，请稍后")
            return
        if self.batch_thread and self.batch_thread.isRunning():
            QMessageBox.warning(self, "提示", "已有批处理任务正在运行，请稍后")
            return

        items_before = len(self.preview_mgr.items)
        valid_items = []
        for item in self.preview_mgr.items:
            if os.path.exists(item.input_path):
                valid_items.append(item)
            else:
                self.append_log(f"已移除：{os.path.basename(item.input_path)}（文件不存在）")
        self.preview_mgr.items = valid_items
        if len(self.preview_mgr.items) < items_before:
            self.refresh_table()

        if not self.preview_mgr.items:
            QMessageBox.warning(self, "提示", "请先添加文件")
            return

        checked_items = [item for item in self.preview_mgr.items if item.checked]
        if not checked_items:
            QMessageBox.warning(self, "提示", "没有勾选任何文件")
            return

        if self.feature_modules[idx]["name"] == "压缩PDF文件":
            from features.pdf_compress import ensure_ghostscript
            if not ensure_ghostscript(self):
                self.append_log("❌ Ghostscript 未配置，压缩任务取消")
                return

        settings = module.collect_settings(panel)
        custom_names = []
        if self.naming_rules.enabled:
            for rule in self.naming_rules.rules:
                if rule.rule_type == "user_input" and rule.enabled:
                    custom_names = rule.params.get("names", [])
                    break
        settings["custom_names"] = custom_names

        module_name = module.__name__.split('.')[-1]

        batch_modules = ["pdf_organize", "img_stitch", "img_gifmaker", "pdf_merge", "video_merge"]
        if module_name in batch_modules:
            def get_output_dir(item):
                if self.output_dir.text().strip():
                    return self.output_dir.text().strip()
                else:
                    return os.path.dirname(item.input_path)

            groups = {}
            for item in checked_items:
                gk = item.preview_extra.get("group_key", "")
                if gk:
                    groups.setdefault(gk, []).append(item)
            group_keys = sorted(groups.keys(), key=lambda k: checked_items.index(groups[k][0]))

            def get_output_name_for_group(group_name):
                if group_name in self.group_custom_names:
                    return self.group_custom_names[group_name]
                if self.naming_rules.enabled:
                    idx = group_keys.index(group_name) if group_name in group_keys else 0
                    return self.naming_rules.apply(group_name, idx)
                else:
                    return group_name

            self.append_log("开始批处理…")
            self.progress.setValue(0)
            self.btn_start.setEnabled(False)
            self.btn_stop_task.setEnabled(True)
            self.is_processing = True

            self.batch_thread = BatchThread(
                checked_items,
                settings,
                get_output_dir,
                get_output_name_for_group,
                module
            )
            self.batch_thread.log_signal.connect(self.append_log)
            self.batch_thread.progress_signal.connect(self.on_progress)

            def on_batch_finished(output_files):
                self.btn_start.setEnabled(True)
                self.btn_stop_task.setEnabled(False)
                self.is_processing = False
                self._delete_source_files(checked_items)
                if self.replace_check.isChecked():
                    self._replace_items_with_outputs(checked_items, output_files)
                else:
                    self.refresh_feature_preview()
                self.refresh_table()
                self.progress.setValue(100)
                total = len(checked_items)
                self.progress.setFormat(f"{total}/{total}")
                self.replace_check.setChecked(False)
                self.delete_source_check.setChecked(False)
                self.batch_thread.deleteLater()
                self.batch_thread = None

            self.batch_thread.finished.connect(on_batch_finished)
            self.batch_thread.start()
            return

        def on_batch_finished(output_files):
            self.btn_start.setEnabled(True)
            self.btn_stop_task.setEnabled(False)
            self.is_processing = False
            self._delete_source_files(checked_items)
            if self.replace_check.isChecked():
                self._replace_items_with_outputs(checked_items, output_files)
            else:
                self.refresh_feature_preview()
            self.refresh_table()
            self.progress.setValue(100)
            total = len(checked_items)
            self.progress.setFormat(f"{total}/{total}")
            self.replace_check.setChecked(False)
            self.delete_source_check.setChecked(False)
            self.batch_thread.deleteLater()
            self.batch_thread = None
            return

        if module_name == "pdf_organize":
            self.append_log("❌ 错误：组织PDF页面功能不支持单任务模式")
            self.btn_start.setEnabled(True)
            self.btn_stop_task.setEnabled(False)
            self.is_processing = False
            return

        one_to_many = ["img_split", "pdf_convert"]
        if module_name in one_to_many:
            task_func = lambda fi: module.run_task(fi, settings, custom_names=settings.get("custom_names", []))
        else:
            task_func = lambda fi: module.run_task(fi, settings)

        self.append_log("开始处理…")
        self.progress.setValue(0)
        self.btn_start.setEnabled(False)
        self.btn_stop_task.setEnabled(True)

        self.current_thread = QThread()
        self.current_worker = Worker()
        self.current_worker.moveToThread(self.current_thread)

        self.current_worker.signals.log_batch.connect(self.append_log_batch)
        self.current_worker.signals.progress.connect(self.on_progress)
        self.is_processing = True

        def on_task_finished():
            if self.current_thread:
                self.current_thread.quit()
                self.current_thread.wait()
                self.current_thread.deleteLater()
                self.current_thread = None
            if self.current_worker:
                self.current_worker.deleteLater()
                self.current_worker = None
            self.btn_start.setEnabled(True)
            self.btn_stop_task.setEnabled(False)
            self.is_processing = False
            self._delete_source_files(checked_items)
            if self.replace_check.isChecked():
                self._replace_items_with_outputs(checked_items, None)
            else:
                self.refresh_feature_preview()
            self.refresh_table()
            self.progress.setValue(100)
            total = len(checked_items)
            self.progress.setFormat(f"{total}/{total}")
            self.replace_check.setChecked(False)
            self.delete_source_check.setChecked(False)

        self.current_worker.signals.finished.connect(on_task_finished)
        self.current_thread.started.connect(
            lambda: self.current_worker.run(checked_items, task_func)
        )
        self.current_thread.start()

    def _stop_task(self):
        try:
            if not self.current_worker and not self.batch_thread:
                return

            self.append_log("⛔ 正在请求终止任务…")

            if self.current_worker and hasattr(self.current_worker, 'request_stop'):
                self.current_worker.request_stop()

            if self.batch_thread and hasattr(self.batch_thread, 'request_stop'):
                self.batch_thread.request_stop()

        except Exception as e:
            self.append_log(f"❌ 终止任务时发生异常：{e}")
            import traceback
            self.append_log(traceback.format_exc())

    def _delete_source_files(self, items):
        if not self.delete_source_check.isChecked():
            return
        deleted_count = 0
        for item in items:
            try:
                if os.path.exists(item.input_path):
                    os.remove(item.input_path)
                    deleted_count += 1
            except Exception as e:
                self.append_log(f"删除失败：{os.path.basename(item.input_path)} - {e}")
        if deleted_count > 0:
            self.append_log(f"已删除 {deleted_count} 个源文件")

    def _replace_items_with_outputs(self, items, output_files):
        new_items = []
        if output_files is None:
            for item in items:
                if hasattr(item, "output_paths") and item.output_paths:
                    for out_path in item.output_paths:
                        if os.path.exists(out_path):
                            new_item = FileItem(
                                input_path=out_path,
                                output_name=os.path.basename(out_path),
                                output_dir=os.path.dirname(out_path),
                                status="待处理",
                                checked=True
                            )
                            new_items.append(new_item)
                else:
                    out_path = item.full_output_path()
                    if os.path.exists(out_path):
                        new_item = FileItem(
                            input_path=out_path,
                            output_name=os.path.basename(out_path),
                            output_dir=os.path.dirname(out_path),
                            status="待处理",
                            checked=True
                        )
                        new_items.append(new_item)
            self._replace_items_in_list(items, new_items)
            return

        if output_files:
            for out_path in output_files:
                if os.path.exists(out_path):
                    new_item = FileItem(
                        input_path=out_path,
                        output_name=os.path.basename(out_path),
                        output_dir=os.path.dirname(out_path),
                        status="待处理",
                        checked=True
                    )
                    new_items.append(new_item)
            self._replace_items_in_list(items, new_items)
        else:
            self.refresh_feature_preview()

    def _replace_items_in_list(self, old_items, new_items):
        for item in old_items:
            if item in self.preview_mgr.items:
                self.preview_mgr.items.remove(item)
        self.preview_mgr.items.extend(new_items)
        self.sort_reverse = False
        self.refresh_feature_preview()
        self.append_log(f"已替换为输出文件（{len(new_items)} 个文件）")

    def show_help(self):
        help_text = self._get_help_text()
        dialog = QDialog(self)
        dialog.setWindowTitle("功能说明")
        dialog.resize(650, 450)
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)
        text_browser = QTextBrowser()
        text_browser.setReadOnly(True)
        text_browser.setOpenExternalLinks(True)
        text_browser.setHtml(help_text)
        layout.addWidget(text_browser)

        btn_ok = QPushButton("确定")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(dialog.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.exec()

    def _get_help_text(self):
        if self._help_text:
            return self._help_text
        return "请重写此方法以显示具体的帮助内容。"

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if self.table.hasFocus():
                self.remove_selected_rows()
                event.accept()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.current_thread and self.current_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "任务正在运行，确定要退出吗？正在进行的转换将会中断。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.current_thread.quit()
                if not self.current_thread.wait(3000):
                    self.current_thread.terminate()
                    self.current_thread.wait()
                event.accept()
            else:
                event.ignore()
        elif self.batch_thread and self.batch_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "批处理任务正在运行，确定要退出吗？正在进行的任务将会中断。",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.batch_thread.quit()
                if not self.batch_thread.wait(3000):
                    self.batch_thread.terminate()
                    self.batch_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def append_log(self, msg: str):
        self.log_box.append(msg)
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )

    def append_log_batch(self, messages: list):
        self.log_box.append("\n".join(messages))
        self.log_box.verticalScrollBar().setValue(
            self.log_box.verticalScrollBar().maximum()
        )

    def on_progress(self, current: int, total: int):
        now = time.time()
        if now - self.last_progress_update >= self.progress_update_interval:
            self.progress.setValue(int(current / total * 100))
            self.progress.setFormat(f"{current}/{total}")
            self.last_progress_update = now


class NamingRulesDialog(QDialog):
    def __init__(self, rules: NamingRules, parent=None):
        super().__init__(parent)
        self.rules = rules
        self.selected_index = -1
        self._loading_rule = False

        self.setWindowTitle("命名规则编辑器")
        self.setMinimumWidth(700)
        self.resize(720, 520)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(14, 14, 14, 14)

        header = QHBoxLayout()
        header.setSpacing(2)
        header.addWidget(QLabel("规则列表："))
        header.addStretch()

        self.add_btn = QPushButton("+ 添加")
        self.add_btn.setFixedHeight(18)
        self.add_menu = QMenu(self.add_btn)
        self.add_menu.addAction("插入").triggered.connect(lambda: self._add_rule("insert"))
        self.add_menu.addAction("用户输入").triggered.connect(lambda: self._add_rule("user_input"))
        self.add_btn.setMenu(self.add_menu)
        header.addWidget(self.add_btn)

        self.del_btn = QPushButton("- 删除")
        self.del_btn.setFixedHeight(18)
        self.del_btn.clicked.connect(self._delete_selected)
        self.del_btn.setEnabled(False)
        header.addWidget(self.del_btn)

        self.up_btn = QPushButton("↑ 上移")
        self.up_btn.setFixedHeight(18)
        self.up_btn.clicked.connect(self._move_up)
        self.up_btn.setEnabled(False)
        header.addWidget(self.up_btn)

        self.down_btn = QPushButton("↓ 下移")
        self.down_btn.setFixedHeight(18)
        self.down_btn.clicked.connect(self._move_down)
        self.down_btn.setEnabled(False)
        header.addWidget(self.down_btn)

        main_layout.addLayout(header)

        self.rule_table = QTableWidget()
        self.rule_table.setColumnCount(3)
        self.rule_table.setHorizontalHeaderLabels(["选择", "序号", "规则"])
        self.rule_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.rule_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.rule_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rule_table.verticalHeader().setVisible(False)
        self.rule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rule_table.setSelectionMode(QTableWidget.SingleSelection)
        self.rule_table.setShowGrid(False)
        self.rule_table.setFixedHeight(110)
        self.rule_table.itemClicked.connect(self._on_rule_selected)
        main_layout.addWidget(self.rule_table)

        main_layout.addSpacing(6)

        self.config_stack = QStackedWidget()
        self.config_stack.setFixedHeight(260)
        main_layout.addWidget(self.config_stack)

        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setContentsMargins(0, 0, 0, 0)
        empty_label = QLabel("暂无规则，请点击「+ 添加」按钮添加规则")
        empty_label.setStyleSheet("color: #999; font-size: 12px;")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.config_stack.addWidget(self.empty_widget)

        self.insert_widget = QWidget()
        ins_layout = QVBoxLayout(self.insert_widget)
        ins_layout.setSpacing(0)
        ins_layout.setContentsMargins(0, 0, 0, 0)

        row_text = QHBoxLayout()
        row_text.setSpacing(2)
        row_text.addWidget(QLabel("插入文本："))
        self.insert_text = QLineEdit()
        self.insert_text.setFixedHeight(28)
        self.insert_text.textChanged.connect(self._on_config_changed)
        row_text.addWidget(self.insert_text)
        ins_layout.addLayout(row_text)

        ins_layout.addSpacing(10)

        row_pos = QHBoxLayout()
        row_pos.setSpacing(2)
        row_pos.addWidget(QLabel("位置："))

        self.position_group = QButtonGroup(self)
        self.rb_prefix = QRadioButton("前缀")
        self.rb_suffix = QRadioButton("后缀")
        self.rb_position = QRadioButton("位置")
        self.rb_after = QRadioButton("到文本后")
        self.rb_before = QRadioButton("到文本前")

        for rb in (self.rb_prefix, self.rb_suffix, self.rb_position, self.rb_after, self.rb_before):
            self.position_group.addButton(rb)
            rb.toggled.connect(self._on_position_toggled)
            rb.toggled.connect(self._on_config_changed)

        row_pos.addWidget(self.rb_prefix)
        row_pos.addWidget(self.rb_suffix)
        row_pos.addWidget(self.rb_position)

        self.pos_container = QWidget()
        pos_container_layout = QHBoxLayout(self.pos_container)
        pos_container_layout.setContentsMargins(0, 0, 0, 0)
        pos_container_layout.setSpacing(2)

        self.pos_spin = QSpinBox()
        self.pos_spin.setRange(1, 9999)
        self.pos_spin.setValue(1)
        self.pos_spin.setFixedWidth(80)
        self.pos_spin.valueChanged.connect(self._on_config_changed)
        pos_container_layout.addWidget(self.pos_spin)

        self.from_right = QCheckBox("从右到左")
        self.from_right.stateChanged.connect(self._on_config_changed)
        pos_container_layout.addWidget(self.from_right)

        row_pos.addWidget(self.pos_container)
        row_pos.addWidget(self.rb_after)

        self.after_edit = QLineEdit()
        self.after_edit.setPlaceholderText("目标文本")
        self.after_edit.setFixedWidth(140)
        self.after_edit.textChanged.connect(self._on_config_changed)
        row_pos.addWidget(self.after_edit)

        row_pos.addWidget(self.rb_before)

        self.before_edit = QLineEdit()
        self.before_edit.setPlaceholderText("目标文本")
        self.before_edit.setFixedWidth(140)
        self.before_edit.textChanged.connect(self._on_config_changed)
        row_pos.addWidget(self.before_edit)

        row_pos.addStretch()
        ins_layout.addLayout(row_pos)
        ins_layout.addStretch()

        self.rb_prefix.setChecked(True)
        self._update_insert_visibility()
        self.config_stack.addWidget(self.insert_widget)

        self.user_widget = QWidget()
        usr_layout = QVBoxLayout(self.user_widget)
        usr_layout.setSpacing(3)
        usr_layout.setContentsMargins(0, 2, 0, 2)

        u1 = QHBoxLayout()
        u1.setSpacing(2)
        u1.addWidget(QLabel("输入新的文件名（每行一个）："))
        u1.addStretch()
        self.user_count = QLabel("需要 0 个，已输入 0 个")
        self.user_count.setStyleSheet("color: #666;")
        u1.addWidget(self.user_count)
        usr_layout.addLayout(u1)

        self.user_text = QTextEdit()
        self.user_text.setFixedHeight(210)
        self.user_text.textChanged.connect(self._on_user_text_changed)
        usr_layout.addWidget(self.user_text)

        u2 = QHBoxLayout()
        u2.setSpacing(2)
        self.user_mode_group = QButtonGroup(self)
        self.rb_ureplace = QRadioButton("替换当前名称")
        self.rb_uinsert_before = QRadioButton("插入到当前名称前")
        self.rb_uinsert_after = QRadioButton("插入到当前名称后")

        for rb in (self.rb_ureplace, self.rb_uinsert_before, self.rb_uinsert_after):
            self.user_mode_group.addButton(rb)
            rb.toggled.connect(self._on_config_changed)

        u2.addWidget(self.rb_ureplace)
        u2.addWidget(self.rb_uinsert_before)
        u2.addWidget(self.rb_uinsert_after)
        u2.addStretch()
        usr_layout.addLayout(u2)

        self.rb_ureplace.setChecked(True)
        self.config_stack.addWidget(self.user_widget)

        main_layout.addSpacing(6)

        preview = QHBoxLayout()
        preview.setSpacing(2)
        preview.addWidget(QLabel("预览："))
        self.preview_display = QLineEdit()
        self.preview_display.setReadOnly(True)
        self.preview_display.setStyleSheet("background-color: #f5f5f5;")
        preview.addWidget(self.preview_display)
        main_layout.addLayout(preview)

        main_layout.addSpacing(6)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_ok = QPushButton("确定")
        self.btn_ok.setFixedWidth(80)
        self.btn_ok.clicked.connect(self._on_accept)
        btn_layout.addWidget(self.btn_ok)

        btn_layout.addSpacing(10)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedWidth(80)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        main_layout.addLayout(btn_layout)

        self._refresh_table()
        if self.rules.rules:
            self.rule_table.setCurrentCell(0, 0)
            self._on_rule_selected(self.rule_table.item(0, 2))
        else:
            self.config_stack.setCurrentIndex(0) 

    def _refresh_table(self):
        self.rule_table.blockSignals(True)
        self.rule_table.setRowCount(0)
        for i, rule in enumerate(self.rules.rules):
            self.rule_table.insertRow(i)

            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.setContentsMargins(2, 0, 2, 0)
            check_layout.setSpacing(2)
            cb = QCheckBox()
            cb.setChecked(rule.enabled)
            cb.stateChanged.connect(lambda state, row=i: self._on_checkbox_toggled(row, state))
            check_layout.addWidget(cb)
            check_layout.addStretch()
            self.rule_table.setCellWidget(i, 0, check_widget)

            seq_item = QTableWidgetItem(str(i + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            seq_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.rule_table.setItem(i, 1, seq_item)

            desc_item = QTableWidgetItem(rule.get_description())
            desc_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            if not rule.enabled:
                desc_item.setForeground(QColor(150, 150, 150))
            self.rule_table.setItem(i, 2, desc_item)

        self.rule_table.resizeRowsToContents()
        self.rule_table.blockSignals(False)

    def _on_checkbox_toggled(self, row, state):
        if row < 0 or row >= len(self.rules.rules):
            return
        rule = self.rules.rules[row]
        rule.enabled = (state == Qt.Checked)
        item = self.rule_table.item(row, 2)
        if item:
            item.setForeground(QColor(0, 0, 0) if rule.enabled else QColor(150, 150, 150))
        self._update_preview()

    def _on_rule_selected(self, item):
        row = self.rule_table.currentRow()
        if row < 0 or row >= len(self.rules.rules):
            return
        self.selected_index = row
        self.del_btn.setEnabled(True)
        self.up_btn.setEnabled(row > 0)
        self.down_btn.setEnabled(row < len(self.rules.rules) - 1)

        rule = self.rules.rules[row]
        self._loading_rule = True

        if rule.rule_type == "insert":
            self.config_stack.setCurrentIndex(1)
            self.insert_text.setText(rule.params.get("text", ""))
            mode = rule.params.get("mode", "prefix")
            mode_map = {
                "prefix": self.rb_prefix,
                "suffix": self.rb_suffix,
                "position": self.rb_position,
                "after_text": self.rb_after,
                "before_text": self.rb_before
            }
            if mode in mode_map:
                mode_map[mode].setChecked(True)
            self.pos_spin.setValue(rule.params.get("position", 1))
            self.from_right.setChecked(rule.params.get("from_right", False))
            self.after_edit.setText(rule.params.get("after_text", ""))
            self.before_edit.setText(rule.params.get("before_text", ""))
            self._update_insert_visibility()
        else: 
            self.config_stack.setCurrentIndex(2)
            names = rule.params.get("names", [])
            self.user_text.setPlainText("\n".join(names))
            self._update_user_count()
            mode = rule.params.get("mode", "replace")
            mode_map = {
                "replace": self.rb_ureplace,
                "insert_before": self.rb_uinsert_before,
                "insert_after": self.rb_uinsert_after
            }
            if mode in mode_map:
                mode_map[mode].setChecked(True)

        self._loading_rule = False
        self._update_preview()

    def _update_insert_visibility(self):
        self.pos_container.setVisible(self.rb_position.isChecked())
        self.after_edit.setVisible(self.rb_after.isChecked())
        self.before_edit.setVisible(self.rb_before.isChecked())

    def _on_position_toggled(self):
        self._update_insert_visibility()
        self._on_config_changed()

    def _get_needed_count(self) -> int:
        parent = self.parent()
        if not parent or not hasattr(parent, 'preview_mgr'):
            return 0

        idx = parent.feature_box.currentIndex() if hasattr(parent, 'feature_box') else -1
        if idx < 0:
            return len(parent.preview_mgr.items)

        module = parent.feature_modules[idx]["module"] if hasattr(parent, 'feature_modules') else None
        module_name = module.__name__.split('.')[-1] if module else ""

        checked_items = [item for item in parent.preview_mgr.items if item.checked]
        if not checked_items:
            return len(parent.preview_mgr.items)

        one_to_many = ["pdf_organize", "img_split", "pdf_convert"]

        if module_name in one_to_many:
            panel = parent.feature_panels[idx] if hasattr(parent, 'feature_panels') else None
            if panel:
                settings = module.collect_settings(panel) if hasattr(module, 'collect_settings') else {}
            else:
                settings = {}

            if module_name == "pdf_organize":
                if settings.get("mode", 0) == 3:
                    split_mode = settings.get("split_mode", 0)
                    first_file = checked_items[0].input_path
                    try:
                        import fitz
                        doc = fitz.open(first_file)
                        total_pages = len(doc)
                        doc.close()
                    except:
                        total_pages = 1
                    if split_mode == 0:
                        page_count = settings.get("split_page_count", 5)
                        return (total_pages + page_count - 1) // page_count
                    else:
                        range_text = settings.get("split_range_list", "")
                        if range_text.strip():
                            return len(range_text.split(','))
                        return 1
                else:
                    return len(checked_items)

            elif module_name == "img_split":
                rows = settings.get("rows", 2)
                cols = settings.get("cols", 3)
                return rows * cols

            elif module_name == "pdf_convert":
                target = settings.get("target", "").lower()
                if target in ("jpg", "png"):
                    page_expr = settings.get("page_range", "")
                    first_file = checked_items[0].input_path
                    try:
                        import fitz
                        doc = fitz.open(first_file)
                        total_pages = len(doc)
                        doc.close()
                    except:
                        total_pages = 1
                    if page_expr.strip():
                        return len(parse_page_range(page_expr, total_pages))
                    return total_pages
                else:
                    return len(checked_items)

        is_batch = hasattr(module, "run_batch") if module else False
        if is_batch:
            groups = {}
            for item in checked_items:
                gk = item.preview_extra.get("group_key", "")
                if gk:
                    groups.setdefault(gk, []).append(item)
            if groups:
                return len(groups)

            try:
                panel = parent.feature_panels[idx]
                settings = module.collect_settings(panel)
                module.prepare_preview(parent.preview_mgr.items, settings)
                groups = {}
                for item in checked_items:
                    gk = item.preview_extra.get("group_key", "")
                    if gk:
                        groups.setdefault(gk, []).append(item)
                return len(groups) if groups else len(checked_items)
            except:
                return len(checked_items)

        return len(checked_items)

    def _update_user_count(self):
        names = [line.strip() for line in self.user_text.toPlainText().splitlines() if line.strip()]
        needed = self._get_needed_count()
        count = len(names)
        if needed > 0 and count != needed:
            self.user_count.setText(f"需要 {needed} 个，已输入 {count} 个")
            self.user_count.setStyleSheet("color: #E65100;")
        else:
            self.user_count.setText(f"需要 {needed} 个，已输入 {count} 个")
            self.user_count.setStyleSheet("color: #666;")

    def _on_user_text_changed(self):
        if self._loading_rule:
            return
        self._update_user_count()
        self._on_config_changed()

    def _on_config_changed(self):
        if self._loading_rule or self.selected_index < 0 or self.selected_index >= len(self.rules.rules):
            return
        rule = self.rules.rules[self.selected_index]

        if rule.rule_type == "insert":
            rule.params["text"] = self.insert_text.text()
            if self.rb_prefix.isChecked():
                rule.params["mode"] = "prefix"
            elif self.rb_suffix.isChecked():
                rule.params["mode"] = "suffix"
            elif self.rb_position.isChecked():
                rule.params["mode"] = "position"
            elif self.rb_after.isChecked():
                rule.params["mode"] = "after_text"
            elif self.rb_before.isChecked():
                rule.params["mode"] = "before_text"
            rule.params["position"] = self.pos_spin.value()
            rule.params["from_right"] = self.from_right.isChecked()
            rule.params["after_text"] = self.after_edit.text()
            rule.params["before_text"] = self.before_edit.text()
        else:
            names = [line.strip() for line in self.user_text.toPlainText().splitlines() if line.strip()]
            rule.params["names"] = names
            if self.rb_ureplace.isChecked():
                rule.params["mode"] = "replace"
            elif self.rb_uinsert_before.isChecked():
                rule.params["mode"] = "insert_before"
            elif self.rb_uinsert_after.isChecked():
                rule.params["mode"] = "insert_after"

        desc_item = self.rule_table.item(self.selected_index, 2)
        if desc_item:
            desc_item.setText(rule.get_description())
        self._update_preview()

    def _update_preview(self):
        if self.rules.enabled:
            result = self.rules.get_preview("示例文件", 0)
            self.preview_display.setText(f"示例文件 → {result}")
        else:
            self.preview_display.setText("保留原名：示例文件")

    def _add_rule(self, rule_type):
        if rule_type == "insert":
            self.rules.add_rule("insert", {
                "text": "", "mode": "prefix", "position": 1,
                "from_right": False, "after_text": "", "before_text": ""
            })
        else:
            self.rules.add_rule("user_input", {"names": [], "mode": "replace"})
        self._refresh_table()
        new_row = len(self.rules.rules) - 1
        self.rule_table.selectRow(new_row)
        self._on_rule_selected(self.rule_table.item(new_row, 2))
        if rule_type == "user_input":
            self._update_user_count()
        self._update_preview()

    def _delete_selected(self):
        if self.selected_index < 0 or self.selected_index >= len(self.rules.rules):
            return
        self.rules.remove_rule(self.selected_index)
        self.selected_index = -1
        self._refresh_table()
        if self.rules.rules:
            self.rule_table.selectRow(0)
            self._on_rule_selected(self.rule_table.item(0, 2))
        else:
            self.del_btn.setEnabled(False)
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(False)
            self.preview_display.setText("无规则")
            self.config_stack.setCurrentIndex(0)

    def _move_up(self):
        if self.selected_index <= 0:
            return
        self.rules.move_rule(self.selected_index, self.selected_index - 1)
        self.selected_index -= 1
        self._refresh_table()
        self.rule_table.selectRow(self.selected_index)
        self._on_rule_selected(self.rule_table.item(self.selected_index, 2))

    def _move_down(self):
        if self.selected_index >= len(self.rules.rules) - 1:
            return
        self.rules.move_rule(self.selected_index, self.selected_index + 1)
        self.selected_index += 1
        self._refresh_table()
        self.rule_table.selectRow(self.selected_index)
        self._on_rule_selected(self.rule_table.item(self.selected_index, 2))

    def _on_accept(self):
        self.rules.enabled = True
        self.accept()

    def get_rules(self) -> NamingRules:
        return self.rules