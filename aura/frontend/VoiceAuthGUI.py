import sys
import os
import threading
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
                             QProgressBar, QFrame, QGridLayout, QGroupBox)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QMovie, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize
from dotenv import dotenv_values

# Import our voice authentication system
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from backend.UnifiedVoiceAuth import UnifiedVoiceAuth

class VoiceAuthWorker(QThread):
    """Worker thread for voice operations"""
    status_update = pyqtSignal(str)
    progress_update = pyqtSignal(int)
    operation_complete = pyqtSignal(bool, str)
    
    def __init__(self, operation, auth, name=None):
        super().__init__()
        self.operation = operation
        self.auth = auth
        self.name = name
    
    def run(self):
        if self.operation == "register":
            self.register_voice()
        elif self.operation == "authenticate":
            self.authenticate_voice()
    
    def register_voice(self):
        """Register voice in background thread"""
        try:
            self.status_update.emit("Starting voice registration...")
            self.progress_update.emit(10)
            
            # Record samples
            samples = []
            audio_files = []
            num_samples = 3
            
            for i in range(num_samples):
                self.status_update.emit(f"Recording sample {i+1}/{num_samples}...")
                self.progress_update.emit(20 + (i * 20))
                
                # Record audio
                audio_file = self.auth.record_audio(f"{self.name}_sample_{i+1}")
                if not audio_file:
                    self.operation_complete.emit(False, f"Sample {i+1} recording failed")
                    return
                
                # Analyze audio
                features = self.auth.analyze_audio(audio_file)
                if not features:
                    self.operation_complete.emit(False, f"Sample {i+1} analysis failed")
                    return
                
                samples.append(features)
                audio_files.append(audio_file)
                self.status_update.emit(f"Sample {i+1} completed")
            
            # Save profile
            if len(samples) >= 2:
                avg_features = {}
                for key in samples[0].keys():
                    avg_features[key] = sum(s[key] for s in samples) / len(samples)
                
                profile = {
                    'name': self.name,
                    'features': avg_features,
                    'samples': len(samples),
                    'audio_files': audio_files,
                    'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'format': 'unified'
                }
                
                self.auth.profiles[self.name] = profile
                self.auth.save_profiles()
                
                self.progress_update.emit(100)
                self.status_update.emit("Registration completed successfully!")
                self.operation_complete.emit(True, f"Voice profile registered for {self.name}")
            else:
                self.operation_complete.emit(False, "Not enough valid samples")
                
        except Exception as e:
            self.operation_complete.emit(False, f"Registration error: {str(e)}")
    
    def authenticate_voice(self):
        """Authenticate voice in background thread"""
        try:
            self.status_update.emit("Starting voice authentication...")
            self.progress_update.emit(20)
            
            # Record test audio
            test_file = self.auth.record_audio("test_auth", duration=2)
            if not test_file:
                self.operation_complete.emit(False, "Failed to record test audio")
                return
            
            self.progress_update.emit(50)
            self.status_update.emit("Analyzing voice...")
            
            # Analyze test audio
            test_features = self.auth.analyze_audio(test_file)
            if not test_features:
                self.operation_complete.emit(False, "Failed to analyze test audio")
                return
            
            self.progress_update.emit(70)
            self.status_update.emit("Comparing with profiles...")
            
            # Authenticate
            if self.name and self.name in self.auth.profiles:
                # Check specific user
                profile_features = self.auth.profiles[self.name]['features']
                similarity = self.auth.calculate_similarity(test_features, profile_features)
                
                if similarity > self.auth.threshold:
                    self.progress_update.emit(100)
                    self.status_update.emit("Authentication successful!")
                    self.operation_complete.emit(True, f"Authenticated as {self.name} (Score: {similarity:.2f})")
                else:
                    self.operation_complete.emit(False, f"Authentication failed for {self.name} (Score: {similarity:.2f})")
            else:
                # Check all profiles
                best_match = None
                best_score = 0
                
                for profile_name, profile in self.auth.profiles.items():
                    similarity = self.auth.calculate_similarity(test_features, profile['features'])
                    if similarity > best_score:
                        best_score = similarity
                        best_match = profile_name
                
                if best_score > self.auth.threshold:
                    self.progress_update.emit(100)
                    self.status_update.emit("Authentication successful!")
                    self.operation_complete.emit(True, f"Authenticated as {best_match} (Score: {best_score:.2f})")
                else:
                    self.operation_complete.emit(False, f"Authentication failed (Best score: {best_score:.2f})")
                    
        except Exception as e:
            self.operation_complete.emit(False, f"Authentication error: {str(e)}")

class VoiceAuthGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.auth = UnifiedVoiceAuth()
        self.worker = None
        self.initUI()
        self.load_profiles()
    
    def initUI(self):
        """Initialize the user interface"""
        self.setWindowTitle("Aura AI - Voice Authentication")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2a2a2a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #00ff00;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #00ff00;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666;
                border-color: #333;
            }
            QLineEdit {
                background-color: #3a3a3a;
                border: 2px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #00ff00;
            }
            QListWidget {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 5px;
                color: white;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #00ff00;
                color: black;
            }
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2a2a2a;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #2a2a2a;
                border: 2px solid #555;
                border-radius: 5px;
                color: white;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Right panel - Status and Logs
        right_panel = self.create_status_panel()
        main_layout.addWidget(right_panel, 1)
    
    def create_control_panel(self):
        """Create the control panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("🎯 Voice Authentication")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #00ff00; margin: 10px;")
        layout.addWidget(title)
        
        # Registration Group
        reg_group = QGroupBox("Voice Registration")
        reg_layout = QVBoxLayout(reg_group)
        
        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your name...")
        reg_layout.addWidget(QLabel("Name:"))
        reg_layout.addWidget(self.name_input)
        
        # Register button
        self.register_btn = QPushButton("🎤 Register Voice")
        self.register_btn.clicked.connect(self.register_voice)
        reg_layout.addWidget(self.register_btn)
        
        layout.addWidget(reg_group)
        
        # Authentication Group
        auth_group = QGroupBox("Voice Authentication")
        auth_layout = QVBoxLayout(auth_group)
        
        # User selection
        self.user_list = QListWidget()
        self.user_list.setMaximumHeight(100)
        auth_layout.addWidget(QLabel("Select User (or leave empty for auto-detect):"))
        auth_layout.addWidget(self.user_list)
        
        # Authenticate button
        self.auth_btn = QPushButton("🔐 Authenticate Voice")
        self.auth_btn.clicked.connect(self.authenticate_voice)
        auth_layout.addWidget(self.auth_btn)
        
        layout.addWidget(auth_group)
        
        # Management Group
        mgmt_group = QGroupBox("Profile Management")
        mgmt_layout = QVBoxLayout(mgmt_group)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete Selected Profile")
        self.delete_btn.clicked.connect(self.delete_profile)
        mgmt_layout.addWidget(self.delete_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh Profiles")
        self.refresh_btn.clicked.connect(self.load_profiles)
        mgmt_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(mgmt_group)
        
        # Spacer
        layout.addStretch()
        
        return panel
    
    def create_status_panel(self):
        """Create the status panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title = QLabel("📊 Status & Logs")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #00ff00; margin: 10px;")
        layout.addWidget(title)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #00ff00; font-size: 14px; padding: 10px;")
        layout.addWidget(self.status_label)
        
        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        layout.addWidget(QLabel("Activity Log:"))
        layout.addWidget(self.log_area)
        
        # Profiles list
        self.profiles_list = QListWidget()
        layout.addWidget(QLabel("Registered Profiles:"))
        layout.addWidget(self.profiles_list)
        
        return panel
    
    def load_profiles(self):
        """Load and display profiles"""
        self.user_list.clear()
        self.profiles_list.clear()
        
        if self.auth.profiles:
            for name, profile in self.auth.profiles.items():
                # Add to user selection list
                item = QListWidgetItem(name)
                self.user_list.addItem(item)
                
                # Add to profiles display
                created = profile.get('created_at', 'Unknown')
                samples = profile.get('samples', 0)
                format_type = profile.get('format', 'unknown')
                profile_text = f"{name} - {samples} samples ({format_type}) - {created}"
                profile_item = QListWidgetItem(profile_text)
                self.profiles_list.addItem(profile_item)
            
            self.log_message(f"Loaded {len(self.auth.profiles)} voice profiles")
        else:
            self.log_message("No voice profiles found")
    
    def register_voice(self):
        """Start voice registration"""
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
        
        # Disable controls
        self.set_controls_enabled(False)
        
        # Start worker thread
        self.worker = VoiceAuthWorker("register", self.auth, name)
        self.worker.status_update.connect(self.update_status)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.operation_complete.connect(self.on_operation_complete)
        self.worker.start()
        
        self.log_message(f"Starting voice registration for {name}...")
    
    def authenticate_voice(self):
        """Start voice authentication"""
        if not self.auth.profiles:
            QMessageBox.warning(self, "Warning", "No voice profiles found. Please register first.")
            return
        
        # Get selected user
        selected_items = self.user_list.selectedItems()
        name = selected_items[0].text() if selected_items else None
        
        # Disable controls
        self.set_controls_enabled(False)
        
        # Start worker thread
        self.worker = VoiceAuthWorker("authenticate", self.auth, name)
        self.worker.status_update.connect(self.update_status)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.operation_complete.connect(self.on_operation_complete)
        self.worker.start()
        
        self.log_message(f"Starting voice authentication{' for ' + name if name else ''}...")
    
    def delete_profile(self):
        """Delete selected profile"""
        selected_items = self.profiles_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a profile to delete")
            return
        
        # Extract name from profile text
        profile_text = selected_items[0].text()
        name = profile_text.split(' - ')[0]
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete {name}'s profile?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.auth.delete_profile(name)
            self.load_profiles()
            self.log_message(f"Deleted profile for {name}")
    
    def update_status(self, message):
        """Update status label"""
        self.status_label.setText(message)
        self.log_message(message)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(True)
    
    def on_operation_complete(self, success, message):
        """Handle operation completion"""
        self.set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ " + message)
            self.status_label.setStyleSheet("color: #00ff00; font-size: 14px; padding: 10px;")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("❌ " + message)
            self.status_label.setStyleSheet("color: #ff0000; font-size: 14px; padding: 10px;")
            QMessageBox.warning(self, "Error", message)
        
        self.log_message(message)
        self.load_profiles()
    
    def set_controls_enabled(self, enabled):
        """Enable/disable controls"""
        self.register_btn.setEnabled(enabled)
        self.auth_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)
        self.refresh_btn.setEnabled(enabled)
        self.name_input.setEnabled(enabled)
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.append(f"[{timestamp}] {message}")
        self.log_area.ensureCursorVisible()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Aura AI Voice Authentication")
    app.setApplicationVersion("1.0")
    
    # Create and show window
    window = VoiceAuthGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
