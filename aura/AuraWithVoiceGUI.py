import sys
import os
import threading
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget,
                             QMessageBox, QFrame, QLineEdit, QProgressBar)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QMovie
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize

# --- MODIFICATION: Import functions to find and update the .env file ---
from dotenv import find_dotenv, set_key

# Import our systems
# Ensure these paths are correct for your project structure
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from frontend.VoiceAuthGUI import VoiceAuthWorker
from frontend.GUI import GraphicalUserInterface
from backend.UnifiedVoiceAuth import UnifiedVoiceAuth

class AuraMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth = UnifiedVoiceAuth()
        self.is_authenticated = False
        self.authenticated_user = None
        self.initUI()
    
    # --- NEW METHOD: To update the .env file safely ---
    def update_env_username(self, username):
        """Finds the .env file and updates the Username variable."""
        try:
            # Find the .env file in the project directory
            dotenv_path = find_dotenv()
            if not dotenv_path:
                # If .env doesn't exist, create it in the current directory
                dotenv_path = os.path.join(os.getcwd(), '.env')
                print(f"Creating .env file at: {dotenv_path}")

            # Set the 'Username' key to the new value
            set_key(dotenv_path, "Username", username)
            print(f"✅ Successfully updated .env with Username: {username}")
        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
            QMessageBox.warning(self, "Error", f"Could not update the .env file: {e}")

    def initUI(self):
        """Initialize the main interface"""
        self.setWindowTitle("Aura AI - Voice Authenticated Assistant")
        self.setGeometry(100, 100, 1000, 700)
        
        self.setWindowIcon(QIcon("icons/logo.png"))
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2f; /* Dark blue-ish background */
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #00b377; /* Vibrant green */
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc88;
            }
            QPushButton:pressed {
                background-color: #009966;
            }
            QPushButton#BackButton {
                background-color: #3a3a4a;
                font-weight: normal;
            }
            QPushButton#BackButton:hover {
                background-color: #4a4a5a;
            }
            QLineEdit {
                background-color: #2c2c3c;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00b377;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 5px;
                text-align: center;
                color: white;
                background-color: #2c2c3c;
            }
            QProgressBar::chunk {
                background-color: #00b377;
                width: 10px; 
                margin: 0.5px;
            }
            QFrame#GroupFrame {
                background-color: #2c2c3c;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        header = self.create_header()
        main_layout.addWidget(header)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self.create_welcome_screen()
        self.create_voice_auth_screen()
        self.create_Aura_screen()
        
        self.stacked_widget.setCurrentIndex(0)
    
    def create_header(self):
        """Create the header section with logo"""
        header_frame = QFrame()
        header_frame.setFixedHeight(80)
        header_frame.setStyleSheet("background-color: #2a2a3a; border-bottom: 2px solid #00b377;")
        
        layout = QHBoxLayout(header_frame)
        layout.setContentsMargins(20, 0, 20, 0)
        
        logo_label = QLabel()
        pixmap = QPixmap("icons/logo.png")
        logo_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(logo_label)

        title = QLabel("Aura AI")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0; margin-left: 10px;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        self.header_status_label = QLabel("Not Authenticated")
        self.header_status_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.header_status_label)
        self.update_header_status("Not Authenticated")
        
        return header_frame
    
    def create_welcome_screen(self):
        """Create a more visually appealing welcome screen"""
        welcome_widget = QWidget()
        layout = QVBoxLayout(welcome_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        logo_label = QLabel()
        pixmap = QPixmap("icons/logo.png")
        logo_label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        welcome_label = QLabel("Welcome to Aura AI")
        welcome_label.setAlignment(Qt.AlignCenter)
        welcome_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        welcome_label.setStyleSheet("color: #00b377; margin-top: 20px;")
        layout.addWidget(welcome_label)
        
        desc_label = QLabel("Your personal assistant, secured by your voice.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setFont(QFont("Segoe UI", 16))
        desc_label.setStyleSheet("color: #cccccc; margin-bottom: 30px;")
        layout.addWidget(desc_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        self.voice_auth_btn = QPushButton("Authenticate / Register")
        self.voice_auth_btn.setMinimumHeight(50)
        self.voice_auth_btn.clicked.connect(self.show_voice_auth)
        button_layout.addWidget(self.voice_auth_btn)
        
        if self.auth.profiles:
            self.quick_start_btn = QPushButton("Quick Start")
            self.quick_start_btn.setMinimumHeight(50)
            self.quick_start_btn.setObjectName("BackButton")
            self.quick_start_btn.clicked.connect(self.quick_authenticate)
            button_layout.addWidget(self.quick_start_btn)
        
        layout.addLayout(button_layout)
        self.stacked_widget.addWidget(welcome_widget)
    
    def create_voice_auth_screen(self):
        """Create the voice authentication screen"""
        voice_auth_container = QWidget()
        container_layout = QVBoxLayout(voice_auth_container)
        container_layout.setContentsMargins(20, 10, 20, 20)

        back_button_layout = QHBoxLayout()
        self.back_to_welcome_btn = QPushButton("← Back")
        self.back_to_welcome_btn.setObjectName("BackButton")
        self.back_to_welcome_btn.setFixedWidth(120)
        self.back_to_welcome_btn.clicked.connect(self.show_welcome)
        back_button_layout.addWidget(self.back_to_welcome_btn)
        back_button_layout.addStretch()
        container_layout.addLayout(back_button_layout)

        self.voice_auth_widget = self.create_simple_voice_auth_widget()
        container_layout.addWidget(self.voice_auth_widget)
        
        self.stacked_widget.addWidget(voice_auth_container)
    
    def create_simple_voice_auth_widget(self):
        """Create a completely redesigned voice authentication widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        self.voice_gif_label = QLabel()
        self.movie = QMovie("gif/voice.gif")
        self.movie.setScaledSize(QSize(300, 300))
        self.voice_gif_label.setMovie(self.movie)
        self.voice_gif_label.setAlignment(Qt.AlignCenter)
        self.voice_gif_label.setVisible(False)
        layout.addWidget(self.voice_gif_label)
        
        self.voice_auth_status_label = QLabel("Please register your voice or authenticate.")
        self.voice_auth_status_label.setAlignment(Qt.AlignCenter)
        self.voice_auth_status_label.setFont(QFont("Segoe UI", 12))
        self.voice_auth_status_label.setWordWrap(True)
        self.voice_auth_status_label.setMinimumHeight(40)
        layout.addWidget(self.voice_auth_status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(400)
        layout.addWidget(self.progress_bar, 0, Qt.AlignCenter)
        
        reg_frame = QFrame()
        reg_frame.setObjectName("GroupFrame")
        reg_frame.setMaximumWidth(500)
        reg_layout = QVBoxLayout(reg_frame)
        reg_layout.addWidget(QLabel("New User Registration:"))
        
        reg_input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        reg_input_layout.addWidget(self.name_input)
        
        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.register_voice)
        reg_input_layout.addWidget(self.register_btn)
        
        reg_layout.addLayout(reg_input_layout)
        layout.addWidget(reg_frame, 0, Qt.AlignCenter)
        
        layout.addSpacing(20)
        
        auth_label = QLabel("Existing User Authentication:")
        auth_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(auth_label)
        
        self.auth_btn = QPushButton("Authenticate Voice")
        self.auth_btn.setMinimumHeight(50)
        self.auth_btn.setMaximumWidth(500)
        self.auth_btn.clicked.connect(self.authenticate_voice)
        layout.addWidget(self.auth_btn, 0, Qt.AlignCenter)
        
        layout.addStretch()
        return widget
    
    def register_voice(self):
        """Register voice profile"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Warning", "Please enter a name")
            return
        
        if name in self.auth.profiles:
            reply = QMessageBox.question(self, "Confirm", 
                                           f"Profile for {name} already exists. Overwrite?",
                                           QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        self.voice_gif_label.setVisible(True)
        self.movie.start()
        self.set_controls_enabled(False)

        self.register_worker = VoiceAuthWorker("register", self.auth, name)
        self.register_worker.status_update.connect(self.update_voice_auth_status)
        self.register_worker.progress_update.connect(self.update_progress)
        self.register_worker.operation_complete.connect(self.on_register_complete)
        self.register_worker.start()

    def authenticate_voice(self):
        """Authenticate voice"""
        if not self.auth.profiles:
            QMessageBox.warning(self, "Warning", "No voice profiles found. Please register first.")
            return
        
        self.voice_gif_label.setVisible(True)
        self.movie.start()
        self.set_controls_enabled(False)
        
        self.auth_worker = VoiceAuthWorker("authenticate", self.auth, None)
        self.auth_worker.status_update.connect(self.update_voice_auth_status)
        self.auth_worker.progress_update.connect(self.update_progress)
        self.auth_worker.operation_complete.connect(self.on_auth_complete)
        self.auth_worker.start()
    
    def update_voice_auth_status(self, message):
        """Update status label on the voice auth screen"""
        self.voice_auth_status_label.setText(message)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
    
    def on_register_complete(self, success, message):
        """Handle registration completion"""
        self.movie.stop()
        self.voice_gif_label.setVisible(False)
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.update_voice_auth_status("✅ " + message)
            QMessageBox.information(self, "Success", message)
        else:
            self.update_voice_auth_status("❌ " + message)
            QMessageBox.warning(self, "Error", message)
    
    def on_auth_complete(self, success, message):
        """Handle authentication completion"""
        self.movie.stop()
        self.voice_gif_label.setVisible(False)
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.update_voice_auth_status("✅ " + message)
            if "Authenticated as" in message:
                user_name = message.split("Authenticated as ")[1].split(" (")[0]
                self.is_authenticated = True
                self.authenticated_user = user_name

                # --- MODIFICATION: Update .env file on successful login ---
                self.update_env_username(self.authenticated_user)

                self.show_Aura()
        else:
            self.update_voice_auth_status("❌ " + message)
            QMessageBox.warning(self, "Authentication Failed", message)
    
    def set_controls_enabled(self, enabled):
        """Enable/disable controls during operations"""
        self.register_btn.setEnabled(enabled)
        self.auth_btn.setEnabled(enabled)
        self.name_input.setEnabled(enabled)
        self.back_to_welcome_btn.setEnabled(enabled)
    
    def create_Aura_screen(self):
        """Create the Aura main screen"""
        Aura_widget = QWidget()
        layout = QVBoxLayout(Aura_widget)
        layout.setAlignment(Qt.AlignCenter)
        
        success_label = QLabel("✅ Voice Authentication Successful!")
        success_label.setAlignment(Qt.AlignCenter)
        success_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        success_label.setStyleSheet("color: #00b377; margin: 20px;")
        layout.addWidget(success_label)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setAlignment(Qt.AlignCenter)
        self.user_info_label.setFont(QFont("Segoe UI", 14))
        self.user_info_label.setStyleSheet("color: #cccccc; margin: 10px;")
        layout.addWidget(self.user_info_label)
        
        self.launch_Aura_btn = QPushButton(" Launch Aura AI")
        self.launch_Aura_btn.setMinimumHeight(50)
        self.launch_Aura_btn.clicked.connect(self.launch_Aura)
        layout.addWidget(self.launch_Aura_btn)
        
        back_btn = QPushButton("← Back to Authentication")
        back_btn.setObjectName("BackButton")
        back_btn.clicked.connect(self.show_voice_auth)
        layout.addWidget(back_btn)
        
        self.stacked_widget.addWidget(Aura_widget)
    
    def show_welcome(self):
        """Show welcome screen"""
        self.stacked_widget.setCurrentIndex(0)
        self.update_header_status("Not Authenticated")
    
    def show_voice_auth(self):
        """Show voice authentication screen"""
        self.stacked_widget.setCurrentIndex(1)
        self.update_voice_auth_status("Ready for voice command.")
    
    def show_Aura(self):
        """Show Aura screen"""
        self.stacked_widget.setCurrentIndex(2)
        self.user_info_label.setText(f"Authenticated as: {self.authenticated_user}")
        self.update_header_status(f"Authenticated as {self.authenticated_user}")
    
    def quick_authenticate(self):
        """Quick authentication for existing users"""
        if not self.auth.profiles:
            QMessageBox.warning(self, "No Profiles", "No voice profiles found. Please register first.")
            return
        
        from PyQt5.QtWidgets import QInputDialog
        users = list(self.auth.profiles.keys())
        user, ok = QInputDialog.getItem(self, "Select User", "Choose your profile:", users, 0, False)
        
        if ok and user:
            self.authenticate_user(user)
    
    def authenticate_user(self, user_name):
        """Authenticate a specific user"""
        try:
            from PyQt5.QtWidgets import QProgressDialog
            progress = QProgressDialog("Authenticating voice...", "Cancel", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            QApplication.processEvents()

            result = self.auth.authenticate_voice(user_name)
            
            progress.close()
            
            if result:
                self.is_authenticated = True
                self.authenticated_user = user_name
                
                # --- MODIFICATION: Update .env file on successful login ---
                self.update_env_username(self.authenticated_user)
                
                self.show_Aura()
                QMessageBox.information(self, "Success", f"Voice authenticated for {user_name}!")
            else:
                QMessageBox.warning(self, "Authentication Failed", "Voice authentication failed. Please try again.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Authentication error: {str(e)}")
    
    def launch_Aura(self):
        """Launch the main Aura AI system"""
        if not self.is_authenticated:
            QMessageBox.warning(self, "Not Authenticated", "Please authenticate your voice first.")
            return
        
        self.close()
        
        try:
            import subprocess
            subprocess.Popen([sys.executable, "MainWithVoiceAuth.py"])
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch Aura: {str(e)}")
    
    def update_header_status(self, status):
        """Update the status label in the main header"""
        self.header_status_label.setText(status)
        if "Authenticated" in status:
            self.header_status_label.setStyleSheet("color: #00b377;")
        else:
            self.header_status_label.setStyleSheet("color: #ff6666;")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Aura AI Voice Authentication")
    app.setApplicationVersion("1.0")
    
    window = AuraMainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()