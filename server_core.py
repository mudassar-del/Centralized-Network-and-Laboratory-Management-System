import os
import socket
import threading
import json
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from protocol import *

# === PORT CONFIGURATION (MATCHED WITH CONFIG.JSON) ===
HOST = "0.0.0.0"
PORT = 5000

class NetworkServerThread(QThread):
    # GUI ko updates bhejne ke liye Signals
    client_connected = pyqtSignal(str, str)     # hostname, ip
    client_disconnected = pyqtSignal(str)       # ip
    result_received = pyqtSignal(str, str)      # ip, result_data

    def __init__(self):
        super().__init__()
        self.server = None
        self.is_running = True
        self.connected_clients = {} # { ip: (socket_obj, hostname) }

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((HOST, PORT))
            self.server.listen()
            print(f"[SERVER] Listening on {PORT}")
        except Exception as e:
            print(f"[SERVER] Bind Error: {e}")
            return

        while self.is_running:
            try:
                client_socket, addr = self.server.accept()
                ip_address = addr[0]
                print(f"[SERVER] Connected: {addr}")
                
                # Default hostname (Starting me IP hi rakh rahe hain, client response se update ho jayega)
                hostname = f"LAB-PC-{ip_address.split('.')[-1]}" 
                
                self.connected_clients[ip_address] = (client_socket, hostname)
                
                # GUI Table me client add karne ke liye signal emit karo
                self.client_connected.emit(hostname, ip_address)

                # Har client ke liye alag background thread
                threading.Thread(
                    target=self.receive_client,
                    args=(client_socket, ip_address),
                    daemon=True
                ).start()
            except:
                break

    def receive_client(self, client_socket, ip_address):
        while self.is_running:
            try:
                data = client_socket.recv(8192)
                if not data:
                    break

                msg = parse_message(data)

                if msg.get("type") == "result":
                    # GUI ke Log aur Dashboard me data bhejne ke liye signal emit karo
                    self.result_received.emit(ip_address, str(msg.get("data", "")))

            except:
                break

        print(f"[SERVER] {ip_address} disconnected")
        if ip_address in self.connected_clients:
            del self.connected_clients[ip_address]
        
        # GUI Table se client remove karne ke liye signal emit karo
        self.client_disconnected.emit(ip_address)
        client_socket.close()

    # GUI se commands execute karne ke liye functions
    def send_command_to_client(self, ip_address, command_text):
        if ip_address in self.connected_clients:
            client_socket = self.connected_clients[ip_address][0]
            try:
                client_socket.send(create_command(command_text))
                return True
            except:
                return False
        return False

    def send_file_to_client(self, ip_address, filepath):
        if ip_address in self.connected_clients:
            client_socket = self.connected_clients[ip_address][0]
            try:
                filename = os.path.basename(filepath)
                with open(filepath, "rb") as f:
                    filedata = f.read()
                
                message = create_file_message(filename, filedata)
                client_socket.send(message)
                return True
            except Exception as e:
                print(f"File Send Error: {e}")
                return False
        return False

# ========================================================
# === ASLI INJECTION: GUI AUR NETWORK ENGINE KO JODO ===
# ========================================================
if __name__ == "__main__":
    print("[SYSTEM] Initializing CNLMS Central Server Engine...")
    
    # 1. PyQt6 ki core application instance banayein
    app = QApplication(sys.argv)
    
    # 2. Network Thread ko start karein taake sockets background me active ho jayein
    server_thread = NetworkServerThread()
    server_thread.start()
    
    # 3. gui.py se MainWindow class ko import karke screen par layein
    try:
        from gui_app import MainWindow
        main_ui = MainWindow(server_thread)  # Network logic window ko pass kar di
        main_ui.show()
        print("[SYSTEM] Sky Blue GUI Dashboard loaded successfully!")
    except ImportError as e:
        print(f"[UI ERROR] Could not find 'MainWindow' inside 'gui.py'. Please check class name! Error: {e}")
        sys.exit(1)
        
    # 4. Main Event Loop start karein
    sys.exit(app.exec())