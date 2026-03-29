import os
import socket
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from datetime import datetime
import threading
import time
from pyftpdlib.servers import FTPServer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.authorizers import DummyAuthorizer
import multiprocessing
import mysql.connector
from mysql.connector import Error

# -------------------- CONFIG --------------------
DB_CONFIG = {
    'host': 'localhost',
    'database': 'ftp_app',
    'user': 'root',
    'password': ''
}

BACKUP_FOLDER = 'ftp_backups'
os.makedirs(BACKUP_FOLDER, exist_ok=True)

# -------------------- COLORS & STYLES --------------------
COLORS = {
    'primary': '#2E3440',
    'secondary': '#3B4252',
    'accent': '#5E81AC',
    'success': '#A3BE8C',
    'warning': '#EBCB8B',
    'error': '#BF616A',
    'text': '#ECEFF4',
    'text_dark': '#4C566A',
    'bg_light': '#D8DEE9',
    'bg_medium': '#E5E9F0'
}

# -------------------- DB UTILS --------------------
def create_connection():
    return mysql.connector.connect(**DB_CONFIG)

def register_user(username, password):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username=%s", (username,))
        if cursor.fetchone():
            return False, "User already exists"
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return True, "Registered successfully"
    except Error as e:
        return False, f"MySQL Error: {e}"
    finally:
        if conn.is_connected(): conn.close()

def validate_login(username, password):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        return result and result[0] == password
    except Error:
        return False
    finally:
        if conn.is_connected(): conn.close()

def get_user_password(username):
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        result = cursor.fetchone()
        return result[0] if result else ""
    except Error:
        return ""
    finally:
        if conn.is_connected(): conn.close()

# -------------------- FTP SERVER --------------------
def run_ftp_server(port, folder, user, passwd):
    authorizer = DummyAuthorizer()
    authorizer.add_user(user, passwd, folder, perm='elradfmwMT')
    handler = FTPHandler
    handler.authorizer = authorizer
    server = FTPServer(("0.0.0.0", port), handler)
    server.serve_forever()

active_servers = []

# -------------------- GUI --------------------
class ModernButton(tk.Button):
    def __init__(self, parent, text, command=None, bg_color=COLORS['accent'], **kwargs):
        super().__init__(parent, text=text, command=command, **kwargs)
        self.config(
            bg=bg_color,
            fg=COLORS['text'],
            font=('Arial', 10, 'bold'),
            relief='flat',
            bd=0,
            cursor='hand2'
        )
        try:
            self.config(padx=20, pady=8)
        except:
            pass
        self.bind('<Enter>', lambda e: self.config(bg=self._lighten_color(bg_color)))
        self.bind('<Leave>', lambda e: self.config(bg=bg_color))
    
    def _lighten_color(self, color):
        # Simple color lightening
        if color == COLORS['accent']: return '#6B8BBB'
        if color == COLORS['success']: return '#B5C99A'
        if color == COLORS['error']: return '#D67682'
        if color == COLORS['warning']: return '#F0D08A'
        return color

class ModernEntry(tk.Entry):
    def __init__(self, parent, placeholder="", **kwargs):
        super().__init__(parent, **kwargs)
        self.placeholder = placeholder
        try:
            self.config(
                font=('Arial', 11),
                relief='flat',
                bd=1,
                highlightthickness=2,
                highlightcolor=COLORS['accent'],
                highlightbackground=COLORS['text_dark'],
                bg=COLORS['bg_light'],
                fg=COLORS['text_dark'],
                insertbackground=COLORS['text_dark']
            )
        except:
            # Fallback configuration
            self.config(
                font=('Arial', 11),
                relief='flat',
                bd=1,
                bg=COLORS['bg_light'],
                fg=COLORS['text_dark']
            )
        
        if placeholder:
            self.insert(0, placeholder)
            self.config(fg=COLORS['text_dark'])
            self.bind('<FocusIn>', self._on_focus_in)
            self.bind('<FocusOut>', self._on_focus_out)
    
    def _on_focus_in(self, event):
        if self.get() == self.placeholder:
            self.delete(0, tk.END)
            self.config(fg=COLORS['primary'])
    
    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.config(fg=COLORS['text_dark'])

class FTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 WiFi FTP Manager")
        self.root.geometry("900x650")
        self.root.configure(bg=COLORS['bg_medium'])
        self.root.resizable(True, True)
        
        # Configure styles
        self.setup_styles()
        
        # Create main container
        self.main_frame = tk.Frame(root, bg=COLORS['bg_medium'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.create_login_screen()

    def setup_styles(self):
        try:
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure treeview style
            style.configure("Modern.Treeview",
                           background=COLORS['bg_light'],
                           foreground=COLORS['text_dark'],
                           rowheight=35,
                           fieldbackground=COLORS['bg_light'],
                           font=('Arial', 10))
            
            style.configure("Modern.Treeview.Heading",
                           background=COLORS['secondary'],
                           foreground=COLORS['text'],
                           font=('Arial', 11, 'bold'))
        except:
            # Skip styling if there are issues
            pass

    def create_login_screen(self):
        self.clear_screen()
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=COLORS['primary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="🌐 WiFi FTP Manager", 
                              font=('Arial', 24, 'bold'), 
                              bg=COLORS['primary'], 
                              fg=COLORS['text'])
        title_label.pack(expand=True)
        
        # Main content
        content_frame = tk.Frame(self.main_frame, bg=COLORS['bg_medium'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left side - Login
        login_frame = tk.Frame(content_frame, bg=COLORS['bg_light'], padx=30, pady=30)
        login_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        
        tk.Label(login_frame, text="Login to Continue", 
                font=('Arial', 16, 'bold'), 
                bg=COLORS['bg_light'], 
                fg=COLORS['primary']).pack(pady=(0, 20))

        tk.Label(login_frame, text="Username", 
                font=('Arial', 11), 
                bg=COLORS['bg_light'], 
                fg=COLORS['text_dark']).pack(anchor='w', pady=(10, 5))
        
        self.username_entry = ModernEntry(login_frame, width=25)
        self.username_entry.pack(pady=(0, 15))

        tk.Label(login_frame, text="Password", 
                font=('Arial', 11), 
                bg=COLORS['bg_light'], 
                fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 5))
        
        self.password_entry = ModernEntry(login_frame, width=25)
        self.password_entry.config(show="*")
        self.password_entry.pack(pady=(0, 20))

        button_frame = tk.Frame(login_frame, bg=COLORS['bg_light'])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ModernButton(button_frame, text="Login", command=self.login, 
                    bg_color=COLORS['success']).pack(fill=tk.X, pady=(0, 10))
        
        ModernButton(button_frame, text="Register New User", command=self.register, 
                    bg_color=COLORS['accent']).pack(fill=tk.X)

        # Right side - Active Servers
        servers_frame = tk.Frame(content_frame, bg=COLORS['bg_light'], padx=20, pady=30)
        servers_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(servers_frame, text="🖥️ Active FTP Servers", 
                font=('Arial', 16, 'bold'), 
                bg=COLORS['bg_light'], 
                fg=COLORS['primary']).pack(pady=(0, 20))
        
        # Scrollable frame for servers
        self.server_canvas = tk.Canvas(servers_frame, bg=COLORS['bg_light'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(servers_frame, orient="vertical", command=self.server_canvas.yview)
        self.scrollable_frame = tk.Frame(self.server_canvas, bg=COLORS['bg_light'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.server_canvas.configure(scrollregion=self.server_canvas.bbox("all"))
        )
        
        self.server_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.server_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.server_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.refresh_server_list()

    def create_server_card(self, srv, index):
        """Create a modern card for each server"""
        card_frame = tk.Frame(self.scrollable_frame, bg=COLORS['secondary'], relief='raised', bd=1)
        card_frame.pack(fill=tk.X, pady=8, padx=10)
        
        # Server info
        info_frame = tk.Frame(card_frame, bg=COLORS['secondary'])
        info_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(info_frame, text=f"👤 {srv['user']}", 
                font=('Arial', 12, 'bold'), 
                bg=COLORS['secondary'], fg=COLORS['text']).pack(anchor='w')
        
        tk.Label(info_frame, text=f"🔌 Port: {srv['port']}", 
                font=('Arial', 10), 
                bg=COLORS['secondary'], fg=COLORS['bg_medium']).pack(anchor='w')
        
        folder_text = srv['folder'][:50] + "..." if len(srv['folder']) > 50 else srv['folder']
        tk.Label(info_frame, text=f"📁 {folder_text}", 
                font=('Arial', 10), 
                bg=COLORS['secondary'], fg=COLORS['bg_medium']).pack(anchor='w')
        
        # Button frame
        btn_frame = tk.Frame(card_frame, bg=COLORS['secondary'])
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Create buttons with icons
        buttons = [
            ("📂 Change", lambda s=srv: self.change_folder(s), COLORS['accent']),
            ("🔄 Restore", lambda s=srv: self.restore_folder(s), COLORS['warning']),
            ("💾 Backup", lambda s=srv: self.manual_backup(s), COLORS['success']),
            ("⏹️ Stop", lambda s=srv: self.stop_server(s), COLORS['error'])
        ]
        
        for i, (text, cmd, color) in enumerate(buttons):
            btn = ModernButton(btn_frame, text=text, command=cmd, bg_color=color)
            btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

    def refresh_server_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not active_servers:
            no_servers_frame = tk.Frame(self.scrollable_frame, bg=COLORS['bg_light'])
            no_servers_frame.pack(fill=tk.BOTH, expand=True, pady=50)
            
            tk.Label(no_servers_frame, text="📡", 
                    font=('Arial', 48), 
                    bg=COLORS['bg_light'], 
                    fg=COLORS['text_dark']).pack()
            
            tk.Label(no_servers_frame, text="No Active Servers", 
                    font=('Arial', 14, 'bold'), 
                    bg=COLORS['bg_light'], 
                    fg=COLORS['text_dark']).pack(pady=(10, 5))
            
            tk.Label(no_servers_frame, text="Login and start your first FTP server!", 
                    font=('Arial', 11), 
                    bg=COLORS['bg_light'], 
                    fg=COLORS['text_dark']).pack()
            return

        for idx, srv in enumerate(active_servers):
            self.create_server_card(srv, idx)

    def backup_folder(self, folder, username, port):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        backup_dir_name = f"{username}_{port}_{timestamp}"
        backup_path = os.path.join(BACKUP_FOLDER, backup_dir_name)
        shutil.copytree(folder, backup_path)
        return backup_path

    def manual_backup(self, srv):
        try:
            backup_path = self.backup_folder(srv['folder'], srv['user'], srv['port'])
            srv['latest_backup'] = backup_path
            messagebox.showinfo("✅ Backup Created", f"Backup successfully created at:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("❌ Backup Error", str(e))

    def restore_folder(self, srv):
        if not srv['latest_backup']:
            messagebox.showerror("⚠️ No Backup", "No backup available yet.\nPlease create a manual backup first.")
            return

        target_folder = srv['folder']
        try:
            shutil.copytree(srv['latest_backup'], target_folder, dirs_exist_ok=True)
            messagebox.showinfo("✅ Restored", f"Backup successfully restored to:\n{target_folder}")
        except Exception as e:
            messagebox.showerror("❌ Restore Error", str(e))

    def stop_server(self, srv):
        if srv['process'].is_alive():
            srv['process'].terminate()
        active_servers.remove(srv)
        self.refresh_server_list()
        messagebox.showinfo("⏹️ Server Stopped", "FTP Server has been stopped successfully!")

    def change_folder(self, srv):
        new_folder = filedialog.askdirectory(title="Select New Folder to Share")
        if not new_folder:
            return
        self.stop_server(srv)
        self.start_ftp_server(srv['port'], new_folder, srv['user'], srv['password'])
        self.refresh_server_list()
        messagebox.showinfo("📂 Folder Changed", f"Now sharing: {new_folder}")

    def create_main_screen(self, username):
        self.username = username
        self.clear_screen()
        
        # Header
        header_frame = tk.Frame(self.main_frame, bg=COLORS['primary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text=f"Welcome back, {username}! 👋", 
                              font=('Arial', 20, 'bold'), 
                              bg=COLORS['primary'], 
                              fg=COLORS['text'])
        title_label.pack(expand=True)
        
        # Content
        content_frame = tk.Frame(self.main_frame, bg=COLORS['bg_light'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        tk.Label(content_frame, text="🚀 Start New FTP Server", 
                font=('Arial', 18, 'bold'), 
                bg=COLORS['bg_light'], 
                fg=COLORS['primary']).pack(pady=(0, 30))

        # Form
        form_frame = tk.Frame(content_frame, bg=COLORS['bg_light'])
        form_frame.pack(anchor='center')
        
        tk.Label(form_frame, text="Port Number", 
                font=('Arial', 12, 'bold'), 
                bg=COLORS['bg_light'], 
                fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 5))
        
        self.port_entry = ModernEntry(form_frame, width=30)
        self.port_entry.insert(0, "2121")
        self.port_entry.pack(pady=(0, 20))

        tk.Label(form_frame, text="Folder to Share", 
                font=('Arial', 12, 'bold'), 
                bg=COLORS['bg_light'], 
                fg=COLORS['text_dark']).pack(anchor='w', pady=(0, 5))

        folder_frame = tk.Frame(form_frame, bg=COLORS['bg_light'])
        folder_frame.pack(fill=tk.X, pady=(0, 30))
        
        self.folder_path = tk.StringVar()
        self.folder_entry = ModernEntry(folder_frame, textvariable=self.folder_path, width=35)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(folder_frame, text="📁 Browse", command=self.browse_folder,
                    bg_color=COLORS['accent']).pack(side=tk.LEFT)

        # Action buttons
        action_frame = tk.Frame(form_frame, bg=COLORS['bg_light'])
        action_frame.pack(fill=tk.X, pady=(20, 0))
        
        ModernButton(action_frame, text="🚀 Start FTP Server", command=self.start_ftp,
                    bg_color=COLORS['success']).pack(side=tk.LEFT, padx=(0, 10))
        
        ModernButton(action_frame, text="🔙 Back to Login", command=self.logout,
                    bg_color=COLORS['error']).pack(side=tk.LEFT)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory(title="Select Folder to Share")
        if folder_selected:
            self.folder_path.set(folder_selected)

    def start_ftp(self):
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("❌ Invalid Port", "Please enter a valid port number")
            return

        folder = self.folder_path.get()
        if not folder:
            messagebox.showerror("❌ No Folder", "Please select a folder to share")
            return

        # Check if selected folder is a full drive
        if folder.strip().lower() in ['c:/', 'd:/', 'e:/', 'f:/']:
            response = messagebox.askquestion(
                "⚠️ Full Drive Warning",
                f"""You're trying to share the full drive ({folder}).
It's recommended to select a specific folder instead.

Do you want to select a different folder?""",
                icon='warning'
            )
            if response == 'yes':
                folder_selected = filedialog.askdirectory(title="Choose Specific Folder to Share")
                if not folder_selected:
                    return
                folder = folder_selected
                self.folder_path.set(folder)
            return

        self.start_ftp_server(port, folder, self.username, get_user_password(self.username))
        ip = get_local_ip()
        messagebox.showinfo("🎉 FTP Server Started!", 
                           f"Server started successfully!\n\n"
                           f"📍 IP Address: {ip}\n"
                           f"🔌 Port: {port}\n\n"
                           f"Connect using any FTP client with these details.")
        self.logout()

    def start_ftp_server(self, port, folder, user, passwd):
        p = multiprocessing.Process(target=run_ftp_server, args=(port, folder, user, passwd))
        p.start()

        server_data = {
            "process": p,
            "port": port,
            "folder": folder,
            "user": user,
            "password": passwd,
            "latest_backup": None
        }

        active_servers.append(server_data)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("❌ Missing Fields", "Please enter both username and password")
            return
            
        if validate_login(username, password):
            self.create_main_screen(username)
        else:
            messagebox.showerror("❌ Login Failed", "Invalid username or password")

    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("❌ Missing Fields", "Please enter both username and password")
            return
            
        success, msg = register_user(username, password)
        if success:
            messagebox.showinfo("✅ Registration Successful", msg)
        else:
            messagebox.showerror("❌ Registration Failed", msg)

    def logout(self):
        self.create_login_screen()

    def clear_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    app = FTPApp(root)
    root.mainloop()