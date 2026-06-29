# """
# CNLMS – Centralized Network Lab Management System
# GUI Console Application

# Wraps the existing server_core.py backend with a professional
# PyQt6 desktop interface for authorized lab administrators.
# """

# from __future__ import annotations

# import os
# import sys
# import socket
# import threading
# import datetime
# import json
# import base64  # Added standard base64 transport support for secure deployments
# from typing import Optional

# # ── PyQt6 imports ────────────────────────────────────────────────────────────
# from PyQt6.QtCore import (
#     Qt, QThread, QObject, pyqtSignal, QTimer, QSize, QSortFilterProxyModel,
#     QAbstractTableModel, QModelIndex, QDateTime,
# )
# from PyQt6.QtGui import (
#     QFont, QColor, QPalette, QIcon, QPixmap, QPainter,
#     QBrush, QAction,
# )
# from PyQt6.QtWidgets import (
#     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
#     QLabel, QPushButton, QTableView, QTabWidget, QTextEdit,
#     QLineEdit, QComboBox, QProgressBar, QFileDialog, QSplitter,
#     QHeaderView, QFrame, QMessageBox, QGroupBox, QGridLayout,
# )

# # ── Protocol helpers (Updated with Auto-Flag & Delimiter Support) ─────────────────────────
# DELIMITER = "<END_OF_MSG>"

# try:
#     from protocol import create_command, create_result, parse_message, create_file_message
# except ImportError:
#     def create_command(cmd: str) -> bytes: 
#         return (json.dumps({"type": "command", "data": cmd}) + DELIMITER).encode('utf-8')
#     def create_result(res: str) -> bytes: 
#         return (json.dumps({"type": "result", "data": res}) + DELIMITER).encode('utf-8')
#     def parse_message(data: bytes) -> dict: 
#         data_str = data.decode('utf-8', errors='ignore')
#         return json.loads(data_str.replace(DELIMITER, "").strip())
    
#     # MODIFIED: Fallback method now accepts and maps silent flags dynamically
#     def create_file_message(name: str, contents: bytes, silent_flag: str = "") -> bytes: 
#         b64_string = base64.b64encode(contents).decode('utf-8')
#         payload = {
#             "type": "file", 
#             "filename": name, 
#             "data": b64_string,
#             "silent_flag": silent_flag  # Injected for zero-touch deployment
#         }
#         return (json.dumps(payload) + DELIMITER).encode('utf-8')


# # ═══════════════════════════════════════════════════════════════════════════════
# #  THEME  –  GitHub Dark palette (Customizable to Light Blue later)
# # ═══════════════════════════════════════════════════════════════════════════════

# THEME = {
#     "bg":       "#0d1117",
#     "panel":    "#161b22",
#     "border":   "#30363d",
#     "primary":  "#1f6feb",
#     "success":  "#238636",
#     "danger":   "#da3633",
#     "warning":  "#d29922",
#     "text":     "#c9d1d9",
#     "subtext":  "#8b949e",
#     "hover":    "#1c2128",
#     "selected": "#1f6feb33",
#     "accent":   "#388bfd",
# }

# STYLESHEET = f"""
# QMainWindow, QWidget {{
#     background-color: {THEME['bg']};
#     color: {THEME['text']};
#     font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
#     font-size: 13px;
# }}
# QFrame#panel {{
#     background-color: {THEME['panel']};
#     border: 1px solid {THEME['border']};
#     border-radius: 6px;
# }}
# QPushButton {{
#     background-color: {THEME['panel']};
#     color: {THEME['text']};
#     border: 1px solid {THEME['border']};
#     border-radius: 6px;
#     padding: 6px 14px;
#     font-weight: 600;
# }}
# QPushButton:hover {{ background-color: {THEME['hover']}; border-color: {THEME['accent']}; }}
# QPushButton#primary {{ background-color: {THEME['primary']}; color: #ffffff; border-color: {THEME['primary']}; }}
# QPushButton#success {{ background-color: {THEME['success']}; color: #ffffff; border-color: {THEME['success']}; }}
# QLineEdit, QComboBox, QTextEdit {{
#     background-color: {THEME['bg']};
#     color: {THEME['text']};
#     border: 1px solid {THEME['border']};
#     border-radius: 6px;
#     padding: 5px 8px;
# }}
# QTableView {{
#     background-color: {THEME['bg']};
#     color: {THEME['text']};
#     border: 1px solid {THEME['border']};
#     gridline-color: {THEME['border']};
# }}
# QHeaderView::section {{
#     background-color: {THEME['panel']};
#     color: {THEME['subtext']};
#     border: none;
#     border-bottom: 1px solid {THEME['border']};
#     padding: 6px 10px;
# }}
# QTabWidget::pane {{ border: 1px solid {THEME['border']}; border-radius: 6px; background-color: {THEME['panel']}; }}
# QTabBar::tab {{
#     background-color: {THEME['bg']};
#     color: {THEME['subtext']};
#     border: 1px solid {THEME['border']};
#     padding: 8px 18px;
#     border-radius: 4px 4px 0 0;
# }}
# QTabBar::tab:selected {{ background-color: {THEME['panel']}; color: {THEME['text']}; border-bottom: 2px solid {THEME['primary']}; }}
# QProgressBar {{ background-color: {THEME['bg']}; border: 1px solid {THEME['border']}; border-radius: 4px; text-align: center; color: {THEME['text']}; }}
# QProgressBar::chunk {{ background-color: {THEME['primary']}; }}
# QGroupBox {{ border: 1px solid {THEME['border']}; border-radius: 6px; margin-top: 14px; padding: 12px 8px; color: {THEME['subtext']}; font-weight: 700; }}
# QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; background-color: {THEME['panel']}; }}
# """

# class DeviceEntry:
#     def __init__(self, sock: socket.socket, addr: tuple[str, int]):
#         self.sock = sock
#         self.ip: str = addr[0]
#         self.port: int = addr[1]
#         self.hostname: str = f"LAB-PC-{self.ip.split('.')[-1]}"
#         self.status: str = "Online"
#         self.last_seen: str = datetime.datetime.now().strftime("%H:%M:%S")

#     def update_last_seen(self) -> None:
#         self.last_seen = datetime.datetime.now().strftime("%H:%M:%S")


# class DeviceTableModel(QAbstractTableModel):
#     HEADERS = ["Hostname", "IP Address", "Port", "Status", "Last Seen"]

#     def __init__(self, parent: Optional[QObject] = None) -> None:
#         super().__init__(parent)
#         self._devices: list[DeviceEntry] = []

#     def add_device(self, entry: DeviceEntry) -> None:
#         row = len(self._devices)
#         self.beginInsertRows(QModelIndex(), row, row)
#         self._devices.append(entry)
#         self.endInsertRows()

#     def remove_device(self, sock: socket.socket) -> None:
#         for i, d in enumerate(self._devices):
#             if d.sock is sock:
#                 self.beginRemoveRows(QModelIndex(), i, i)
#                 self._devices.pop(i)
#                 self.endRemoveRows()
#                 return

#     def device_at(self, row: int) -> Optional[DeviceEntry]:
#         if 0 <= row < len(self._devices):
#             return self._devices[row]
#         return None

#     def device_for_sock(self, sock: socket.socket) -> Optional[DeviceEntry]:
#         for d in self._devices:
#             if d.sock is sock:
#                 return d
#         return None

#     def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self._devices)
#     def columnCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.HEADERS)
#     def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
#         if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self.HEADERS[section]
#         return None

#     def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
#         if not index.isValid(): return None
#         d = self._devices[index.row()]
#         col = index.column()
#         if role == Qt.ItemDataRole.DisplayRole:
#             return [d.hostname, d.ip, str(d.port), d.status, d.last_seen][col]
#         if role == Qt.ItemDataRole.ForegroundRole:
#             if col == 3: return QColor(THEME["success"] if d.status == "Online" else THEME["danger"])
#             return QColor(THEME["text"])
#         return None


# class ServerWorker(QObject):
#     client_connected = pyqtSignal(object, tuple)
#     client_disconnected = pyqtSignal(object)
#     result_received = pyqtSignal(object, str)
#     error_occurred = pyqtSignal(str)

#     HOST = "0.0.0.0"
#     PORT = 5000  # <--- FIXED: 9000 se badal kar 5000 kar diya (Sync with client config)

#     def __init__(self) -> None:
#         super().__init__()
#         self._server_sock: Optional[socket.socket] = None
#         self._running = False

#     def start_server(self) -> None:
#         try:
#             self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             self._server_sock.bind((self.HOST, self.PORT))
#             self._server_sock.listen()
#             self._server_sock.settimeout(1.0)
#             self._running = True
#             print(f"[SERVER ENGINE] Sockets running natively on Port {self.PORT}")

#             while self._running:
#                 try:
#                     client, addr = self._server_sock.accept()
#                     self.client_connected.emit(client, addr)
#                     t = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
#                     t.start()
#                 except socket.timeout:
#                     continue
#                 except OSError:
#                     break
#         except Exception as exc:
#             self.error_occurred.emit(str(exc))

#     def _handle_client(self, client: socket.socket, addr: tuple) -> None:
#         client_buffer = "" 
        
#         while self._running:
#             try:
#                 data = client.recv(65536) 
#                 if not data:
#                     break
                
#                 client_buffer += data.decode('utf-8', errors='ignore')
                
#                 while DELIMITER in client_buffer:
#                     message_str, client_buffer = client_buffer.split(DELIMITER, 1)
                    
#                     try:
#                         msg = json.loads(message_str)
#                         if msg.get("type") == "result":
#                             self.result_received.emit(client, msg.get("data", ""))
#                     except Exception as json_err:
#                         print(f"[-] GUI Server JSON parse error: {json_err}")
#                         continue
                        
#             except Exception:
#                 break
                
#         self.client_disconnected.emit(client)
#         try: client.close()
#         except: pass

#     def stop(self) -> None:
#         self._running = False
#         if self._server_sock:
#             try: self._server_sock.close()
#             except: pass


# # ── Background Thread class with Intelligent Auto-Flag Detection ──
# class FileSenderThread(QThread):
#     progress_signal = pyqtSignal(int)
#     finished_signal = pyqtSignal(str)
#     error_signal = pyqtSignal(str)

#     def __init__(self, sock: socket.socket, path: str):
#         super().__init__()
#         self.sock = sock
#         self.path = path

#     def run(self) -> None:
#         try:
#             filename = os.path.basename(self.path)
#             self.progress_signal.emit(10)
            
#             # --- UPDATED: Intelligent Auto-Flag Detection logic for Lab Attendant Ease ---
#             lower_name = filename.lower()
#             auto_silent_flag = ""
            
#             if lower_name.endswith(".exe"):
#                 auto_silent_flag = "/S"      # Universal standard flag for Nullsoft/Inno installers
#             elif lower_name.endswith(".msi"):
#                 auto_silent_flag = "/qn /norestart"  # Quiet system flag for Microsoft Windows packages
                
#             print(f"[CNLMS Engine] Auto-detected execution signature. Using switch: '{auto_silent_flag}'")
#             self.progress_signal.emit(20)
            
#             # 1. Heavy file data ko step-by-step memory buffer par load karna
#             with open(self.path, "rb") as f:
#                 filedata = f.read()
#             self.progress_signal.emit(40)
            
#             # 2. Structural packaging logic convert karna (Passing the dynamic silent flag)
#             try:
#                 msg_payload = create_file_message(filename, filedata, silent_flag=auto_silent_flag)
#             except TypeError:
#                 b64_string = base64.b64encode(filedata).decode('utf-8')
#                 payload = {"type": "file", "filename": filename, "data": b64_string, "silent_flag": auto_silent_flag}
#                 msg_payload = (json.dumps(payload) + DELIMITER).encode('utf-8')
                
#             self.progress_signal.emit(60)
            
#             # 3. Payload size nikal kar 1MB Chunks mein distribution stream chalana
#             total_payload_len = len(msg_payload)
#             bytes_sent = 0
#             chunk_size = 1024 * 1024  # 1 MegaByte Buffer Block
            
#             while bytes_sent < total_payload_len:
#                 chunk = msg_payload[bytes_sent : bytes_sent + chunk_size]
#                 self.sock.sendall(chunk)
#                 bytes_sent += len(chunk)
                
#                 current_percent = int((bytes_sent / total_payload_len) * 30) + 70
#                 if current_percent < 100:
#                     self.progress_signal.emit(current_percent)
            
#             self.progress_signal.emit(100)
#             self.finished_signal.emit(filename)
#         except Exception as e:
#             self.error_signal.emit(str(e))


# def make_panel() -> QFrame:
#     f = QFrame()
#     f.setObjectName("panel")
#     return f

# def make_label(text: str, style: str = "normal") -> QLabel:
#     lbl = QLabel(text)
#     if style == "heading": lbl.setStyleSheet(f"color:{THEME['text']}; font-size:14px; font-weight:700;")
#     elif style == "subtext": lbl.setStyleSheet(f"color:{THEME['subtext']}; font-size:11px;")
#     return lbl

# class StatCard(QFrame):
#     def __init__(self, title: str, value: str = "0", color: str = THEME["accent"]) -> None:
#         super().__init__()
#         self.setObjectName("panel")
#         layout = QVBoxLayout(self)
#         self._title_lbl = QLabel(title.upper())
#         self._title_lbl.setStyleSheet(f"color:{THEME['subtext']}; font-size:10px; font-weight:700;")
#         self._value_lbl = QLabel(value)
#         self._value_lbl.setStyleSheet(f"color:{color}; font-size:28px; font-weight:700;")
#         layout.addWidget(self._title_lbl)
#         layout.addWidget(self._value_lbl)

#     def set_value(self, v: str) -> None: self._value_lbl.setText(v)


# class DevicePanel(QFrame):
#     device_selected = pyqtSignal(object)

#     def __init__(self, model: DeviceTableModel, parent=None) -> None:
#         super().__init__(parent)
#         self.setObjectName("panel")
#         self.setMinimumWidth(320)
#         self._model = model

#         layout = QVBoxLayout(self)
#         hdr = QHBoxLayout()
#         hdr.addWidget(make_label("Connected Devices", "heading"))
#         self._count_badge = QLabel("0")
#         self._count_badge.setStyleSheet(f"background:{THEME['primary']}; color:#fff; border-radius:10px; padding:2px 8px; font-weight:700;")
#         hdr.addWidget(self._count_badge)
#         layout.addLayout(hdr)

#         self._table = QTableView()
#         self._table.setModel(self._model)
#         self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
#         self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
#         self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
#         self._table.verticalHeader().setVisible(False)
#         self._table.horizontalHeader().setStretchLastSection(True)
#         self._table.selectionModel().selectionChanged.connect(self._on_selection)
#         layout.addWidget(self._table)

#         # FIXED: Label ko 5000 show karne ke liye update kar diya
#         self._status_lbl = make_label("Server listening on :5000", "subtext")
#         layout.addWidget(self._status_lbl)

#     def refresh_badge(self) -> None: self._count_badge.setText(str(self._model.rowCount()))

#     def _on_selection(self) -> None:
#         rows = self._table.selectionModel().selectedRows()
#         if rows:
#             entry = self._model.device_at(rows[0].row())
#             if entry: self.device_selected.emit(entry)


# ADMIN_TASKS: dict[str, str] = {
#     "Get Hostname":           "hostname",
#     "Get IP Configuration":   "ipconfig /all" if sys.platform == "win32" else "ip a",
#     "Get OS Information":     "winver" if sys.platform == "win32" else "uname -a",
#     "Get Disk Usage":         "wmic logicaldisk get caption,freespace,size" if sys.platform == "win32" else "df -h",
#     "List Running Services":  "sc query state= running" if sys.platform == "win32" else "systemctl list-units --type=service --state=running",
# }

# class ManagementTab(QWidget):
#     command_requested = pyqtSignal(str)

#     def __init__(self, parent=None) -> None:
#         super().__init__(parent)
#         self._current_device: Optional[DeviceEntry] = None
#         self._build_ui()

#     def _build_ui(self) -> None:
#         root = QVBoxLayout(self)
#         info_group = QGroupBox("Selected Device")
#         ig_layout = QGridLayout(info_group)
#         labels = ["Hostname:", "IP Address:", "Port:", "Status:"]
#         self._info_values: list[QLabel] = []
#         for i, lbl in enumerate(labels):
#             ig_layout.addWidget(make_label(lbl, "subtext"), i, 0)
#             v = make_label("—")
#             ig_layout.addWidget(v, i, 1)
#             self._info_values.append(v)
#         root.addWidget(info_group)

#         task_group = QGroupBox("Administrative Tasks")
#         tg_layout = QVBoxLayout(task_group)
#         self._task_combo = QComboBox()
#         self._task_combo.addItems(list(ADMIN_TASKS.keys()))
#         tg_layout.addWidget(self._task_combo)
#         run_btn = QPushButton("▶  Execute Task")
#         run_btn.setObjectName("primary")
#         run_btn.clicked.connect(self._run_task)
#         tg_layout.addWidget(run_btn)
#         root.addWidget(task_group)

#         custom_group = QGroupBox("Custom Command")
#         cg_layout = QHBoxLayout(custom_group)
#         self._cmd_input = QLineEdit()
#         self._cmd_input.setPlaceholderText("Enter shell command…")
#         self._cmd_input.returnPressed.connect(self._run_custom)
#         cg_layout.addWidget(self._cmd_input)
#         send_btn = QPushButton("Send")
#         send_btn.setObjectName("success")
#         send_btn.clicked.connect(self._run_custom)
#         cg_layout.addWidget(send_btn)
#         root.addWidget(custom_group)

#         out_group = QGroupBox("Output")
#         og_layout = QVBoxLayout(out_group)
#         self._output = QTextEdit()
#         self._output.setReadOnly(True)
#         og_layout.addWidget(self._output)
#         clear_btn = QPushButton("Clear Output")
#         clear_btn.clicked.connect(self._output.clear)
#         og_layout.addWidget(clear_btn)
#         root.addWidget(out_group, stretch=1)

#     def set_device(self, device: Optional[DeviceEntry]) -> None:
#         self._current_device = device
#         if device:
#             vals = [device.hostname, device.ip, str(device.port), device.status]
#             colors = [THEME["text"], THEME["text"], THEME["subtext"], THEME["success"]]
#             for lbl, val, col in zip(self._info_values, vals, colors):
#                 lbl.setText(val)
#                 lbl.setStyleSheet(f"color:{col};")
#         else:
#             for lbl in self._info_values: lbl.setText("—")

#     def append_result(self, text: str) -> None:
#         self._output.append(f'<span style="color:{THEME["text"]}">{text}</span>')

#     def _run_task(self) -> None:
#         if not self._current_device: return
#         self.command_requested.emit(ADMIN_TASKS.get(self._task_combo.currentText(), ""))

#     def _run_custom(self) -> None:
#         cmd = self._cmd_input.text().strip()
#         if cmd and self._current_device:
#             self.command_requested.emit(cmd)
#             self._cmd_input.clear()


# class FileTab(QWidget):
#     file_send_requested = pyqtSignal(str)

#     def __init__(self, parent=None) -> None:
#         super().__init__(parent)
#         self._build_ui()

#     def _build_ui(self) -> None:
#         root = QVBoxLayout(self)
#         file_group = QGroupBox("File Selection")
#         fg_layout = QVBoxLayout(file_group)
#         path_row = QHBoxLayout()
#         self._file_path = QLineEdit()
#         self._file_path.setReadOnly(True)
#         path_row.addWidget(self._file_path)
#         browse_btn = QPushButton("Browse…")
#         browse_btn.clicked.connect(self._browse)
#         path_row.addWidget(browse_btn)
#         fg_layout.addLayout(path_row)
#         root.addWidget(file_group)

#         deploy_group = QGroupBox("Deployment Config (Auto-Detect Flags Mode)")
#         dpl_layout = QVBoxLayout(deploy_group)
#         self._deploy_btn = QPushButton("🚀  Deploy File Silently")
#         self._deploy_btn.setObjectName("primary")
#         self._deploy_btn.clicked.connect(self._deploy)
#         dpl_layout.addWidget(self._deploy_btn)
#         self._progress = QProgressBar()
#         dpl_layout.addWidget(self._progress)
#         root.addWidget(deploy_group)
#         root.addStretch()

#     def _browse(self) -> None:
#         path, _ = QFileDialog.getOpenFileName(self, "Select File")
#         if path: self._file_path.setText(path)

#     def _deploy(self) -> None:
#         path = self._file_path.text()
#         if path: self.file_send_requested.emit(path)

#     def update_progress(self, val: int) -> None: self._progress.setValue(val)


# class DashboardTab(QWidget):
#     def __init__(self, parent=None) -> None:
#         super().__init__(parent)
#         layout = QGridLayout(self)
#         self.card1 = StatCard("Active Lab Terminals", "0", THEME["success"])
#         self.card2 = StatCard("Actions Executed", "0", THEME["accent"])
#         layout.addWidget(self.card1, 0, 0)
#         layout.addWidget(self.card2, 0, 1)
#         layout.setRowStretch(1, 1)


# class MainWindow(QMainWindow):
#     def __init__(self) -> None:
#         super().__init__()
#         self.setWindowTitle("CNLMS – System Core Console")
#         self.resize(1100, 700)
#         self.setStyleSheet(STYLESHEET)

#         self.device_model = DeviceTableModel()
#         self._total_actions = 0
#         self.file_sender: Optional[FileSenderThread] = None

#         splitter = QSplitter(Qt.Orientation.Horizontal)
#         self.device_panel = DevicePanel(self.device_model)
#         splitter.addWidget(self.device_panel)

#         self.tabs = QTabWidget()
#         self.dash_tab = DashboardTab()
#         self.mgmt_tab = ManagementTab()
#         self.file_tab = FileTab()

#         self.tabs.addTab(self.dash_tab, "Dashboard")
#         self.tabs.addTab(self.mgmt_tab, "Terminal Management")
#         self.tabs.addTab(self.file_tab, "Deploy Configuration")
#         splitter.addWidget(self.tabs)
#         splitter.setSizes([350, 750])
#         self.setCentralWidget(splitter)

#         # Signals Mapping
#         self.device_panel.device_selected.connect(self.mgmt_tab.set_device)
#         self.mgmt_tab.command_requested.connect(self._execute_command)
#         self.file_tab.file_send_requested.connect(self._deploy_file)

#         # Thread Setup for Server Listener
#         self.server_thread = QThread()
#         self.server_worker = ServerWorker()
#         self.server_worker.moveToThread(self.server_thread)
#         self.server_thread.started.connect(self.server_worker.start_server)

#         self.server_worker.client_connected.connect(self._on_client_connected)
#         self.server_worker.client_disconnected.connect(self._on_client_disconnected)
#         self.server_worker.result_received.connect(self._on_result_received)

#         self.server_thread.start()

#     def _on_client_connected(self, sock, addr):
#         dev = DeviceEntry(sock, addr)
#         self.device_model.add_device(dev)
#         self.device_panel.refresh_badge()
#         self.dash_tab.card1.set_value(str(self.device_model.rowCount()))

#     def _on_client_disconnected(self, sock):
#         self.device_model.remove_device(sock)
#         self.device_panel.refresh_badge()
#         self.dash_tab.card1.set_value(str(self.device_model.rowCount()))
#         if self.mgmt_tab._current_device and self.mgmt_tab._current_device.sock is sock:
#             self.mgmt_tab.set_device(None)

#     def _execute_command(self, cmd: str) -> None:
#         dev = self.mgmt_tab._current_device
#         if not dev:
#             QMessageBox.warning(self, "Selection Required", "Please select an active device from the left panel.")
#             return

#         self._total_actions += 1
#         self.dash_tab.card2.set_value(str(self._total_actions))
        
#         try:
#             dev.sock.sendall(create_command(cmd))
#             self.mgmt_tab.append_result(f"<b>[Sent]</b> Command: {cmd}")
#         except Exception as e:
#             QMessageBox.critical(self, "Transmission Error", f"Failed to send command: {e}")

#     def _deploy_file(self, path: str) -> None:
#         """
#         Multi-Threaded Secure File Deployment with Automatic Lab Attendant Flag Bypass.
#         """
#         dev = self.mgmt_tab._current_device
#         if not dev:
#             QMessageBox.warning(self, "Selection Required", "Please select an active device from the left panel.")
#             return

#         filename = os.path.basename(path)
#         self.mgmt_tab.append_result(f"<b>[System]</b> Scanning structure & launching async silent stream for: {filename}...")
        
#         self.file_tab._deploy_btn.setEnabled(False)
        
#         self.file_sender = FileSenderThread(dev.sock, path)
#         self.file_sender.progress_signal.connect(self.file_tab.update_progress)
        
#         def on_success(fname: str):
#             self._total_actions += 1
#             self.dash_tab.card2.set_value(str(self._total_actions))
#             self.mgmt_tab.append_result(f"<b>[Sent]</b> Zero-Touch deployment completed successfully for: {fname}")
#             QMessageBox.information(self, "Success", f"File '{fname}' deployed silently in background thread without user prompts!")
#             self.file_tab.update_progress(0)
#             self.file_tab._deploy_btn.setEnabled(True)
            
#         def on_error(err_msg: str):
#             self.file_tab.update_progress(0)
#             self.mgmt_tab.append_result(f"<b>[Error]</b> Zero-Touch deployment failed: {err_msg}")
#             QMessageBox.critical(self, "Deployment Error", f"Failed to transport file payload: {err_msg}")
#             self.file_tab._deploy_btn.setEnabled(True)

#         self.file_sender.finished_signal.connect(on_success)
#         self.file_sender.error_signal.connect(on_error)
#         self.file_sender.start()

#     def _on_result_received(self, sock, output):
#         dev = self.device_model.device_for_sock(sock)
#         if dev:
#             dev.update_last_seen()
#             self.device_model.dataChanged.emit(QModelIndex(), QModelIndex())
        
#         clean_output = output.replace("\n", "<br>")
#         self.mgmt_tab.append_result(f"<b>[Response]</b>:<br>{clean_output}<br>")

#     def closeEvent(self, event) -> None:
#         self.server_worker.stop()
#         self.server_thread.quit()
#         self.server_thread.wait()
#         if self.file_sender and self.file_sender.isRunning():
#             self.file_sender.quit()
#             self.file_sender.wait()
#         super().closeEvent(event)


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = MainWindow()
#     window.show()
#     sys.exit(app.exec())





"""
CNLMS – Centralized Network Lab Management System
GUI Console Application

Wraps the existing server_core.py backend with a professional
PyQt6 desktop interface for authorized lab administrators.
Optimized for high-contrast light environment documentation printing.
"""

from __future__ import annotations

import os
import sys
import socket
import threading
import datetime
import json
import base64  # Added standard base64 transport support for secure deployments
from typing import Optional

# ── PyQt6 imports ────────────────────────────────────────────────────────────
from PyQt6.QtCore import (
    Qt, QThread, QObject, pyqtSignal, QTimer, QSize, QSortFilterProxyModel,
    QAbstractTableModel, QModelIndex, QDateTime,
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QIcon, QPixmap, QPainter,
    QBrush, QAction,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableView, QTabWidget, QTextEdit,
    QLineEdit, QComboBox, QProgressBar, QFileDialog, QSplitter,
    QHeaderView, QFrame, QMessageBox, QGroupBox, QGridLayout,
)

# ── Protocol helpers (Updated with Auto-Flag & Delimiter Support) ─────────────────────────
DELIMITER = "<END_OF_MSG>"

try:
    from protocol import create_command, create_result, parse_message, create_file_message
except ImportError:
    def create_command(cmd: str) -> bytes: 
        return (json.dumps({"type": "command", "data": cmd}) + DELIMITER).encode('utf-8')
    def create_result(res: str) -> bytes: 
        return (json.dumps({"type": "result", "data": res}) + DELIMITER).encode('utf-8')
    def parse_message(data: bytes) -> dict: 
        data_str = data.decode('utf-8', errors='ignore')
        return json.loads(data_str.replace(DELIMITER, "").strip())
    
    # MODIFIED: Fallback method now accepts and maps silent flags dynamically
    def create_file_message(name: str, contents: bytes, silent_flag: str = "") -> bytes: 
        b64_string = base64.b64encode(contents).decode('utf-8')
        payload = {
            "type": "file", 
            "filename": name, 
            "data": b64_string,
            "silent_flag": silent_flag  # Injected for zero-touch deployment
        }
        return (json.dumps(payload) + DELIMITER).encode('utf-8')


# ═══════════════════════════════════════════════════════════════════════════════
#  THEME  –  High Contrast Light Blue Palette (Optimized for Thesis Printing)
# ═══════════════════════════════════════════════════════════════════════════════

THEME = {
    "bg":       "#FFFFFF",  # Pure white background for zero toner/ink usage
    "panel":    "#F8F9FA",  # Very light gray for clean structural boxes
    "border":   "#BCC1C8",  # Medium gray borders for razor sharp print line contrast
    "primary":  "#0D6EFD",  # Standard Royal Blue for actions
    "success":  "#198754",  # Darker corporate green for visible status indication
    "danger":   "#DC3545",  # Highly legible high-contrast red
    "warning":  "#997404",  # Darkened warning gold for print text clarity
    "text":     "#111111",  # Dark Charcoal (almost pure black) for ultimate readability
    "subtext":  "#495057",  # Slate gray for secondary metadata labels
    "hover":    "#E9ECEF",  # Soft selection hover layout
    "selected": "#0D6EFD1A", # Soft blue accent transparency highlight
    "accent":   "#0A58CA",  # Safe dark cobalt blue
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {THEME['bg']};
    color: {THEME['text']};
    font-family: 'Segoe UI', 'Arial', 'Helvetica', sans-serif;
    font-size: 13px;
}}
QFrame#panel {{
    background-color: {THEME['panel']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
}}
QPushButton {{
    background-color: {THEME['panel']};
    color: {THEME['text']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {THEME['hover']}; border-color: {THEME['accent']}; }}
QPushButton#primary {{ background-color: {THEME['primary']}; color: #ffffff; border-color: {THEME['primary']}; }}
QPushButton#success {{ background-color: {THEME['success']}; color: #ffffff; border-color: {THEME['success']}; }}
QLineEdit, QComboBox, QTextEdit {{
    background-color: {THEME['bg']};
    color: {THEME['text']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 5px 8px;
}}
QTableView {{
    background-color: {THEME['bg']};
    color: {THEME['text']};
    border: 1px solid {THEME['border']};
    gridline-color: {THEME['border']};
    selection-background-color: {THEME['hover']};
    selection-color: {THEME['text']};
}}
QHeaderView::section {{
    background-color: {THEME['panel']};
    color: {THEME['text']};
    border: 1px solid {THEME['border']};
    padding: 6px 10px;
    font-weight: bold;
}}
QTabWidget::pane {{ border: 1px solid {THEME['border']}; border-radius: 6px; background-color: {THEME['panel']}; }}
QTabBar::tab {{
    background-color: {THEME['panel']};
    color: {THEME['subtext']};
    border: 1px solid {THEME['border']};
    padding: 8px 18px;
    border-radius: 4px 4px 0 0;
}}
QTabBar::tab:selected {{ background-color: {THEME['bg']}; color: {THEME['primary']}; border-bottom: 2px solid {THEME['primary']}; font-weight: bold; }}
QProgressBar {{ background-color: {THEME['panel']}; border: 1px solid {THEME['border']}; border-radius: 4px; text-align: center; color: {THEME['text']}; font-weight: bold; }}
QProgressBar::chunk {{ background-color: {THEME['primary']}; }}
QGroupBox {{ border: 1px solid {THEME['border']}; border-radius: 6px; margin-top: 14px; padding: 12px 8px; color: {THEME['text']}; font-weight: 700; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; background-color: {THEME['panel']}; }}
"""

class DeviceEntry:
    def __init__(self, sock: socket.socket, addr: tuple[str, int]):
        self.sock = sock
        self.ip: str = addr[0]
        self.port: int = addr[1]
        self.hostname: str = f"LAB-PC-{self.ip.split('.')[-1]}"
        self.status: str = "Online"
        self.last_seen: str = datetime.datetime.now().strftime("%H:%M:%S")

    def update_last_seen(self) -> None:
        self.last_seen = datetime.datetime.now().strftime("%H:%M:%S")


class DeviceTableModel(QAbstractTableModel):
    HEADERS = ["Hostname", "IP Address", "Port", "Status", "Last Seen"]

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._devices: list[DeviceEntry] = []

    def add_device(self, entry: DeviceEntry) -> None:
        row = len(self._devices)
        self.beginInsertRows(QModelIndex(), row, row)
        self._devices.append(entry)
        self.endInsertRows()

    def remove_device(self, sock: socket.socket) -> None:
        for i, d in enumerate(self._devices):
            if d.sock is sock:
                self.beginRemoveRows(QModelIndex(), i, i)
                self._devices.pop(i)
                self.endRemoveRows()
                return

    def device_at(self, row: int) -> Optional[DeviceEntry]:
        if 0 <= row < len(self._devices):
            return self._devices[row]
        return None

    def device_for_sock(self, sock: socket.socket) -> Optional[DeviceEntry]:
        for d in self._devices:
            if d.sock is sock:
                return d
        return None

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self._devices)
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int: return len(self.HEADERS)
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal: return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        d = self._devices[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return [d.hostname, d.ip, str(d.port), d.status, d.last_seen][col]
        if role == Qt.ItemDataRole.ForegroundRole:
            if col == 3: return QColor(THEME["success"] if d.status == "Online" else THEME["danger"])
            return QColor(THEME["text"])
        return None


class ServerWorker(QObject):
    client_connected = pyqtSignal(object, tuple)
    client_disconnected = pyqtSignal(object)
    result_received = pyqtSignal(object, str)
    error_occurred = pyqtSignal(str)

    HOST = "0.0.0.0"
    PORT = 5000  

    def __init__(self) -> None:
        super().__init__()
        self._server_sock: Optional[socket.socket] = None
        self._running = False

    def start_server(self) -> None:
        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((self.HOST, self.PORT))
            self._server_sock.listen()
            self._server_sock.settimeout(1.0)
            self._running = True
            print(f"[SERVER ENGINE] Sockets running natively on Port {self.PORT}")

            while self._running:
                try:
                    client, addr = self._server_sock.accept()
                    self.client_connected.emit(client, addr)
                    t = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
                    t.start()
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as exc:
            self.error_occurred.emit(str(exc))

    def _handle_client(self, client: socket.socket, addr: tuple) -> None:
        client_buffer = "" 
        
        while self._running:
            try:
                data = client.recv(65536) 
                if not data:
                    break
                
                client_buffer += data.decode('utf-8', errors='ignore')
                
                while DELIMITER in client_buffer:
                    message_str, client_buffer = client_buffer.split(DELIMITER, 1)
                    
                    try:
                        msg = json.loads(message_str)
                        if msg.get("type") == "result":
                            self.result_received.emit(client, msg.get("data", ""))
                    except Exception as json_err:
                        print(f"[-] GUI Server JSON parse error: {json_err}")
                        continue
                        
            except Exception:
                break
                
        self.client_disconnected.emit(client)
        try: client.close()
        except: pass

    def stop(self) -> None:
        self._running = False
        if self._server_sock:
            try: self._server_sock.close()
            except: pass


class FileSenderThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, sock: socket.socket, path: str):
        super().__init__()
        self.sock = sock
        self.path = path

    def run(self) -> None:
        try:
            filename = os.path.basename(self.path)
            self.progress_signal.emit(10)
            
            lower_name = filename.lower()
            auto_silent_flag = ""
            
            if lower_name.endswith(".exe"):
                auto_silent_flag = "/S"      
            elif lower_name.endswith(".msi"):
                auto_silent_flag = "/qn /norestart"  
                
            print(f"[CNLMS Engine] Auto-detected execution signature. Using switch: '{auto_silent_flag}'")
            self.progress_signal.emit(20)
            
            with open(self.path, "rb") as f:
                filedata = f.read()
            self.progress_signal.emit(40)
            
            try:
                msg_payload = create_file_message(filename, filedata, silent_flag=auto_silent_flag)
            except TypeError:
                b64_string = base64.b64encode(filedata).decode('utf-8')
                payload = {"type": "file", "filename": filename, "data": b64_string, "silent_flag": auto_silent_flag}
                msg_payload = (json.dumps(payload) + DELIMITER).encode('utf-8')
                
            self.progress_signal.emit(60)
            
            total_payload_len = len(msg_payload)
            bytes_sent = 0
            chunk_size = 1024 * 1024  
            
            while bytes_sent < total_payload_len:
                chunk = msg_payload[bytes_sent : bytes_sent + chunk_size]
                self.sock.sendall(chunk)
                bytes_sent += len(chunk)
                
                current_percent = int((bytes_sent / total_payload_len) * 30) + 70
                if current_percent < 100:
                    self.progress_signal.emit(current_percent)
            
            self.progress_signal.emit(100)
            self.finished_signal.emit(filename)
        except Exception as e:
            self.error_signal.emit(str(e))


def make_panel() -> QFrame:
    f = QFrame()
    f.setObjectName("panel")
    return f

def make_label(text: str, style: str = "normal") -> QLabel:
    lbl = QLabel(text)
    if style == "heading": lbl.setStyleSheet(f"color:{THEME['text']}; font-size:14px; font-weight:700;")
    elif style == "subtext": lbl.setStyleSheet(f"color:{THEME['subtext']}; font-size:11px;")
    return lbl

class StatCard(QFrame):
    def __init__(self, title: str, value: str = "0", color: str = THEME["accent"]) -> None:
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        self._title_lbl = QLabel(title.upper())
        self._title_lbl.setStyleSheet(f"color:{THEME['subtext']}; font-size:10px; font-weight:700;")
        self._value_lbl = QLabel(value)
        self._value_lbl.setStyleSheet(f"color:{color}; font-size:28px; font-weight:700;")
        layout.addWidget(self._title_lbl)
        layout.addWidget(self._value_lbl)

    def set_value(self, v: str) -> None: self._value_lbl.setText(v)


class DevicePanel(QFrame):
    device_selected = pyqtSignal(object)

    def __init__(self, model: DeviceTableModel, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMinimumWidth(320)
        self._model = model

        layout = QVBoxLayout(self)
        hdr = QHBoxLayout()
        hdr.addWidget(make_label("Connected Devices", "heading"))
        self._count_badge = QLabel("0")
        self._count_badge.setStyleSheet(f"background:{THEME['primary']}; color:#fff; border-radius:10px; padding:2px 8px; font-weight:700;")
        hdr.addWidget(self._count_badge)
        layout.addLayout(hdr)

        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.selectionModel().selectionChanged.connect(self._on_selection)
        layout.addWidget(self._table)

        self._status_lbl = make_label("Server listening on :5000", "subtext")
        layout.addWidget(self._status_lbl)

    def refresh_badge(self) -> None: self._count_badge.setText(str(self._model.rowCount()))

    def _on_selection(self) -> None:
        rows = self._table.selectionModel().selectedRows()
        if rows:
            entry = self._model.device_at(rows[0].row())
            if entry: self.device_selected.emit(entry)


ADMIN_TASKS: dict[str, str] = {
    "Get Hostname":           "hostname",
    "Get IP Configuration":   "ipconfig /all" if sys.platform == "win32" else "ip a",
    "Get OS Information":     "winver" if sys.platform == "win32" else "uname -a",
    "Get Disk Usage":         "wmic logicaldisk get caption,freespace,size" if sys.platform == "win32" else "df -h",
    "List Running Services":  "sc query state= running" if sys.platform == "win32" else "systemctl list-units --type=service --state=running",
}

class ManagementTab(QWidget):
    command_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_device: Optional[DeviceEntry] = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        info_group = QGroupBox("Selected Device")
        info_group.setStyleSheet(f"color: {THEME['text']};")
        ig_layout = QGridLayout(info_group)
        labels = ["Hostname:", "IP Address:", "Port:", "Status:"]
        self._info_values: list[QLabel] = []
        for i, lbl in enumerate(labels):
            ig_layout.addWidget(make_label(lbl, "subtext"), i, 0)
            v = make_label("—")
            ig_layout.addWidget(v, i, 1)
            self._info_values.append(v)
        root.addWidget(info_group)

        task_group = QGroupBox("Administrative Tasks")
        tg_layout = QVBoxLayout(task_group)
        self._task_combo = QComboBox()
        self._task_combo.addItems(list(ADMIN_TASKS.keys()))
        tg_layout.addWidget(self._task_combo)
        run_btn = QPushButton("▶  Execute Task")
        run_btn.setObjectName("primary")
        run_btn.clicked.connect(self._run_task)
        tg_layout.addWidget(run_btn)
        root.addWidget(task_group)

        custom_group = QGroupBox("Custom Command")
        cg_layout = QHBoxLayout(custom_group)
        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("Enter shell command…")
        self._cmd_input.returnPressed.connect(self._run_custom)
        cg_layout.addWidget(self._cmd_input)
        send_btn = QPushButton("Send")
        send_btn.setObjectName("success")
        send_btn.clicked.connect(self._run_custom)
        cg_layout.addWidget(send_btn)
        root.addWidget(custom_group)

        out_group = QGroupBox("Output Terminal")
        og_layout = QVBoxLayout(out_group)
        self._output = QTextEdit()
        self._output.setReadOnly(True)
        # Force dynamic background on output for clear monochrome contrast printing
        self._output.setStyleSheet(f"background-color: {THEME['bg']}; color: #000000; font-family: 'Consolas', monospace;")
        og_layout.addWidget(self._output)
        clear_btn = QPushButton("Clear Output")
        clear_btn.clicked.connect(self._output.clear)
        og_layout.addWidget(clear_btn)
        root.addWidget(out_group, stretch=1)

    def set_device(self, device: Optional[DeviceEntry]) -> None:
        self._current_device = device
        if device:
            vals = [device.hostname, device.ip, str(device.port), device.status]
            colors = [THEME["text"], THEME["text"], THEME["subtext"], THEME["success"]]
            for lbl, val, col in zip(self._info_values, vals, colors):
                lbl.setText(val)
                lbl.setStyleSheet(f"color:{col}; font-weight: bold;")
        else:
            for lbl in self._info_values: lbl.setText("—")

    def append_result(self, text: str) -> None:
        # Styled cleanly using dark charcoal spans for crisp line outputs
        self._output.append(f'<span style="color:#000000;">{text}</span>')

    def _run_task(self) -> None:
        if not self._current_device: return
        self.command_requested.emit(ADMIN_TASKS.get(self._task_combo.currentText(), ""))

    def _run_custom(self) -> None:
        cmd = self._cmd_input.text().strip()
        if cmd and self._current_device:
            self.command_requested.emit(cmd)
            self._cmd_input.clear()


class FileTab(QWidget):
    file_send_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        file_group = QGroupBox("File Selection")
        fg_layout = QVBoxLayout(file_group)
        path_row = QHBoxLayout()
        self._file_path = QLineEdit()
        self._file_path.setReadOnly(True)
        path_row.addWidget(self._file_path)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        fg_layout.addLayout(path_row)
        root.addWidget(file_group)

        deploy_group = QGroupBox("Deployment Config (Auto-Detect Flags Mode)")
        dpl_layout = QVBoxLayout(deploy_group)
        self._deploy_btn = QPushButton("🚀  Deploy File Silently")
        self._deploy_btn.setObjectName("primary")
        self._deploy_btn.clicked.connect(self._deploy)
        dpl_layout.addWidget(self._deploy_btn)
        self._progress = QProgressBar()
        dpl_layout.addWidget(self._progress)
        root.addWidget(deploy_group)
        root.addStretch()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if path: self._file_path.setText(path)

    def _deploy(self) -> None:
        path = self._file_path.text()
        if path: self.file_send_requested.emit(path)

    def update_progress(self, val: int) -> None: self._progress.setValue(val)


class DashboardTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QGridLayout(self)
        self.card1 = StatCard("Active Lab Terminals", "0", THEME["success"])
        self.card2 = StatCard("Actions Executed", "0", THEME["accent"])
        layout.addWidget(self.card1, 0, 0)
        layout.addWidget(self.card2, 0, 1)
        layout.setRowStretch(1, 1)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CNLMS – System Core Console")
        self.resize(1100, 700)
        self.setStyleSheet(STYLESHEET)

        self.device_model = DeviceTableModel()
        self._total_actions = 0
        self.file_sender: Optional[FileSenderThread] = None

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.device_panel = DevicePanel(self.device_model)
        splitter.addWidget(self.device_panel)

        self.tabs = QTabWidget()
        self.dash_tab = DashboardTab()
        self.mgmt_tab = ManagementTab()
        self.file_tab = FileTab()

        self.tabs.addTab(self.dash_tab, "Dashboard")
        self.tabs.addTab(self.mgmt_tab, "Terminal Management")
        self.tabs.addTab(self.file_tab, "Deploy Configuration")
        splitter.addWidget(self.tabs)
        splitter.setSizes([350, 750])
        self.setCentralWidget(splitter)

        # Signals Mapping
        self.device_panel.device_selected.connect(self.mgmt_tab.set_device)
        self.mgmt_tab.command_requested.connect(self._execute_command)
        self.file_tab.file_send_requested.connect(self._deploy_file)

        # Thread Setup for Server Listener
        self.server_thread = QThread()
        self.server_worker = ServerWorker()
        self.server_worker.moveToThread(self.server_thread)
        self.server_thread.started.connect(self.server_worker.start_server)

        self.server_worker.client_connected.connect(self._on_client_connected)
        self.server_worker.client_disconnected.connect(self._on_client_disconnected)
        self.server_worker.result_received.connect(self._on_result_received)

        self.server_thread.start()

    def _on_client_connected(self, sock, addr):
        dev = DeviceEntry(sock, addr)
        self.device_model.add_device(dev)
        self.device_panel.refresh_badge()
        self.dash_tab.card1.set_value(str(self.device_model.rowCount()))

    def _on_client_disconnected(self, sock):
        self.device_model.remove_device(sock)
        self.device_panel.refresh_badge()
        self.dash_tab.card1.set_value(str(self.device_model.rowCount()))
        if self.mgmt_tab._current_device and self.mgmt_tab._current_device.sock is sock:
            self.mgmt_tab.set_device(None)

    def _execute_command(self, cmd: str) -> None:
        dev = self.mgmt_tab._current_device
        if not dev:
            QMessageBox.warning(self, "Selection Required", "Please select an active device from the left panel.")
            return

        self._total_actions += 1
        self.dash_tab.card2.set_value(str(self._total_actions))
        
        try:
            dev.sock.sendall(create_command(cmd))
            self.mgmt_tab.append_result(f"<b>[Sent]</b> Command: {cmd}")
        except Exception as e:
            QMessageBox.critical(self, "Transmission Error", f"Failed to send command: {e}")

    def _deploy_file(self, path: str) -> None:
        """
        Multi-Threaded Secure File Deployment with Automatic Lab Attendant Flag Bypass.
        """
        dev = self.mgmt_tab._current_device
        if not dev:
            QMessageBox.warning(self, "Selection Required", "Please select an active device from the left panel.")
            return

        filename = os.path.basename(path)
        self.mgmt_tab.append_result(f"<b>[System]</b> Scanning structure & launching async silent stream for: {filename}...")
        
        self.file_tab._deploy_btn.setEnabled(False)
        
        self.file_sender = FileSenderThread(dev.sock, path)
        self.file_sender.progress_signal.connect(self.file_tab.update_progress)
        
        def on_success(fname: str):
            self._total_actions += 1
            self.dash_tab.card2.set_value(str(self._total_actions))
            self.mgmt_tab.append_result(f"<b>[Sent]</b> Zero-Touch deployment completed successfully for: {fname}")
            QMessageBox.information(self, "Success", f"File '{fname}' deployed silently in background thread without user prompts!")
            self.file_tab.update_progress(0)
            self.file_tab._deploy_btn.setEnabled(True)
            
        def on_error(err_msg: str):
            self.file_tab.update_progress(0)
            self.mgmt_tab.append_result(f"<b>[Error]</b> Zero-Touch deployment failed: {err_msg}")
            QMessageBox.critical(self, "Deployment Error", f"Failed to transport file payload: {err_msg}")
            self.file_tab._deploy_btn.setEnabled(True)

        self.file_sender.finished_signal.connect(on_success)
        self.file_sender.error_signal.connect(on_error)
        self.file_sender.start()

    def _on_result_received(self, sock, output):
        dev = self.device_model.device_for_sock(sock)
        if dev:
            dev.update_last_seen()
            self.device_model.dataChanged.emit(QModelIndex(), QModelIndex())
        
        clean_output = output.replace("\n", "<br>")
        self.mgmt_tab.append_result(f"<b>[Response]</b>:<br>{clean_output}<br>")

    def closeEvent(self, event) -> None:
        self.server_worker.stop()
        self.server_thread.quit()
        self.server_thread.wait()
        if self.file_sender and self.file_sender.isRunning():
            self.file_sender.quit()
            self.file_sender.wait()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())