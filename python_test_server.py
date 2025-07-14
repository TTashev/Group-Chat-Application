import socket
import threading
import time

SERVER_IP = '127.0.0.1'
SERVER_PORT = 2000
NUM_CLIENTS = 100
MESSAGE_INTERVAL = 1  # seconds

def client_thread(index):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_IP, SERVER_PORT))
        print(f"[Client {index}] Connected to server.")

        # Send hello message
        name = f"Client{index}"
        message_count = 0

        def receive():
            while True:
                try:
                    data = sock.recv(1024)
                    if data:
                        print(f"[Client {index} RECEIVED]: {data.decode()}")
                except:
                    break

        threading.Thread(target=receive, daemon=True).start()

        while True:
            message = f"{name} : Hello {message_count}"
            sock.sendall(message.encode())
            print(f"[Client {index} SENT]: {message}")
            message_count += 1
            time.sleep(MESSAGE_INTERVAL)

    except Exception as e:
        print(f"[Client {index} ERROR]: {e}")
    finally:
        sock.close()

# Spawn multiple clients
for i in range(NUM_CLIENTS):
    threading.Thread(target=client_thread, args=(i,), daemon=True).start()

# Keep main thread alive
while True:
    time.sleep(10)

