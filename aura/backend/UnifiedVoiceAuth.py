import os
import json
import wave
import pyaudio
import numpy as np
from datetime import datetime
import threading
import time

class UnifiedVoiceAuth:
    def __init__(self):
        self.voice_data_dir = "data/voice_profiles"
        self.profiles_file = "data/voice_profiles.json"
        self.sample_rate = 16000
        self.duration = 2
        self.chunk_size = 1024
        self.threshold = 0.6  # Similarity threshold
        
        # Create directories
        os.makedirs(self.voice_data_dir, exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Load profiles
        self.profiles = self.load_profiles()
    
    def load_profiles(self):
        """Load voice profiles with full compatibility"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    profiles = json.load(f)
                
                # Convert any format to unified format
                unified_profiles = {}
                for name, profile in profiles.items():
                    unified_profiles[name] = self.convert_to_unified_format(name, profile)
                
                return unified_profiles
            except Exception as e:
                print(f"Error loading profiles: {e}")
                return {}
        return {}
    
    def convert_to_unified_format(self, name, profile):
        """Convert any profile format to unified format"""
        if 'features' in profile and isinstance(profile['features'], list):
            # Old complex format - extract basic features
            features = profile['features']
            return {
                'name': name,
                'features': {
                    'mean_amplitude': abs(features[0]) if len(features) > 0 else 1000,
                    'max_amplitude': abs(features[1]) if len(features) > 1 else 2000,
                    'std_amplitude': abs(features[2]) if len(features) > 2 else 500,
                    'zero_crossings': int(abs(features[3])) if len(features) > 3 else 100,
                    'duration': 3.0
                },
                'samples': profile.get('num_samples', 3),
                'audio_files': profile.get('sample_files', []),
                'created_at': profile.get('created_at', 'Unknown'),
                'format': 'converted'
            }
        elif 'features' in profile and isinstance(profile['features'], dict):
            # New simple format
            return {
                'name': name,
                'features': profile['features'],
                'samples': profile.get('samples', 3),
                'audio_files': profile.get('audio_files', []),
                'created_at': profile.get('created_at', 'Unknown'),
                'format': 'simple'
            }
        else:
            # Unknown format - create default
            return {
                'name': name,
                'features': {
                    'mean_amplitude': 1000,
                    'max_amplitude': 2000,
                    'std_amplitude': 500,
                    'zero_crossings': 100,
                    'duration': 3.0
                },
                'samples': 3,
                'audio_files': [],
                'created_at': 'Unknown',
                'format': 'default'
            }
    
    def save_profiles(self):
        """Save profiles in unified format"""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=4)
    
    def record_audio(self, filename, duration=None):
        """Record audio to file"""
        if duration is None:
            duration = self.duration
        
        print(f"🎤 Recording for {duration} seconds...")
        print("🔴 Speak now!")
        
        try:
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            for i in range(0, int(self.sample_rate / self.chunk_size * duration)):
                data = stream.read(self.chunk_size)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            filepath = os.path.join(self.voice_data_dir, f"{filename}.wav")
            with wave.open(filepath, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
            
            print("✅ Recording complete!")
            return filepath
            
        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None
    
    def analyze_audio(self, filepath):
        """Analyze audio file"""
        try:
            with wave.open(filepath, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)
                
                if len(audio_data) == 0:
                    return None
                
                features = {
                    'mean_amplitude': float(np.mean(np.abs(audio_data))),
                    'max_amplitude': float(np.max(np.abs(audio_data))),
                    'std_amplitude': float(np.std(audio_data)),
                    'zero_crossings': int(np.sum(np.diff(np.sign(audio_data)) != 0)),
                    'duration': len(audio_data) / self.sample_rate
                }
                
                return features
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return None
    
    def register_voice(self, name, num_samples=3):
        """Register voice profile"""
        print(f"🎯 Registering voice for {name}")
        
        samples = []
        audio_files = []
        
        for i in range(num_samples):
            print(f"\n--- Sample {i+1}/{num_samples} ---")
            
            audio_file = self.record_audio(f"{name}_sample_{i+1}")
            if not audio_file:
                print(f"❌ Sample {i+1} failed")
                continue
            
            features = self.analyze_audio(audio_file)
            if not features:
                print(f"❌ Analysis failed for sample {i+1}")
                continue
            
            samples.append(features)
            audio_files.append(audio_file)
            print(f"✅ Sample {i+1} recorded and analyzed")
        
        if len(samples) >= 2:
            # Calculate average features
            avg_features = {}
            for key in samples[0].keys():
                avg_features[key] = np.mean([s[key] for s in samples])
            
            # Save profile
            profile = {
                'name': name,
                'features': avg_features,
                'samples': len(samples),
                'audio_files': audio_files,
                'created_at': datetime.now().isoformat(),
                'format': 'unified'
            }
            
            self.profiles[name] = profile
            self.save_profiles()
            
            print(f"✅ Voice profile registered for {name}")
            return True
        else:
            print("❌ Not enough valid samples")
            return False
    
    def authenticate_voice(self, name=None):
        """Authenticate voice"""
        if not self.profiles:
            print("❌ No profiles found")
            return False
        
        print("🎤 Please speak for authentication...")
        
        test_file = self.record_audio("test_auth", duration=2)
        if not test_file:
            return False
        
        test_features = self.analyze_audio(test_file)
        if not test_features:
            return False
        
        if name and name in self.profiles:
            # Check specific user
            profile_features = self.profiles[name]['features']
            similarity = self.calculate_similarity(test_features, profile_features)
            
            if similarity > self.threshold:
                print(f"✅ Authenticated as {name} (Similarity: {similarity:.2f})")
                return True
            else:
                print(f"❌ Authentication failed for {name} (Similarity: {similarity:.2f})")
                return False
        else:
            # Check all profiles
            best_match = None
            best_score = 0
            
            for profile_name, profile in self.profiles.items():
                similarity = self.calculate_similarity(test_features, profile['features'])
                if similarity > best_score:
                    best_score = similarity
                    best_match = profile_name
            
            if best_score > self.threshold:
                print(f"✅ Authenticated as {best_match} (Similarity: {best_score:.2f})")
                return best_match
            else:
                print(f"❌ Authentication failed (Best score: {best_score:.2f})")
                return False
    
    def calculate_similarity(self, features1, features2):
        """Calculate similarity between feature sets"""
        try:
            similarities = []
            
            for key in features1.keys():
                if key in features2:
                    val1 = features1[key]
                    val2 = features2[key]
                    
                    if val1 == 0 and val2 == 0:
                        similarity = 1.0
                    elif val1 == 0 or val2 == 0:
                        similarity = 0.0
                    else:
                        # Calculate relative similarity
                        similarity = 1.0 - abs(val1 - val2) / max(val1, val2)
                        similarity = max(0.0, min(1.0, similarity))
                    
                    similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            print(f"❌ Similarity calculation error: {e}")
            return 0.0
    
    def list_profiles(self):
        """List all profiles"""
        if not self.profiles:
            print("📝 No profiles found")
            return
        
        print("👥 Registered Profiles:")
        for name, profile in self.profiles.items():
            created = profile.get('created_at', 'Unknown')
            samples = profile.get('samples', 0)
            format_type = profile.get('format', 'unknown')
            print(f"  • {name} - {samples} samples ({format_type}) (Created: {created})")
    
    def delete_profile(self, name):
        """Delete a profile"""
        if name in self.profiles:
            # Delete audio files
            for audio_file in self.profiles[name].get('audio_files', []):
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            del self.profiles[name]
            self.save_profiles()
            print(f"✅ Profile deleted for {name}")
        else:
            print(f"❌ Profile not found: {name}")

# Test the system
if __name__ == "__main__":
    auth = UnifiedVoiceAuth()
    
    while True:
        print("\n🎯 Unified Voice Authentication")
        print("1. Register voice")
        print("2. Authenticate voice")
        print("3. List profiles")
        print("4. Delete profile")
        print("5. Exit")
        
        choice = input("Choice (1-5): ").strip()
        
        if choice == "1":
            name = input("Enter name: ").strip()
            if name:
                auth.register_voice(name)
        
        elif choice == "2":
            name = input("Enter name (or press Enter for auto-detect): ").strip()
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
            print("❌ Invalid choice")
