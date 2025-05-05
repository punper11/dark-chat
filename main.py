import socket
from datetime import datetime
import time
from operator import contains
from turtle import Tbuffer

import wx
from wx import *
import wx.richtext
from cryptography.fernet import Fernet
import threading
import wx.adv
import random
import os
import json
import re
import webbrowser


class DarkChat(wx.Frame):
    def __init__(self):
        try:
            with open('config.json', 'r') as file:
                self.data = json.load(file)
        except Exception as e:
            print(f"[!] Error opening config file: {e}")
        base_path = os.path.join(os.path.dirname(__file__), "SFX")
        self.chatSounds = [wx.adv.Sound(os.path.join(base_path, self.data["MessageSound1"])),wx.adv.Sound(os.path.join(base_path, self.data["MessageSound2"])),wx.adv.Sound(os.path.join(base_path, self.data["MessageSound3"]))]
        self.playerJoinSound = wx.adv.Sound(os.path.join(base_path, self.data["PlayerJoinSound"]))
        self.errorSound = wx.adv.Sound(os.path.join(base_path, self.data["ErrorSound"]))
        self.connectSound = wx.adv.Sound(os.path.join(base_path, self.data["ConnectSound"]))
        self.disconnectSound = wx.adv.Sound(os.path.join(base_path, self.data["DisconnectSound"]))
        self.startupSound = wx.adv.Sound(os.path.join(base_path, self.data["StartupSound"]))
        self.color1 = wx.Colour(self.data["color1_1"], self.data["color1_2"], self.data["color1_3"])
        self.color2 = wx.Colour(self.data["color2_1"], self.data["color2_2"], self.data["color2_3"])
        self.color3 = wx.Colour(self.data["color3_1"], self.data["color3_2"], self.data["color3_3"])
        self.color4 = wx.Colour(self.data["color4_1"], self.data["color4_2"], self.data["color4_3"])
        self.color5 = wx.Colour(self.data["color5_1"], self.data["color5_2"], self.data["color5_3"])
        self.ip = f""
        self.port = 80
        self.ekey = f""
        self.connected = False
        self.buffer = b""
        self.usernameCode = "USERNAME_OK_56788677676742446876563470743401"
        super().__init__(parent=None, title="Dark Chat", size=(1000,750))
        self.SetBackgroundColour(self.color1)
        self.mpnl = wx.Panel(self)
        self.mpnl.SetBackgroundColour(self.color1)

        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        # === Room Label ===
        self.roomLbl = wx.StaticText(self.mpnl, label="[Not connected to a room.]")
        self.roomLbl.SetForegroundColour(self.color2)
        self.roomLbl.SetBackgroundColour(self.color4)
        font = self.roomLbl.GetFont()
        font.PointSize += 2
        font = font.Bold()
        self.roomLbl.SetFont(font)
        self.roomLbl.Wrap(-1)
        self.roomLbl.SetWindowStyleFlag(wx.ALIGN_CENTER)
        left_sizer.Add(self.roomLbl, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        # === Form Inputs (Left side) ===
        form_sizer = wx.FlexGridSizer(0, 2, 10, 10)
        form_sizer.AddGrowableCol(1, 1)

        self.ipLbl = wx.StaticText(self.mpnl, label="Enter IP:")
        self.ipEntry = wx.TextCtrl(self.mpnl, style=wx.BORDER_NONE)
        self.portLbl = wx.StaticText(self.mpnl, label="Enter port:")
        self.portEntry = wx.TextCtrl(self.mpnl, style=wx.BORDER_NONE)
        self.encryptionKeyLbl = wx.StaticText(self.mpnl, label="Enter encryption key:")
        self.encryptionKeyEntry = wx.TextCtrl(self.mpnl, style=wx.BORDER_NONE)

        for label in [self.ipLbl, self.portLbl, self.encryptionKeyLbl]:
            label.SetForegroundColour(self.color2)
            label.SetBackgroundColour(self.color4)

        for entry in [self.ipEntry, self.portEntry, self.encryptionKeyEntry]:
            entry.SetBackgroundColour(self.color4)
            entry.SetForegroundColour(self.color2)

        form_sizer.AddMany([
            (self.ipLbl, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.ipEntry, 1, wx.EXPAND),
            (self.portLbl, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.portEntry, 1, wx.EXPAND),
            (self.encryptionKeyLbl, 0, wx.ALIGN_CENTER_VERTICAL),
            (self.encryptionKeyEntry, 1, wx.EXPAND),
        ])

        left_sizer.Add(form_sizer, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # === Connect Button ===
        self.connectbutton = wx.Button(self.mpnl, label="Click me to connect!", style=wx.NO_BORDER)
        self.connectbutton.Bind(wx.EVT_BUTTON, self.connect)
        self.connectbutton.SetBackgroundColour(self.color5)
        self.connectbutton.SetForegroundColour(self.color2)
        left_sizer.Add(self.connectbutton, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        # === Disconnect Button (now below connect inputs) ===
        self.disconnectbutton = wx.Button(self.mpnl, label="Disconnect", style=wx.NO_BORDER, size=wx.Size(200, 50))
        self.disconnectbutton.Bind(wx.EVT_BUTTON, self.disconnect)
        self.disconnectbutton.SetBackgroundColour(self.color5)
        self.disconnectbutton.SetForegroundColour(self.color2)
        left_sizer.Add(self.disconnectbutton, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        left_sizer.AddSpacer(20)

        # === User List ===
        self.userListLabel = wx.StaticText(self.mpnl, label="User List")
        self.userList = wx.TextCtrl(self.mpnl, style=wx.LB_SINGLE)
        self.userList.SetMinSize(wx.Size(200, 150))
        self.userListLabel.SetBackgroundColour(self.color4)
        self.userListLabel.SetForegroundColour(self.color2)
        self.userList.SetBackgroundColour(self.color5)
        self.userList.SetForegroundColour(self.color2)

        left_sizer.Add(self.userListLabel, flag=wx.ALIGN_CENTER | wx.TOP, border=10)
        left_sizer.Add(self.userList, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # === Chat Area (Right side) ===
        self.chat = wx.richtext.RichTextCtrl(self.mpnl,
                                             style=wx.TE_MULTILINE | wx.TE_RICH2 | wx.HSCROLL | wx.TE_READONLY)
        self.chatEntry = wx.TextCtrl(self.mpnl, style=wx.TE_PROCESS_ENTER | wx.BORDER_SIMPLE)  # Added visible border

        self.chat.SetBackgroundColour(self.color3)
        self.chat.Bind(wx.EVT_TEXT_URL, self.OnURL)
        self.chatEntry.SetBackgroundColour(self.color4)
        self.chatEntry.SetForegroundColour(self.color2)
        self.chatEntry.Bind(wx.EVT_TEXT_ENTER, self.send)

        right_sizer.Add(self.chat, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)
        right_sizer.Add(self.chatEntry, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=10)

        # === Combine Layouts ===
        main_sizer.Add(left_sizer, proportion=0, flag=wx.EXPAND | wx.ALL, border=10)
        main_sizer.Add(right_sizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        # === Final Setup ===
        self.mpnl.SetSizer(main_sizer)
        self.disconnectbutton.Hide()
        self.userList.Hide()
        self.userListLabel.Hide()
        self.connectbutton.Show()
        self.ipLbl.Show()
        self.ipEntry.Show()
        self.portLbl.Show()
        self.portEntry.Show()
        self.encryptionKeyLbl.Show()
        self.encryptionKeyEntry.Show()
        self.Layout()
        self.Show()
        self.startupSound.Play()

    def connect(self, event):
        self.chat.SetValue("")
        self.usernameCode = "USERNAME_OK_56788677676742446876563470743401"
        self.mainsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mainsock.settimeout(None)
        try:
            self.ekey = f"{self.encryptionKeyEntry.GetValue()}"
            self.fernet = Fernet(self.ekey)
        except Exception as e:

            self.chat.BeginTextColour(wx.Colour(255, 0,0))

            self.chat.WriteText(f"[!] Invalid encryption key: {e}\n")

            self.chat.EndTextColour()
            self.errorSound.Play()
            return
        try:
            self.ip = f"{self.ipEntry.GetValue()}"
            self.port = int(self.portEntry.GetValue())
            self.mainsock.connect((self.ip, self.port))
        except Exception as e:
            print(f"[!] Could not connect: {e}\n")
            self.errorSound.Play()
            return
        test = "AUTH"
        self.mainsock.sendall(self.fernet.encrypt(test.encode()))
        try:
            response = self.fernet.decrypt(self.mainsock.recv(1024)).decode()
            if response != "KEY_OK":

                self.chat.BeginTextColour(wx.Colour(255, 0, 0))

                self.chat.WriteText("[!] Server rejected encryption key.\n")

                self.chat.EndTextColour()
                self.errorSound.Play()
                return
        except Exception as e:

            self.chat.BeginTextColour(wx.Colour(255, 0, 0))

            self.chat.WriteText(f"[!] Error during handshake: {e}\n")
            self.chat.EndTextColour()
            self.errorSound.Play()
            return
        self.connected = True
        self.disconnectbutton.Show()
        self.userList.Show()
        self.connectbutton.Hide()
        self.ipLbl.Hide()
        self.ipEntry.Hide()
        self.portLbl.Hide()
        self.portEntry.Hide()
        self.encryptionKeyLbl.Hide()
        self.encryptionKeyEntry.Hide()
        self.connectSound.Play()
        try:
            full_msg = self.fernet.decrypt(self.mainsock.recv(1024)).decode()
            if "||" in full_msg:
                prompt, roomName = full_msg.split("||", 1)

                self.chat.BeginTextColour(wx.Colour(186, 85, 211))
                self.chat.BeginBold()
                self.chat.WriteText(prompt + "\n")
                self.chat.EndBold()
                self.chat.EndTextColour()
                self.roomLbl.SetLabel("[" + roomName + "]")
                self.mpnl.Layout()
            else:

                self.chat.BeginTextColour(wx.Colour(255, 0, 0))
                self.chat.WriteText(f"[!] Malformed username message: {full_msg}\n")
                self.chat.EndTextColour()
                self.errorSound.Play()
        except Exception as e:

            self.chat.BeginTextColour(wx.Colour(255, 0,0))
            self.chat.WriteText(f"[!] Error receiving initial info: {e}\n")
            self.chat.EndTextColour()
            self.errorSound.Play()
        if not hasattr(self, 'recv_thread') or not self.recv_thread.is_alive():
            self.recv_thread = threading.Thread(target=self.receive, daemon=True)
            self.recv_thread.start()

    def receive(self):
        print("Receive thread started.")
        self.buffer = b""
        while self.connected:
            try:
                raw = self.mainsock.recv(4096)
                if not raw:
                    break

                self.buffer += raw

                while len(self.buffer) >= 4:
                    # Read the 4-byte length prefix
                    msg_len = int.from_bytes(self.buffer[:4], byteorder="big")

                    if len(self.buffer) < 4 + msg_len:
                        # Not enough data yet
                        break

                    encrypted_msg = self.buffer[4:4 + msg_len]
                    self.buffer = self.buffer[4 + msg_len:]

                    try:
                        msg = self.fernet.decrypt(encrypted_msg).decode()
                        print(f"Decrypted message: {msg}")
                        wx.CallAfter(self.checkMsgAndWrite, msg)
                    except Exception as e:
                        print(f"[!] Failed to decrypt: {e}")
                        wx.CallAfter(
                            self.recieveAndWrite,
                            f"[!] Failed to decrypt message: {e}\n",
                            False,
                            wx.Colour(255, 0, 0)
                        )
                        self.errorSound.Play()

            except Exception as e:
                if hasattr(e, "winerror") and e.winerror == 10038:
                    break
                print(f"[!] Receive exception: {e}")
                wx.CallAfter(self.recieveAndWrite, f"[!] Receive error: {e}\n", False, wx.Colour(255, 0, 0))
                self.errorSound.Play()
                break

        wx.CallAfter(self.disconnect)


    def checkMsgAndWrite(self, msg=""):

        for line in msg.splitlines():
            print("Decrypted message:", line)

        # Try parsing as JSON
        try:
            parsed = json.loads(msg)
            if parsed.get("type") == "USER_LIST":
                users = parsed["users"]
                self.changeUserList(users)
                return
        except json.JSONDecodeError:
            pass  # Not a JSON message

        # Handle chat message types
        if "has joined the chat!" in msg:
            self.playerJoinSound.Play()
            self.recieveAndWrite( f"{msg}\n", False, wx.Colour(0, 255, 0))

        elif self.usernameCode in msg:
            usernameCode = None
            self.clearChat()

        elif re.search(r"(https?://[^\s]+|www\.[^\s]+)", msg):
            random.choice(self.chatSounds).Play()
            splitMsg = msg.split("]:", 1)
            self.chat.SetEditable(True)
            self.recieveAndWrite( f"{splitMsg[0]}]:", False, wx.Colour(255, 255, 255))
            self.chat.SetEditable(False)
            self.write_message_with_links(splitMsg[1])
        else:
            random.choice(self.chatSounds).Play()
            self.chat.SetEditable(True)
            self.recieveAndWrite(f"{msg}\n", False, wx.Colour(255, 255, 255))
            self.chat.EndTextColour()
            self.chat.SetEditable(False)

    def changeUserList(self, users):
        print("Received user list:", users)
        self.userList.Clear()
        for user in users:
            self.userList.AppendText(f"{user}\n")
    def clearChat(self):
        self.chat.SetValue("")

    def recieveAndWrite(self, msg, isBold=False, color=wx.Colour(255,255,255)):
        self.chat.BeginTextColour(color)
        if isBold:
            self.chat.BeginBold()
        self.chat.WriteText(msg)
        if isBold:
            self.chat.EndBold()
        self.chat.EndTextColour()

    def write_message_with_links(self, msg):
        try:
            self.chat.SetEditable(True)
            self.chat.BeginAlignment(wx.TEXT_ALIGNMENT_LEFT)

            # Match URLs that are properly formatted
            url_pattern = re.compile(
                r"\b((?:https?://|www\.)[^\s\"'<>]+)", re.IGNORECASE
            )

            last_end = 0
            for match in url_pattern.finditer(msg):
                start, end = match.span()
                url = match.group()

                # Write any text before the URL
                if start > last_end:
                    self.chat.BeginTextColour(wx.Colour(255, 255, 255))
                    self.chat.WriteText(msg[last_end:start])
                    self.chat.EndTextColour()

                # Basic URL validation: avoid writing broken links
                if "." in url and len(url) < 2083:
                    full_url = url if url.startswith("http") else "http://" + url

                    self.chat.BeginTextColour(wx.Colour(0, 255, 255))  # Cyan
                    self.chat.BeginUnderline()
                    self.chat.BeginURL(full_url)
                    self.chat.WriteText(url)
                    self.chat.EndURL()
                    self.chat.EndUnderline()
                    self.chat.EndTextColour()
                else:
                    # Write broken/partial URL as normal text
                    self.chat.BeginTextColour(wx.Colour(255, 255, 255))
                    self.chat.WriteText(url)
                    self.chat.EndTextColour()

                last_end = end

            # Write any remaining text
            if last_end < len(msg):
                self.chat.BeginTextColour(wx.Colour(255, 255, 255))
                self.chat.WriteText(msg[last_end:])
                self.chat.EndTextColour()

            self.chat.WriteText("\n")
            self.chat.SetEditable(False)

        except Exception as e:
            print(f"Error while parsing URLs: {e}")
            self.chat.BeginTextColour(wx.Colour(255, 255, 255))
            self.chat.WriteText(msg + "\n")
            self.chat.EndTextColour()
            self.chat.SetEditable(False)

    def send(self, event=None):
        if not self.connected:
            return
        else:
            try:
                msg = self.chatEntry.GetValue().strip()
                if msg:
                    self.mainsock.sendall(self.fernet.encrypt(msg.encode()))
                    self.chatEntry.SetValue("")
            except Exception as e:

                self.chat.BeginTextColour(wx.Colour(255, 0, 0))
                self.chat.AppendText(f"[!] Error sending message: {e}\n")
                self.chat.EndTextColour()
                self.errorSound.Play()


    def disconnect(self, event=None):
        if self.connected:
            try:
                self.roomLbl.SetLabel("[Not connected to a room.]")
                self.connected = False

                try:
                    self.mainsock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                self.mainsock.close()
            except:
                pass
            self.chat.Clear()   
            self.chat.EndURL()
            self.chat.BeginTextColour(wx.Colour(186, 85, 211))
            self.chat.WriteText("[*] Disconnected from server.\n")
            self.chat.EndTextColour()
            self.disconnectSound.Play()
            self.userList.SetValue("")
            self.disconnectbutton.Hide()
            self.userList.Hide()
            self.connectbutton.Show()
            self.ipLbl.Show()
            self.ipEntry.Show()
            self.portLbl.Show()
            self.portEntry.Show()
            self.encryptionKeyLbl.Show()
            self.encryptionKeyEntry.Show()
            self.mpnl.Layout()

    def OnURL(self, event):
        url = event.GetString()
        print(f"Opening URL: {url}")
        webbrowser.open(url)







if __name__ == '__main__':
    app = wx.App(False)
    frame = DarkChat()
    app.MainLoop()

# while True:
#    dt = datetime.now().strftime("[%m/%d/%Y] [%I:%M:%S|%p]")
#    print(dt)
#    time.sleep(1)