from cryptography.fernet import Fernet

key = Fernet.generate_key()
print("Put this in config.json, and send it to anyone you want to join the chat room!\nHere is your key:\n" + key.decode())