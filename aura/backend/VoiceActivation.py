import os
import time
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from backend.VoiceAuth import VoiceAuthentication, check_activation_phrase
import mtranslate as mt
from dotenv import dotenv_values

class VoiceActivationSystem:
    def __init__(self):
        self.auth = VoiceAuthentication()
        self.is_activated = False
        self.authenticated_user = None
        self.driver = None
        self.listening = False
        
        # Load environment variables
        env_vars = dotenv_values(".env")
        self.input_language = env_vars.get("InputLanguage", "en-US")
        
        # HTML for continuous listening
        self.html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Voice Activation</title>
</head>
<body>
    <div id="status">Listening for activation...</div>
    <div id="output"></div>
    <script>
        const status = document.getElementById('status');
        const output = document.getElementById('output');
        let recognition;
        let isListening = false;

        function startRecognition() {
            if (isListening) return;
            
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = 'en-US';
            recognition.continuous = true;
            recognition.interimResults = true;

            recognition.onstart = function() {
                isListening = true;
                status.textContent = 'Listening for activation...';
            };

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent = transcript;
                
                // Check for activation phrases
                if (transcript.toLowerCase().includes('Aura') || 
                    transcript.toLowerCase().includes('hey Aura')) {
                    status.textContent = 'ACTIVATED!';
                    status.style.color = 'green';
                    status.style.fontWeight = 'bold';
                }
            };

            recognition.onerror = function(event) {
                console.log('Recognition error:', event.error);
                isListening = false;
                setTimeout(startRecognition, 1000);
            };

            recognition.onend = function() {
                isListening = false;
                setTimeout(startRecognition, 1000);
            };

            recognition.start();
        }

        // Start recognition when page loads
        window.onload = function() {
            startRecognition();
        };
    </script>
</body>
</html>'''
        
        self.setup_chrome()
    
    def setup_chrome(self):
        """Setup Chrome driver for voice recognition"""
        try:
            # Write HTML file
            os.makedirs("data", exist_ok=True)
            with open("data/VoiceActivation.html", "w", encoding='utf-8') as f:
                f.write(self.html_code)
            
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--use-fake-ui-for-media-stream")
            chrome_options.add_argument("--use-fake-device-for-media-stream")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.media_stream_mic": 1
            })
            
            # Try to initialize driver with better error handling
            try:
                service = ChromeDriverManager().install()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ Chrome driver initialized successfully")
            except Exception as driver_error:
                print(f"⚠️ ChromeDriverManager failed: {driver_error}")
                print("🔄 Trying alternative Chrome setup...")
                
                # Try with system Chrome
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    print("✅ Chrome driver initialized with system Chrome")
                except Exception as system_error:
                    print(f"❌ System Chrome failed: {system_error}")
                    raise Exception("Could not initialize Chrome driver")
            
            # Load the HTML page
            current_dir = os.getcwd()
            link = f"file:///{current_dir}/data/VoiceActivation.html"
            self.driver.get(link)
            print("✅ Voice activation page loaded")
            
        except Exception as e:
            print(f"❌ Error setting up Chrome: {e}")
            print("💡 Please ensure Chrome browser is installed and up to date")
            return False
        return True
    
    def start_voice_activation(self):
        """Start the voice activation system"""
        print("🎯 Starting Voice Activation System...")
        
        # Check if user is registered
        if not self.auth.profiles:
            print("📝 No voice profiles found. Starting registration...")
            self.register_new_user()
        
        # Check if Chrome setup was successful
        if not self.driver:
            print("⚠️ Chrome driver not available. Voice activation disabled.")
            print("💡 You can still use Aura with manual activation.")
            return False
        
        # Start listening for activation
        self.listening = True
        print("🎤 Listening for 'Hey Aura' or 'Aura'...")
        
        # Start the listening loop in a separate thread
        activation_thread = threading.Thread(target=self._listen_for_activation)
        activation_thread.daemon = True
        activation_thread.start()
        
        return True
    
    def _listen_for_activation(self):
        """Listen for activation phrase in background thread"""
        while self.listening:
            try:
                # Check for activation phrase
                if self.driver:
                    try:
                        output_element = self.driver.find_element(By.ID, "output")
                        status_element = self.driver.find_element(By.ID, "status")
                        
                        current_text = output_element.text.strip()
                        status_text = status_element.text.strip()
                        
                        if current_text and check_activation_phrase(current_text):
                            print(f"🔊 Activation phrase detected: '{current_text}'")
                            
                            # Authenticate user
                            print("🔐 Authenticating voice...")
                            auth_result = self.auth.authenticate_voice()
                            
                            if auth_result:
                                self.authenticated_user = auth_result if isinstance(auth_result, str) else "User"
                                self.is_activated = True
                                print(f"✅ Aura activated for {self.authenticated_user}!")
                                return True
                            else:
                                print("❌ Voice authentication failed. Access denied.")
                                time.sleep(2)  # Wait before trying again
                        
                        # Clear output after processing
                        if current_text:
                            self.driver.execute_script("document.getElementById('output').textContent = '';")
                            
                    except Exception as e:
                        # Element not found or other error, continue listening
                        pass
                
                time.sleep(0.5)  # Check every 500ms
                
            except KeyboardInterrupt:
                print("\n🛑 Voice activation stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in voice activation: {e}")
                time.sleep(1)
        
        return False
    
    def register_new_user(self):
        """Register a new user for voice authentication"""
        print("\n🎯 Voice Registration Required")
        print("To use Aura, you need to register your voice first.")
        
        while True:
            name = input("Enter your name: ").strip()
            if name:
                break
            print("❌ Please enter a valid name")
        
        print(f"\n📝 Registering voice for {name}...")
        print("You'll need to speak 3 times for better accuracy.")
        
        success = self.auth.register_voice(name)
        if success:
            print(f"✅ Voice registration successful for {name}!")
            print("You can now use voice activation.")
        else:
            print("❌ Voice registration failed. Please try again.")
            return False
        
        return True
    
    def stop_activation(self):
        """Stop the voice activation system"""
        self.listening = False
        if self.driver:
            self.driver.quit()
        print("🛑 Voice activation system stopped")
    
    def is_Aura_activated(self):
        """Check if Aura is currently activated"""
        return self.is_activated
    
    def get_authenticated_user(self):
        """Get the name of the authenticated user"""
        return self.authenticated_user
    
    def reset_activation(self):
        """Reset activation state (for logout)"""
        self.is_activated = False
        self.authenticated_user = None
        print("🔄 Aura activation reset")

# Integration with main Aura system
def integrate_voice_activation():
    """Integrate voice activation with the main Aura system"""
    activation_system = VoiceActivationSystem()
    
    try:
        # Start voice activation
        if activation_system.start_voice_activation():
            print("🚀 Aura is now ready to use!")
            return activation_system
        else:
            print("❌ Failed to activate Aura")
            return None
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        activation_system.stop_activation()
        return None
    except Exception as e:
        print(f"❌ Error in voice activation: {e}")
        activation_system.stop_activation()
        return None

if __name__ == "__main__":
    # Test the voice activation system
    activation_system = integrate_voice_activation()
    
    if activation_system and activation_system.is_Aura_activated():
        print(f"✅ Aura activated for {activation_system.get_authenticated_user()}")
        print("🎤 You can now use voice commands!")
        
        # Keep the system running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
            activation_system.stop_activation()
    else:
        print("❌ Voice activation failed")
