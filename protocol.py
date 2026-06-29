import json
import base64

# Unique Marker jo har network packet ke end ko identify karega
DELIMITER = "<END_OF_MSG>"

def create_command(command):
    payload = {"type": "command", "data": command}
    # Message ke end me delimiter lagana zaroori hai
    return (json.dumps(payload) + DELIMITER).encode('utf-8')

def create_result(output):
    payload = {"type": "result", "data": output}
    return (json.dumps(payload) + DELIMITER).encode('utf-8')

def parse_message(data):
    # Agar data bytes me hai to pehle string me convert karenge
    if isinstance(data, bytes):
        data_str = data.decode('utf-8', errors='ignore')
    else:
        data_str = data
        
    # Delimiter ko clean karke JSON parse karna
    clean_data = data_str.replace(DELIMITER, "").strip()
    return json.loads(clean_data)

def create_file_message(filename, filedata_bytes, silent_flag=""):
    """
    Hex ki jagah Base64 use kar rahe hain jo memory optimized hai aur 
    client agent ke naye architecture ke sath 100% compatible hai.
    Sath hi silent_flag support add kiya hai taake GUI isko access kar sake.
    """
    # Binary bytes ko base64 string me convert karna
    b64_string = base64.b64encode(filedata_bytes).decode('utf-8')
    
    payload = {
        "type": "file",
        "filename": filename,
        "data": b64_string,
        "silent_flag": silent_flag  # Injected for zero-touch deployment mapping
    }
    return (json.dumps(payload) + DELIMITER).encode('utf-8')