# Copyright (C) 2026 张小鱼
# SPDX-License-Identifier: AGPL-3.0-or-later

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QHeaderView, QHBoxLayout, 
    QLabel, QLineEdit, QMenu, QPushButton, QRadioButton, 
    QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QTextEdit, 
    QVBoxLayout, QWidget
)
from .utils import NamingRules, parse_page_range


class NamingRulesDialog(QDialog):
    def __init__(self, rules: NamingRules, parent=None):
        """初始化命名规则编辑器对话框"""
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
        """刷新规则列表表格"""
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
        """规则启用/禁用复选框切换"""
        if row < 0 or row >= len(self.rules.rules):
            return
        rule = self.rules.rules[row]
        rule.enabled = (state == Qt.Checked)
        item = self.rule_table.item(row, 2)
        if item:
            item.setForeground(QColor(0, 0, 0) if rule.enabled else QColor(150, 150, 150))
        self._update_preview()

    def _on_rule_selected(self, _item):
        """选择规则时加载对应配置面板"""
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
        """根据插入位置模式显示/隐藏相应控件"""
        self.pos_container.setVisible(self.rb_position.isChecked())
        self.after_edit.setVisible(self.rb_after.isChecked())
        self.before_edit.setVisible(self.rb_before.isChecked())

    def _on_position_toggled(self):
        """位置单选按钮切换时更新可见性并触发配置变更"""
        self._update_insert_visibility()
        self._on_config_changed()

    def _get_needed_count(self) -> int:
        """计算当前功能需要的文件名数量"""
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
        """更新用户输入计数提示"""
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
        """用户输入文本变更时更新计数并触发配置变更"""
        if self._loading_rule:
            return
        self._update_user_count()
        self._on_config_changed()

    def _on_config_changed(self):
        """配置变更时更新当前规则的参数和预览"""
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
        """更新预览显示"""
        if self.rules.enabled:
            result = self.rules.get_preview("示例文件", 0)
            self.preview_display.setText(f"示例文件 → {result}")
        else:
            self.preview_display.setText("保留原名：示例文件")

    def _add_rule(self, rule_type):
        """添加一条新规则"""
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
        """删除选中的规则"""
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
        """上移选中的规则"""
        if self.selected_index <= 0:
            return
        self.rules.move_rule(self.selected_index, self.selected_index - 1)
        self.selected_index -= 1
        self._refresh_table()
        self.rule_table.selectRow(self.selected_index)
        self._on_rule_selected(self.rule_table.item(self.selected_index, 2))

    def _move_down(self):
        """下移选中的规则"""
        if self.selected_index >= len(self.rules.rules) - 1:
            return
        self.rules.move_rule(self.selected_index, self.selected_index + 1)
        self.selected_index += 1
        self._refresh_table()
        self.rule_table.selectRow(self.selected_index)
        self._on_rule_selected(self.rule_table.item(self.selected_index, 2))

    def _on_accept(self):
        """确定按钮"""
        self.rules.enabled = True
        self.accept()

    def get_rules(self) -> NamingRules:
        """返回编辑后的规则对象"""
        return self.rules