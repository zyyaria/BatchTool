# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import sys
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QMessageBox, QDialog, QLabel, QTextEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QAbstractItemView
)
from core.base import BaseMainWindow
from core.utils import resource_path
from core.version import PDF_VERSION
from core.help import get_pdf_help_text
from features import PDF_FEATURES
from features.pdf_resize import detect_page_sizes, get_detect_summary_for_autoset


class PDFMainWindow(BaseMainWindow):
    def __init__(self):
        """初始化主窗口"""
        super().__init__(
            app_title=f"PDF 批量处理工具  v{PDF_VERSION}    ©张小鱼",
            feature_modules=PDF_FEATURES,
            icon_path="assets/logo_pdf.ico",
            help_text=get_pdf_help_text()
        )

    def _connect_extra_signals(self, feat, panel):
        """连接 PDF 特有信号"""
        super()._connect_extra_signals(feat, panel)
        
        if feat["name"] == "调整 PDF 尺寸":
            if hasattr(panel, "detect_requested"):
                try:
                    panel.detect_requested.disconnect(self._on_detect_size_requested)
                except RuntimeError:
                    pass
                panel.detect_requested.connect(self._on_detect_size_requested)
                
        if feat["name"] == "PDF 添加书签":
            if hasattr(panel, "detect_bookmark_signal"):
                try:
                    panel.detect_bookmark_signal.disconnect(self._detect_pages_and_bookmarks)
                except RuntimeError:
                    pass
                panel.detect_bookmark_signal.connect(self._detect_pages_and_bookmarks)
            if hasattr(panel, "clear_bookmark_signal"):
                try:
                    panel.clear_bookmark_signal.disconnect(self._clear_bookmarks)
                except RuntimeError:
                    pass
                panel.clear_bookmark_signal.connect(self._clear_bookmarks)
                
        if feat["name"] == "组织 PDF 页面":
            if hasattr(panel, "detect_page_signal"):
                try:
                    panel.detect_page_signal.disconnect(self._detect_pages)
                except RuntimeError:
                    pass
                panel.detect_page_signal.connect(self._detect_pages)

    def _on_detect_size_requested(self):
        """检测所有文件的页面尺寸，自动设置匹配的标准尺寸"""
        items = self.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加要检测的PDF文件")
            return

        file_paths = [item.input_path for item in items]

        try:
            result = detect_page_sizes(file_paths)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"检测失败：{str(e)}")
            return

        self.append_log("")
        self.append_log("========== 页面尺寸检测 ==========")
        idx = 1
        for file_path, info in result.items():
            base_name = os.path.basename(file_path)
            if info["valid"]:
                self.append_log(f"{idx}. {base_name}: {info['summary']}")
            else:
                self.append_log(f"{idx}. {base_name}: ❌ {info['error']}")
            idx += 1
        self.append_log("========== 检测完成 ==========")
        self.append_log("")

        matched = get_detect_summary_for_autoset(result)
        if matched:
            resize_idx = None
            for i, feat in enumerate(self.feature_modules):
                if feat["name"] == "调整 PDF 尺寸":
                    resize_idx = i
                    break
            if resize_idx is not None:
                panel = self.feature_panels[resize_idx]
                if hasattr(panel, "size_combo"):
                    index = panel.size_combo.findText(matched)
                    if index >= 0:
                        panel.size_combo.setCurrentIndex(index)
                        self.append_log(f"已自动设置目标尺寸为：{matched}")

    def _detect_pages_and_bookmarks(self):
        """检测文件的页码和书签结构"""
        from PyPDF2 import PdfReader

        items = self.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加PDF文件")
            return

        self.append_log("")
        self.append_log("========== 页码与书签检测 ==========")
        self.append_log(f"共检测 {len(items)} 个文件")
        self.append_log("")

        for i, item in enumerate(items, 1):
            file_path = item.input_path
            base_name = os.path.basename(file_path)

            try:
                reader = PdfReader(file_path)
                total_pages = len(reader.pages)
                self.append_log(f"{i}. {base_name} → {total_pages} 页")

                try:
                    outline = reader.outline
                    if callable(outline):
                        outline = outline()
                except Exception:
                    outline = None

                if outline:
                    self.append_log("书签：")
                    for line in self._format_outline(outline, reader):
                        self.append_log(line)
                else:
                    self.append_log("   书签：无")

            except Exception as e:
                self.append_log(f"{i}. {base_name} ❌ 读取失败：{str(e)}")

            self.append_log("")
            self.append_log("----------------------------------------------------")

        self.append_log("========== 检测完成 ==========")
        self.append_log("")

    def _clear_bookmarks(self):
        """清除所有文件的已有书签"""
        from PyPDF2 import PdfReader, PdfWriter
        from PySide6.QtWidgets import QMessageBox

        items = self.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加PDF文件")
            return

        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除当前列表中所有 PDF 的已有书签吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        cleared = []
        failed = []

        for item in items:
            file_path = item.input_path
            try:
                reader = PdfReader(file_path)
                try:
                    outline = reader.outline
                    if callable(outline):
                        outline = outline()
                except Exception:
                    outline = None

                if not outline:
                    continue

                writer = PdfWriter()
                for page in reader.pages:
                    writer.add_page(page)

                with open(file_path, 'wb') as f:
                    writer.write(f)
                cleared.append(os.path.basename(file_path))

            except Exception as e:
                failed.append(f"{os.path.basename(file_path)}: {str(e)}")

        if cleared:
            self.append_log(f"已清除书签：{', '.join(cleared)}")
        if failed:
            self.append_log(f"❌ 清除失败：{', '.join(failed)}")
        if not cleared and not failed:
            self.append_log("所有文件均无书签，无需清除")

        self._detect_pages_and_bookmarks()

    def _format_outline(self, outline, reader, level=1):
        """递归格式化书签为文本行"""
        lines = []
        if not outline:
            return lines
        for item in outline:
            title = getattr(item, "title", "(无标题)")
            try:
                page_num = reader.get_destination_page_number(item)
                if page_num is not None:
                    lines.append(f"{level} {title} {page_num + 1}")
                else:
                    lines.append(f"{level} {title} -")
            except Exception:
                lines.append(f"{level} {title} -")

            children = getattr(item, "children", None)
            if children:
                if callable(children):
                    try:
                        children = children()
                    except Exception:
                        children = None
                if children:
                    lines.extend(self._format_outline(children, reader, level + 1))
        return lines

    def _detect_pages(self):
        """检测文件的页码数量"""
        from PyPDF2 import PdfReader

        items = self.preview_mgr.items
        if not items:
            QMessageBox.warning(self, "提示", "请先添加PDF文件")
            return

        self.append_log("")
        self.append_log("========== 页码检测 ==========")
        self.append_log(f"共检测 {len(items)} 个文件")
        self.append_log("")

        for i, item in enumerate(items, 1):
            file_path = item.input_path
            base_name = os.path.basename(file_path)
            try:
                reader = PdfReader(file_path)
                total_pages = len(reader.pages)
                self.append_log(f"{i}. {base_name} → {total_pages} 页")
            except Exception as e:
                self.append_log(f"{i}. {base_name} ❌ 读取失败：{str(e)}")

        self.append_log("========== 检测完成 ==========")
        self.append_log("")


    def on_cell_double_clicked(self, item):
        """重写父类方法：支持在“设置”列双击编辑单个文件的书签"""
        row = item.row()
        fi = self.preview_mgr.items[row]
        col = item.column()

        idx = self.feature_box.currentIndex()
        if idx < 0:
            return
        feature_name = self.feature_modules[idx]["name"]

        if feature_name == "PDF 添加书签" and col == self.COL_PREVIEW:
            self._edit_outlines_for_file(row, fi)
            return

        super().on_cell_double_clicked(item)

    def _edit_outlines_for_file(self, row: int, fi):
        """弹出对话框编辑单个文件的自定义书签"""
        idx = self.feature_box.currentIndex()
        outline_panel = self.feature_panels[idx]

        global_text = outline_panel.text_edit.toPlainText()
        default_text = getattr(fi, "custom_outlines", "") if getattr(fi, "custom_outlines", "") else global_text

        dialog = QDialog(self)
        dialog.setWindowTitle(f"编辑书签 - {os.path.basename(fi.input_path)}")
        dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(dialog)

        info = QLabel("修改该书签数据（留空则使用全局规则）")
        info.setStyleSheet("color: #666;")
        layout.addWidget(info)

        text_edit = QTextEdit()
        text_edit.setPlainText(default_text)
        text_edit.setPlaceholderText("1\t第一章\t1\n2\t1.1节\t3")
        layout.addWidget(text_edit)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_clear = QPushButton("清空（使用全局规则）")

        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)

        def clear_and_accept():
            text_edit.clear()
            dialog.accept()

        btn_clear.clicked.connect(clear_and_accept)

        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_ok)
        layout.addLayout(btn_row)

        if dialog.exec() == QDialog.Accepted:
            new_text = text_edit.toPlainText().strip()
            fi.custom_outlines = new_text

            current_row = self.table.currentRow()
            scroll_pos = self.table.verticalScrollBar().value()

            module = self.feature_modules[idx]["module"]
            panel = self.feature_panels[idx]
            settings = module.collect_settings(panel)
            module.prepare_preview(self.preview_mgr.items, settings)

            self.refresh_table()

            if current_row >= 0 and current_row < self.table.rowCount():
                self.table.selectRow(current_row)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(10, lambda: self.table.scrollToItem(
                    self.table.item(current_row, 0),
                    QAbstractItemView.PositionAtCenter
                ))
            else:
                self.table.verticalScrollBar().setValue(scroll_pos)

            if new_text:
                self.append_log(f"已为 {os.path.basename(fi.input_path)} 设置自定义书签")
            else:
                self.append_log(f"已清除 {os.path.basename(fi.input_path)} 的自定义书签，将使用全局规则")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    icon_path = resource_path("assets/logo_pdf.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setFont(QFont("Microsoft YaHei" if sys.platform.startswith("win") else "Arial", 10))

    window = PDFMainWindow()
    window.show()
    sys.exit(app.exec())