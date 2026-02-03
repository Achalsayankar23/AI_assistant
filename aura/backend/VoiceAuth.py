import os
import json
import numpy as np
import librosa
import soundfile as sf
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime
import threading
import time

class VoiceAuthentication:
    def __init__(self):
        self.voice_data_dir = "data/voice_profiles"
        self.profiles_file = "data/voice_profiles.json"
        self.model_file = "data/voice_model.pkl"
        self.sample_rate = 22050
        self.duration = 3  # seconds for voice samples
        self.threshold = 0.7  # similarity threshold
        
        # Create directories if they don't exist
        os.makedirs(self.voice_data_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Load existing profiles
        self.profiles = self.load_profiles()
        self.scaler = StandardScaler()
        
    def load_profiles(self):
        """Load existing voice profiles from file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_profiles(self):
        """Save voice profiles to file"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=4)
    
    def extract_features(self, audio_data):
        """Extract MFCC features from audio data"""
        try:
            # Ensure audio data is not empty
            if len(audio_data) == 0:
                print("Warning: Empty audio data")
                return None
            
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=audio_data, sr=self.sample_rate, n_mfcc=13)
            
            # Extract additional features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)
            
            # Ensure all features have the same dimensions by taking means
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            spectral_centroids_mean = np.mean(spectral_centroids)
            spectral_rolloff_mean = np.mean(spectral_rolloff)
            zero_crossing_rate_mean = np.mean(zero_crossing_rate)
            
            # Combine features - ensure all are 1D arrays
            features = np.concatenate([
                mfcc_mean.flatten(),
                mfcc_std.flatten(),
                [spectral_centroids_mean],
                [spectral_rolloff_mean],
                [zero_crossing_rate_mean]
            ])
            
            return features
        except Exception as e:
            print(f"Error extracting features: {e}")
            return None
    
    def record_voice_sample(self, sample_name, duration=None):
        """Record a voice sample for training"""
        if duration is None:
            duration = self.duration
            
        print(f"🎤 Recording voice sample '{sample_name}' for {duration} seconds...")
        print("Please speak clearly when you see the prompt...")
        
        try:
            import pyaudio
            import wave
            
            # Audio recording parameters
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = self.sample_rate
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open stream
            stream = p.open(format=format,
                          channels=channels,
                          rate=rate,
                          input=True,
                          frames_per_buffer=chunk)
            
            print("🔴 Recording... Speak now!")
            frames = []
            
            # Record for specified duration
            for i in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)
            
            print("✅ Recording complete!")
            
            # Stop and close stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # Save audio file
            audio_file = os.path.join(self.voice_data_dir, f"{sample_name}.wav")
            with wave.open(audio_file, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(p.get_sample_size(format))
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))
            
            # Load and process the audio
            try:
                audio_data, _ = librosa.load(audio_file, sr=self.sample_rate)
                print(f"Audio loaded: {len(audio_data)} samples, {len(audio_data)/self.sample_rate:.2f} seconds")
                
                # Check if audio has enough data
                if len(audio_data) < self.sample_rate * 0.5:  # At least 0.5 seconds
                    print("Warning: Audio too short, may not be enough for feature extraction")
                
                features = self.extract_features(audio_data)
                
                if features is not None:
                    print(f"Features extracted successfully: {len(features)} dimensions")
                    return features, audio_file
                else:
                    print("Failed to extract features from audio")
                    return None, None
            except Exception as e:
                print(f"Error processing audio file: {e}")
                return None, None
                
        except ImportError:
            print("❌ PyAudio not installed. Installing...")
            os.system("pip install pyaudio")
            return self.record_voice_sample(sample_name, duration)
        except Exception as e:
            print(f"❌ Error recording voice sample: {e}")
            return None, None
    
    def register_voice(self, user_name, num_samples=3):
        """Register a new voice profile"""
        print(f"🎯 Registering voice for user: {user_name}")
        print(f"📝 We need {num_samples} voice samples for better accuracy")
        
        features_list = []
        audio_files = []
        
        for i in range(num_samples):
            print(f"\n--- Sample {i+1}/{num_samples} ---")
            features, audio_file = self.record_voice_sample(f"{user_name}_sample_{i+1}")
            
            if features is not None:
                features_list.append(features)
                audio_files.append(audio_file)
                print(f"✅ Sample {i+1} recorded successfully")
            else:
                print(f"❌ Sample {i+1} failed")
                return False
        
        if len(features_list) >= 2:  # Need at least 2 samples
            # Calculate average features
            avg_features = np.mean(features_list, axis=0)
            
            # Save profile
            profile = {
                "user_name": user_name,
                "features": avg_features.tolist(),
                "sample_files": audio_files,
                "created_at": datetime.now().isoformat(),
                "num_samples": len(features_list)
            }
            
            self.profiles[user_name] = profile
            self.save_profiles()
            
            print(f"✅ Voice profile registered successfully for {user_name}")
            print(f"📊 Features extracted: {len(avg_features)} dimensions")
            return True
        else:
            print("❌ Not enough valid samples for registration")
            return False
    
    def authenticate_voice(self, user_name=None):
        """Authenticate voice against registered profiles"""
        if not self.profiles:
            print("❌ No voice profiles found. Please register first.")
            return False
        
        print("🎤 Please speak for voice authentication...")
        features, _ = self.record_voice_sample("auth_temp", duration=2)
        
        if features is None:
            print("❌ Failed to extract voice features")
            return False
        
        best_match = None
        best_score = 0
        
        if user_name and user_name in self.profiles:
            # Authenticate against specific user
            profile_features = np.array(self.profiles[user_name]["features"])
            similarity = cosine_similarity([features], [profile_features])[0][0]
            
            if similarity >= self.threshold:
                print(f"✅ Voice authenticated for {user_name} (Score: {similarity:.3f})")
                return True
            else:
                print(f"❌ Voice authentication failed for {user_name} (Score: {similarity:.3f})")
                return False
        else:
            # Authenticate against all profiles
            for name, profile in self.profiles.items():
                profile_features = np.array(profile["features"])
                similarity = cosine_similarity([features], [profile_features])[0][0]
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = name
            
            if best_score >= self.threshold:
                print(f"✅ Voice authenticated as {best_match} (Score: {best_score:.3f})")
                return best_match
            else:
                print(f"❌ Voice authentication failed (Best score: {best_score:.3f})")
                return False
    
    def list_profiles(self):
        """List all registered voice profiles"""
        if not self.profiles:
            print("📝 No voice profiles registered")
            return
        
        print("👥 Registered Voice Profiles:")
        for name, profile in self.profiles.items():
            created = profile.get("created_at", "Unknown")
            samples = profile.get("num_samples", 0)
            print(f"  • {name} - {samples} samples (Created: {created})")
    
    def delete_profile(self, user_name):
        """Delete a voice profile"""
        if user_name in self.profiles:
            # Delete audio files
            for audio_file in self.profiles[user_name].get("sample_files", []):
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            # Remove from profiles
            del self.profiles[user_name]
            self.save_profiles()
            print(f"✅ Voice profile deleted for {user_name}")
        else:
            print(f"❌ Profile not found for {user_name}")

# Voice activation phrases
ACTIVATION_PHRASES = [
    "hey Aura",
    "Aura",
    "wake up Aura",
    "start Aura",
    "activate Aura"
]

def check_activation_phrase(text):
    """Check if the spoken text contains activation phrases"""
    text_lower = text.lower().strip()
    return any(phrase in text_lower for phrase in ACTIVATION_PHRASES)

# Example usage
if __name__ == "__main__":
    auth = VoiceAuthentication()
    
    while True:
        print("\n🎯 Voice Authentication System")
        print("1. Register new voice")
        print("2. Authenticate voice")
        print("3. List profiles")
        print("4. Delete profile")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            name = input("Enter your name: ").strip()
            if name:
                auth.register_voice(name)
        
        elif choice == "2":
            name = input("Enter your name (or press Enter for auto-detect): ").strip()
            if name:
                auth.authenticate_voice(name)
            else:
                auth.authenticate_voice()
        
        elif choice == "3":
            auth.list_profiles()
        
        elif choice == "4":
            name = input("Enter name to delete: ").strip()
            if name:
                auth.delete_profile(name)
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")
