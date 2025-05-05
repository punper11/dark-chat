import socket
import threading
from cryptography.fernet import Fernet
import json
import time

clients = []
usernames = {}

def broadcast(message):
    for client in clients:
        try:
            print(f"[>] Sending to client: {message}")
            payload = fernet.encrypt(message.encode())
            length_prefix = len(payload).to_bytes(4, byteorder="big")
            client.sendall(length_prefix + payload)
        except:
            client.close()
            clients.remove(client)

def broadcast_user_list():
    user_list = [username for username in usernames.values()]
    message = json.dumps({"type": "USER_LIST", "users": user_list})
    for client in clients:
        try:
            print(f"[>] Sending to client: {message}")
            payload = fernet.encrypt(message.encode())
            length_prefix = len(payload).to_bytes(4, byteorder="big")
            client.sendall(length_prefix + payload)
        except:
            client.close()
            clients.remove(client)



def handleClient(conn, addr):

    print(f"[+] {addr} has connected to the room!")

    try:
        # Try to receive an encrypted "AUTH" handshake
        encrypted_test = conn.recv(1024)
        test_msg = fernet.decrypt(encrypted_test).decode()

        if test_msg != "AUTH":
            raise ValueError("Invalid handshake")

        conn.sendall(fernet.encrypt(b"KEY_OK"))
    except Exception as e:
        conn.sendall(fernet.encrypt(b"[!] Invalid encryption key."))
        conn.close()
        print(f"[!] Rejected {addr}: Invalid encryption key.")
        return
    combined_msg = f"[!] Enter your username: ||{data['roomname']}"
    conn.sendall(fernet.encrypt(combined_msg.encode()))
    username = fernet.decrypt(conn.recv(1024)).decode('utf-8').strip()
    usernames[conn] = username
    clients.append(conn)
    payload = fernet.encrypt(b"USERNAME_OK_56788677676742446876563470743401")
    length_prefix = len(payload).to_bytes(4, byteorder="big")
    conn.sendall(length_prefix + payload)
    welcome = f"[+] {username} has joined the chat!"
    print(welcome)
    broadcast(welcome)
    broadcast_user_list()

    while True:
        try:
            msg = fernet.decrypt(conn.recv(4096)).decode().strip()
            if not msg:
                break
            if msg != "" :
                print("[" + username + "]: " + msg)
                broadcast(f"[{username}]: {msg}")
        except:
            break

    print(f"[-] {username} disconnected.")
    broadcast(f"[-] {username} has left the chat.")
    clients.remove(conn)
    del usernames[conn]
    broadcast_user_list()
    conn.close()


try:
    with open('config.json', 'r') as file:
        data = json.load(file)
except Exception as e:
    print(f"[!] Error opening config file: {e}")
key = data["encryption"]
fernet = Fernet(key)
print(f"[*] Using encryption: " + data["encryption"])
try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error as e:
    print(f"[!] Error opening socket: {e}")
try:
    server.bind(("0.0.0.0", data["port"]))

except socket.error as e:
    print(f"[!] Error binding socket: {e}")

try:
    server.listen()
except socket.error as e:
    print(f"[!] Error listening on port " + str(data["port"]) + ":" + f"{e}")
print("[*] Server started on port: " + str(data["port"]))

while True:
    conn, addr = server.accept()
    threading.Thread(target=handleClient, args=(conn, addr)).start()