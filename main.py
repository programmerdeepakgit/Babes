import os
import sys
import time
import random
import datetime
import socket
import threading
import pyperclip
import pyautogui
import pyjokes
import requests
import wolframalpha
import webbrowser
import re
import pprint
import pyttsx3
import json
import subprocess
from PIL import Image
from PyQt5 import QtWidgets, QtCore, QtGui, QtWebSockets, QtNetwork
from PyQt5.QtCore import QTimer, QTime, QDate, Qt, QSettings, QThread, pyqtSignal, QUrl, QObject
from PyQt5.QtGui import QMovie, QPixmap, QIcon, QFontDatabase
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog, QListWidgetItem, QInputDialog
from PyQt5.QtWebSockets import QWebSocketServer
from PyQt5.QtNetwork import QHostAddress

# Local imports
from Babes import BabesAssistant
from Babes.config import config

# Initialize assistant
obj = BabesAssistant()

# ============================== CONSTANTS ====================================
GREETINGS = ["hey babes", "babes", "wake up babes", "you there babes", 
            "time to work babes", "ok babes", "are you there babes"]
GREETINGS_RES = [
    "Always here for you", 
    "Ready and waiting",
    "Your wish is my command",
    "How may I help you today?",
    "Online and ready"
]

EMAIL_DIC = {
    'myself': 'goodvibesdeepak@gmail.com',
    'my official email': 'cytolearners@gmail.com',
    'my second email': 'ayushsingh05991@gmail.com'
}

COMMAND_MAP = {
    'time': ['what time is it', 'current time', 'tell me the time'],
    'date': ['what date is it', 'today\'s date', 'current date'],
    'todo': ['what\'s on my todo', 'show my tasks', 'todo list'],
    'add todo': ['add to my todo', 'add task'],
    'delete todo': ['remove task', 'delete todo'],
    'clear todos': ['clear all tasks', 'empty todo list'],
    'screenshot': ['take screenshot', 'capture screen'],
    'system info': ['system specs', 'system information'],
    'hide windows': ['minimize all', 'hide all windows'],
    'show windows': ['restore windows', 'show all windows'],
    'calculate': ['what is', 'how much is', 'calculate'],
    'search': ['search for', 'google'],
    'exit': ['goodbye', 'quit', 'exit', 'shutdown'],
    'open app': ['open', 'launch', 'start'],
    'play music': ['play music', 'play song', 'play some music'],
    'hide files': ['hide files', 'hide all files', 'make files invisible'],
    'show files': ['show files', 'show all files', 'make files visible'],
    'view screenshot': ['show screenshot', 'open screenshot', 'view screenshot'],
    'switch window': ['switch window', 'alt tab', 'change window'],
    'play video': ['play', 'play on youtube'],
    'help': ['help', 'what can you do', 'show commands']
}

websites = {
    'instagram': 'https://instagram.com',
    'youtube': 'https://youtube.com',
    'linkedin': 'https://linkedin.com',
    'chatgpt': 'https://chat.openai.com',
    'deepseek': 'https://deepseek.com',
    'whatsapp': 'https://web.whatsapp.com',
    'facebook': 'https://facebook.com',
    'google': 'https://google.com'
}

app_paths = {
    'chrome': 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'notepad': 'notepad.exe',
    'calculator': 'calc.exe',
    'music': 'wmplayer.exe',
    'spotify': os.path.expanduser('~/AppData/Roaming/Spotify/Spotify.exe')
}

# Initialize settings
settings = QSettings('BabesAI', 'BabesAssistant')
# ============================================================================

_engine = pyttsx3.init()

def _select_female_voice(engine):
    for voice in engine.getProperty('voices'):
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            return
    engine.setProperty('voice', engine.getProperty('voices')[0].id)

_select_female_voice(_engine)

def speak(text: str):
    try:
        _engine.say(text)
        _engine.runAndWait()
    except Exception as e:
        print(f"Speech error: {e}")

def get_asset_path(filename):
    """Get path to asset file with fallback to default location"""
    # Try local assets folder first
    local_path = os.path.join("assets", filename)
    if os.path.exists(local_path):
        return local_path
    
    # Try package assets folder
    package_path = os.path.join(os.path.dirname(__file__), "assets", filename)
    if os.path.exists(package_path):
        return package_path
    
    # Return None if not found (will be handled by caller)
    return None

def advanced_calculation(question):
    try:
        client = wolframalpha.Client(config.wolframalpha_id)
        answer = client.query(question)
        return next(answer.results).text
    except Exception as e:
        speak("I couldn't solve that. Please try asking differently")
        return None

def read_todo():
    todo_path = settings.value('todo_path', os.path.expanduser('~/todo.txt'))
    try:
        with open(todo_path, 'r') as f:
            todos = f.readlines()
        return "Your tasks:\n" + "".join(todos) if todos else "Your todo list is empty"
    except Exception as e:
        print(f"Todo error: {e}")
        return "I couldn't find your todo list"

def add_todo(task):
    todo_path = settings.value('todo_path', os.path.expanduser('~/todo.txt'))
    try:
        with open(todo_path, 'a') as f:
            f.write(f"- {task}\n")
        return f"I've added '{task}' to your todo list"
    except Exception as e:
        print(f"Todo error: {e}")
        return "I couldn't add to your todo list"

def delete_todo(index):
    todo_path = settings.value('todo_path', os.path.expanduser('~/todo.txt'))
    try:
        with open(todo_path, 'r') as f:
            todos = f.readlines()
        
        if 0 <= index < len(todos):
            deleted = todos.pop(index)
            with open(todo_path, 'w') as f:
                f.writelines(todos)
            return f"Removed: {deleted.strip()}"
        return "Invalid task number"
    except Exception as e:
        print(f"Todo error: {e}")
        return "I couldn't delete that task"

def clear_todos():
    todo_path = settings.value('todo_path', os.path.expanduser('~/todo.txt'))
    try:
        open(todo_path, 'w').close()
        return "Todo list cleared"
    except Exception as e:
        print(f"Todo error: {e}")
        return "I couldn't clear your todo list"

def take_screenshot(name="screenshot"):
    try:
        screenshot_dir = os.path.join("Babes", "Screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(screenshot_dir, f"{name}_{timestamp}.png")
        
        pyautogui.screenshot(filename)
        return f"Screenshot saved as {os.path.basename(filename)}"
    except Exception as e:
        print(f"Screenshot error: {e}")
        return "Failed to take screenshot"

def open_screenshot():
    try:
        screenshot_dir = os.path.join("Babes", "Screenshots")
        if not os.path.exists(screenshot_dir):
            return "No screenshots found"
            
        screenshots = sorted(
            [f for f in os.listdir(screenshot_dir) if f.endswith('.png')],
            key=lambda x: os.path.getmtime(os.path.join(screenshot_dir, x)),
            reverse=True
        )
        
        if screenshots:
            latest = os.path.join(screenshot_dir, screenshots[0])
            os.startfile(latest)
            return f"Opening {screenshots[0]}"
        return "No screenshots available"
    except Exception as e:
        return f"Failed to open screenshot: {str(e)}"

def get_system_info():
    try:
        info = obj.system_info()
        return info
    except Exception as e:
        print(f"System info error: {e}")
        return "Couldn't retrieve system information"

def window_control(action):
    try:
        if action == "hide":
            pyautogui.hotkey('win', 'd')
            return "All windows minimized"
        elif action == "show":
            pyautogui.hotkey('win', 'shift', 'm')
            return "Windows restored"
        else:
            return "Invalid window command"
    except Exception as e:
        print(f"Window control error: {e}")
        return "Failed to control windows"

def toggle_file_visibility(visible=True):
    try:
        if sys.platform != 'win32':
            return "This feature is only available on Windows"

        current_dir = os.getcwd()
        
        if visible:
            result = subprocess.run(
                ["attrib", "-h", current_dir, "/s", "/d"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                return "All files in this folder are now visible"
            return f"Failed to make files visible: {result.stderr}"
        else:
            result = subprocess.run(
                ["attrib", "+h", current_dir, "/s", "/d"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                return "All files in this folder are now hidden"
            return f"Failed to hide files: {result.stderr}"

    except Exception as e:
        return f"Error controlling file visibility: {str(e)}"

def launch_application(app_name):
    try:
        app_name_lower = app_name.lower()
        if app_name_lower in app_paths:
            os.startfile(app_paths[app_name_lower])
            return f"Opening {app_name}"
        
        os.startfile(app_name)
        return f"Opening {app_name}"
    except Exception as e:
        return f"Failed to open {app_name}: {str(e)}"

def play_music():
    try:
        music_dir = os.path.expanduser('~/Music')
        if os.path.exists(music_dir):
            songs = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
            if songs:
                song = random.choice(songs)
                os.startfile(os.path.join(music_dir, song))
                return f"Playing {song}"
        return "No music files found in Music directory"
    except Exception as e:
        return f"Failed to play music: {str(e)}"

def play_youtube_video(query):
    try:
        url = f"https://www.youtube.com/results?search_query={query}"
        webbrowser.open(url)
        return f"Searching YouTube for {query}"
    except Exception as e:
        return f"Failed to play video: {str(e)}"

def show_help():
    help_text = "Available commands:\n"
    for action, phrases in COMMAND_MAP.items():
        help_text += f"- {action}: {', '.join(phrases)}\n"
    return help_text

def match_command(cmd):
    cmd = cmd.lower()
    for action, keywords in COMMAND_MAP.items():
        for keyword in keywords:
            if keyword in cmd:
                return action, cmd.replace(keyword, "").strip()
    return None, cmd

class WebSocketServer(QObject):
    client_connected = pyqtSignal(str)
    command_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.server = QWebSocketServer("BabesServer", QWebSocketServer.NonSecureMode)
        self.clients = []
        
    def start(self):
        if not self.server.listen(QHostAddress.Any, 12345):
            print("Failed to start websocket server")
            return False
            
        self.server.newConnection.connect(self.handle_new_connection)
        print("WebSocket server started on port 12345")
        return True
        
    def handle_new_connection(self):
        client = self.server.nextPendingConnection()
        if client:
            self.clients.append(client)
            self.client_connected.emit(client.peerAddress().toString())
            
            client.textMessageReceived.connect(self.handle_message)
            client.disconnected.connect(self.handle_disconnection)
            
    def handle_message(self, message):
        self.command_received.emit(message)
        
    def handle_disconnection(self):
        client = self.sender()
        if client in self.clients:
            self.clients.remove(client)
            client.deleteLater()
            
    def send_to_all(self, message):
        for client in self.clients:
            client.sendTextMessage(message)

class AssistantThread(QThread):
    update_gui = pyqtSignal(str, str)
    command_processed = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.listening = False
        self.running = True
        self.websocket_server = WebSocketServer()
        self.websocket_server.moveToThread(self)
        self.websocket_server.command_received.connect(self.process_command)
        
    def run(self):
        if self.websocket_server.start():
            self.initialize()
        
        while self.running:
            if self.listening:
                command = obj.mic_input()
                if command:
                    self.process_command(command)
            time.sleep(0.5)
            
    def initialize(self):
        self.update_gui.emit('status_indicator', 'listening.gif')
        speak("Initializing all systems")
        speak("All systems ready")
        
        hour = datetime.datetime.now().hour
        if 0 <= hour < 12:
            greeting = "Good morning"
        elif 12 <= hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
            
        username = settings.value('username', '')
        if username:
            greeting += f" {username}"
            
        speak(greeting)
        speak(f"The time is {obj.tell_time()}")
        self.update_gui.emit('status_indicator', 'waiting.gif')
        
    def process_command(self, cmd):
        if not cmd:
            return
            
        cmd = cmd.lower().strip()
        self.update_gui.emit('text_display', f"You: {cmd}")
        self.update_gui.emit('status_indicator', 'listening.gif')
        
        try:
            if any(greet in cmd for greet in GREETINGS):
                response = random.choice(GREETINGS_RES)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            action, remainder = match_command(cmd)
            
            if action == 'time':
                time_str = obj.tell_time()
                response = f"The time is currently {time_str}"
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'date':
                date_str = obj.tell_me_date()
                response = f"Today is {date_str}"
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'todo':
                response = read_todo()
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'add todo':
                task = remainder if remainder else obj.mic_input()
                response = add_todo(task)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'delete todo':
                try:
                    index = int(re.search(r'\d+', cmd).group()) - 1
                    response = delete_todo(index)
                except:
                    response = "Please specify which task to delete"
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'clear todos':
                response = clear_todos()
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'screenshot':
                name = "screenshot"
                if "name" in cmd:
                    name = cmd.split("name")[1].strip()
                response = take_screenshot(name)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'view screenshot':
                response = open_screenshot()
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'system info':
                response = get_system_info()
                speak("Here's your system information")
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'hide windows':
                response = window_control("hide")
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'show windows':
                response = window_control("show")
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'hide files':
                response = toggle_file_visibility(False)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'show files':
                response = toggle_file_visibility(True)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'switch window':
                try:
                    pyautogui.hotkey('alt', 'tab')
                    response = "Switched window"
                except Exception as e:
                    response = f"Failed to switch window: {str(e)}"
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'calculate':
                result = advanced_calculation(remainder)
                if result:
                    response = f"The answer is {result}"
                    speak(response)
                    self.command_processed.emit(cmd, response)
                return
            
            elif action == 'search':
                query = remainder if remainder else obj.mic_input()
                speak(f"Searching for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                response = f"Searching for {query}"
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'open app':
                app = remainder if remainder else obj.mic_input()
                response = launch_application(app)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'play music':
                response = play_music()
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'play video':
                query = remainder if remainder else obj.mic_input()
                response = play_youtube_video(query)
                speak(response)
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'help':
                response = show_help()
                speak("Here's what I can do")
                self.command_processed.emit(cmd, response)
                return
            
            elif action == 'exit':
                response = "Goodbye"
                speak(response)
                self.command_processed.emit(cmd, response)
                self.running = False
                QApplication.quit()
                return
            
            else:
                response = "I didn't understand that command. Try saying 'help' for a list of commands"
                speak(response)
                self.command_processed.emit(cmd, response)
                
        except Exception as e:
            print(f"Command error: {e}")
            response = "An error occurred processing that command"
            speak(response)
            self.command_processed.emit(cmd, f"Error: {str(e)}")
            
        finally:
            self.update_gui.emit('status_indicator', 'waiting.gif')

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Babes AI Assistant")
        self.setMinimumSize(1000, 700)
        
        # Initialize assets directory
        self.assets_dir = self.get_assets_directory()
        
        # Load custom font
        font_db = QFontDatabase()
        font_path = os.path.join(self.assets_dir, "Roboto-Regular.ttf") if self.assets_dir else None
        
        if font_path and os.path.exists(font_path):
            font_id = font_db.addApplicationFont(font_path)
            if font_id != -1:
                self.app_font = font_db.applicationFontFamilies(font_id)[0]
            else:
                self.app_font = "Segoe UI"
        else:
            self.app_font = "Segoe UI"
        
        self.init_ui()
        
        self.assistant = AssistantThread()
        self.assistant.update_gui.connect(self.update_gui_element)
        self.assistant.command_processed.connect(self.display_response)
        self.assistant.start()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        
        self.load_chat_history()
        
    def get_assets_directory(self):
        """Find the assets directory with fallback options"""
        # Try local assets folder
        local_assets = os.path.join(os.path.dirname(__file__), "assets")
        if os.path.exists(local_assets):
            return local_assets
        
        # Try package assets folder
        package_assets = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        if os.path.exists(package_assets):
            return package_assets
        
        # Create assets folder if it doesn't exist
        os.makedirs("assets", exist_ok=True)
        return "assets"
        
    def init_ui(self):
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #1a1a2e;
            }}
            QLabel {{
                color: #e6e6e6;
                font-family: '{self.app_font}';
            }}
            QPushButton {{
                background-color: #4a4a6a;
                color: #ffffff;
                border-radius: 5px;
                padding: 8px;
                font-family: '{self.app_font}';
            }}
            QPushButton:hover {{
                background-color: #5a5a7a;
            }}
            QTextEdit, QTextBrowser {{
                background-color: #16213e;
                color: #e6e6e6;
                border: 1px solid #4a4a6a;
                border-radius: 5px;
                padding: 10px;
                font-family: '{self.app_font}';
            }}
            QListWidget {{
                background-color: #16213e;
                color: #e6e6e6;
                border: 1px solid #4a4a6a;
                border-radius: 5px;
            }}
            QLineEdit {{
                background-color: #16213e;
                color: #e6e6e6;
                border: 1px solid #4a4a6a;
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        # Central widget
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.central_widget.setLayout(self.main_layout)
        
        # Left sidebar
        self.sidebar = QtWidgets.QFrame()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setStyleSheet("background-color: #16213e;")
        self.sidebar_layout = QtWidgets.QVBoxLayout()
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.sidebar_layout.setSpacing(15)
        self.sidebar.setLayout(self.sidebar_layout)
        
        # Logo - with fallback if image not found
        self.logo = QtWidgets.QLabel()
        logo_path = os.path.join(self.assets_dir, "main_logo.png") if self.assets_dir else None
        if logo_path and os.path.exists(logo_path):
            self.logo.setPixmap(QPixmap(logo_path).scaled(100, 100, Qt.KeepAspectRatio))
        else:
            self.logo.setText("Babes AI")
            self.logo.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.logo.setAlignment(Qt.AlignCenter)
        self.sidebar_layout.addWidget(self.logo)
        
        # User settings button
        self.user_btn = QtWidgets.QPushButton("Set Username")
        self.user_btn.clicked.connect(self.set_username)
        self.sidebar_layout.addWidget(self.user_btn)
        
        # Todo section
        self.todo_label = QtWidgets.QLabel("Todo List")
        self.todo_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.sidebar_layout.addWidget(self.todo_label)
        
        self.todo_list = QtWidgets.QListWidget()
        self.sidebar_layout.addWidget(self.todo_list)
        
        self.todo_input = QtWidgets.QLineEdit()
        self.todo_input.setPlaceholderText("Add new task...")
        self.sidebar_layout.addWidget(self.todo_input)
        
        self.todo_buttons = QtWidgets.QHBoxLayout()
        self.add_todo_btn = QtWidgets.QPushButton("Add")
        self.add_todo_btn.clicked.connect(self.add_todo_from_ui)
        self.delete_todo_btn = QtWidgets.QPushButton("Delete")
        self.delete_todo_btn.clicked.connect(self.delete_todo_from_ui)
        self.clear_todo_btn = QtWidgets.QPushButton("Clear All")
        self.clear_todo_btn.clicked.connect(self.clear_todos_from_ui)
        self.todo_buttons.addWidget(self.add_todo_btn)
        self.todo_buttons.addWidget(self.delete_todo_btn)
        self.todo_buttons.addWidget(self.clear_todo_btn)
        self.sidebar_layout.addLayout(self.todo_buttons)
        
        # Main content area
        self.content_area = QtWidgets.QFrame()
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        self.content_area.setLayout(self.content_layout)
        
        # Top bar
        self.top_bar = QtWidgets.QHBoxLayout()
        
        # Menu button with fallback icon
        self.menu_btn = QtWidgets.QPushButton()
        menu_icon_path = os.path.join(self.assets_dir, "menu_icon.png") if self.assets_dir else None
        if menu_icon_path and os.path.exists(menu_icon_path):
            self.menu_btn.setIcon(QIcon(menu_icon_path))
        else:
            self.menu_btn.setText("☰")
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.setStyleSheet("border: none;")
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        
        self.title_label = QtWidgets.QLabel("Babes Voice Assistant")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.time_date_layout = QtWidgets.QVBoxLayout()
        self.date_label = QtWidgets.QLabel()
        self.time_label = QtWidgets.QLabel()
        self.time_date_layout.addWidget(self.date_label)
        self.time_date_layout.addWidget(self.time_label)
        
        self.top_bar.addWidget(self.menu_btn)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.title_label)
        self.top_bar.addStretch()
        self.top_bar.addLayout(self.time_date_layout)
        
        self.content_layout.addLayout(self.top_bar)
        
        # Chat area
        self.chat_area = QtWidgets.QTextBrowser()
        self.chat_area.setOpenExternalLinks(True)
        self.content_layout.addWidget(self.chat_area)
        
        # Animation/Status area
        self.animation_area = QtWidgets.QLabel()
        self.animation_area.setAlignment(Qt.AlignCenter)
        self.animation_area.setFixedHeight(150)
        
        # Load animation with fallback
        animation_path = os.path.join(self.assets_dir, "waiting.gif") if self.assets_dir else None
        if animation_path and os.path.exists(animation_path):
            movie = QMovie(animation_path)
            self.animation_area.setMovie(movie)
            movie.start()
        else:
            self.animation_area.setText("Status: Ready")
            self.animation_area.setStyleSheet("font-size: 18px;")
            
        self.content_layout.addWidget(self.animation_area)
        
        # Input area
        self.input_area = QtWidgets.QHBoxLayout()
        self.input_field = QtWidgets.QLineEdit()
        self.input_field.setPlaceholderText("Type your command here...")
        self.input_field.returnPressed.connect(self.send_text_command)
        
        # Mic button with fallback
        self.mic_btn = QtWidgets.QPushButton()
        mic_icon_path = os.path.join(self.assets_dir, "mic_off.png") if self.assets_dir else None
        if mic_icon_path and os.path.exists(mic_icon_path):
            self.mic_btn.setIcon(QIcon(mic_icon_path))
        else:
            self.mic_btn.setText("🎤")
        self.mic_btn.setFixedSize(60, 60)
        self.mic_btn.setStyleSheet("border-radius: 30px;")
        self.mic_btn.clicked.connect(self.toggle_mic)
        
        self.input_area.addWidget(self.input_field)
        self.input_area.addWidget(self.mic_btn)
        self.content_layout.addLayout(self.input_area)
        
        # Add sidebar and content area to main layout
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area)
        
        # Load initial todo list
        self.load_todo_list()
        
    def set_username(self):
        username, ok = QInputDialog.getText(self, 'Set Username', 'Enter your name:')
        if ok and username:
            settings.setValue('username', username)
            self.chat_area.append(f"<b>System:</b> Username set to {username}")
    
    def update_gui_element(self, element, value):
        if element == 'text_display':
            self.chat_area.append(value)
        elif element == 'status_indicator':
            if value.endswith('.gif'):
                gif_path = os.path.join(self.assets_dir, value) if self.assets_dir else None
                if gif_path and os.path.exists(gif_path):
                    movie = QMovie(gif_path)
                    self.animation_area.setMovie(movie)
                    movie.start()
                else:
                    self.animation_area.setText("Status: " + value.replace('.gif', ''))
    
    def display_response(self, command, response):
        self.chat_area.append(f"<b>You:</b> {command}")
        self.chat_area.append(f"<b>Babes:</b> {response}")
        self.save_chat_history()
        
    def update_clock(self):
        current_time = QTime.currentTime()
        current_date = QDate.currentDate()
        self.time_label.setText(current_time.toString('hh:mm:ss AP'))
        self.date_label.setText(current_date.toString('dddd, MMMM d, yyyy'))
    
    def toggle_mic(self):
        self.assistant.listening = not self.assistant.listening
        if self.assistant.listening:
            mic_icon_path = os.path.join(self.assets_dir, "mic_on.png") if self.assets_dir else None
            if mic_icon_path and os.path.exists(mic_icon_path):
                self.mic_btn.setIcon(QIcon(mic_icon_path))
            else:
                self.mic_btn.setText("🔴")
            speak("Listening")
            self.assistant.update_gui.emit('status_indicator', 'listening.gif')
        else:
            mic_icon_path = os.path.join(self.assets_dir, "mic_off.png") if self.assets_dir else None
            if mic_icon_path and os.path.exists(mic_icon_path):
                self.mic_btn.setIcon(QIcon(mic_icon_path))
            else:
                self.mic_btn.setText("🎤")
            speak("Microphone off")
            self.assistant.update_gui.emit('status_indicator', 'waiting.gif')
    
    def send_text_command(self):
        command = self.input_field.text()
        if command:
            self.input_field.clear()
            self.assistant.process_command(command)
    
    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()
    
    def load_todo_list(self):
        todo_path = settings.value('todo_path', os.path.expanduser('~/todo.txt'))
        try:
            with open(todo_path, 'r') as f:
                todos = f.readlines()
            self.todo_list.clear()
            for todo in todos:
                item = QListWidgetItem(todo.strip())
                self.todo_list.addItem(item)
        except Exception as e:
            print(f"Todo load error: {e}")
    
    def add_todo_from_ui(self):
        task = self.todo_input.text()
        if task:
            response = add_todo(task)
            self.todo_input.clear()
            self.load_todo_list()
            self.chat_area.append(f"<b>System:</b> {response}")
    
    def delete_todo_from_ui(self):
        selected = self.todo_list.currentRow()
        if selected >= 0:
            response = delete_todo(selected)
            self.load_todo_list()
            self.chat_area.append(f"<b>System:</b> {response}")
    
    def clear_todos_from_ui(self):
        response = clear_todos()
        self.load_todo_list()
        self.chat_area.append(f"<b>System:</b> {response}")
    
    def save_chat_history(self):
        try:
            chat_history = self.chat_area.toPlainText()
            history_dir = os.path.join("Babes")
            os.makedirs(history_dir, exist_ok=True)
            
            history_path = os.path.join(history_dir, "chat_history.txt")
            
            try:
                with open(history_path, 'w', encoding='utf-8') as f:
                    f.write(chat_history)
            except PermissionError:
                alt_path = os.path.expanduser('~/Babes_chat_history.txt')
                with open(alt_path, 'w', encoding='utf-8') as f:
                    f.write(chat_history)
        except Exception as e:
            print(f"Error saving chat history: {e}")
    
    def load_chat_history(self):
        try:
            possible_paths = [
                os.path.join("Babes", "chat_history.txt"),
                os.path.expanduser("~/Babes_chat_history.txt"),
                os.path.join(os.environ.get("APPDATA", ""), "Babes", "chat_history.txt")
            ]
            
            for history_path in possible_paths:
                try:
                    os.makedirs(os.path.dirname(history_path), exist_ok=True)
                    
                    if os.path.exists(history_path):
                        with open(history_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content:
                                self.chat_area.setPlainText(content)
                        return
                except (PermissionError, OSError) as e:
                    print(f"Failed to load from {history_path}: {e}")
                    continue
            
            print("Chat history not found in any standard location")
        except Exception as e:
            print(f"Unexpected error loading chat history: {e}")

if __name__ == "__main__":
    # Create application instance
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    try:
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Handle application exit
        ret = app.exec_()
        sys.exit(ret)
        
    except Exception as e:
        # Show error message if initialization fails
        error_msg = QMessageBox()
        error_msg.setIcon(QMessageBox.Critical)
        error_msg.setWindowTitle("Initialization Error")
        error_msg.setText(f"Failed to initialize application: {str(e)}")
        error_msg.setDetailedText(traceback.format_exc())
        error_msg.exec_()
        sys.exit(1)