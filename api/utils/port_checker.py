# You can check if a port is in use by trying to bind to it with a socket.
# If the port is in use, increment the port number by 1 and try again recursively.
import socket

def find_free_port(
    port, 
    host: str = "127.0.0.1", 
    is_production: bool = False
):
    if is_production:
        host = '0.0.0.0'
        
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f'Checking port {port} for host {host}')
        s.settimeout(1)
        try:
            s.bind((host, port))
            return port  # Port is free
        except OSError:
            print(f'Port {port} is in use. Trying port {port + 1}')
            return find_free_port(port + 1, host)