#!/usr/bin/env python3
"""
Unified Voice Authentication Setup for Aura AI
This system is compatible with all previous voice profile formats
"""

import os
import sys
from backend.UnifiedVoiceAuth import UnifiedVoiceAuth

def main():
    print("🎯 Aura AI - Unified Voice Authentication Setup")
    print("=" * 55)
    print("✅ Compatible with all previous voice profiles")
    
    # Initialize voice authentication
    auth = UnifiedVoiceAuth()
    
    # Show current profiles
    if auth.profiles:
        print("\n📋 Current Profiles:")
        auth.list_profiles()
    
    while True:
        print("\n📋 Voice Authentication Menu:")
        print("1. Register new voice profile")
        print("2. Test voice authentication")
        print("3. List registered profiles")
        print("4. Delete voice profile")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == "1":
            register_voice_profile(auth)
        elif choice == "2":
            test_voice_authentication(auth)
        elif choice == "3":
            auth.list_profiles()
        elif choice == "4":
            delete_voice_profile(auth)
        elif choice == "5":
            print("👋 Setup complete! You can now use voice authentication.")
            break
        else:
            print("❌ Invalid choice. Please try again.")

def register_voice_profile(auth):
    """Register a new voice profile"""
    print("\n🎤 Voice Profile Registration")
    print("-" * 30)
    
    name = input("Enter your name: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return
    
    if name in auth.profiles:
        overwrite = input(f"Profile for {name} already exists. Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Registration cancelled.")
            return
    
    print(f"\n📝 Registering voice for {name}...")
    print("You'll need to speak 3 times for better accuracy.")
    print("Make sure you're in a quiet environment.")
    print("Speak clearly and at normal volume.")
    
    confirm = input("Ready to start? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Registration cancelled.")
        return
    
    success = auth.register_voice(name)
    if success:
        print(f"✅ Voice profile registered successfully for {name}!")
        print("You can now use voice authentication.")
    else:
        print("❌ Voice registration failed. Please try again.")

def test_voice_authentication(auth):
    """Test voice authentication"""
    print("\n🔐 Voice Authentication Test")
    print("-" * 30)
    
    if not auth.profiles:
        print("❌ No voice profiles found. Please register first.")
        return
    
    print("Available profiles:")
    auth.list_profiles()
    
    name = input("\nEnter your name (or press Enter for auto-detect): ").strip()
    
    print("\n🎤 Please speak for authentication...")
    print("You have 2 seconds to speak clearly.")
    
    if name:
        result = auth.authenticate_voice(name)
        if result:
            print(f"✅ Authentication successful for {name}!")
        else:
            print(f"❌ Authentication failed for {name}")
    else:
        result = auth.authenticate_voice()
        if result:
            print(f"✅ Authentication successful! Identified as: {result}")
        else:
            print("❌ Authentication failed")

def delete_voice_profile(auth):
    """Delete a voice profile"""
    print("\n🗑️ Delete Voice Profile")
    print("-" * 25)
    
    if not auth.profiles:
        print("❌ No voice profiles found.")
        return
    
    print("Available profiles:")
    auth.list_profiles()
    
    name = input("\nEnter name to delete: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return
    
    if name not in auth.profiles:
        print(f"❌ Profile not found for {name}")
        return
    
    confirm = input(f"Are you sure you want to delete {name}'s profile? (y/n): ").strip().lower()
    if confirm == 'y':
        auth.delete_profile(name)
    else:
        print("Deletion cancelled.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please make sure PyAudio is installed:")
        print("pip install pyaudio")
