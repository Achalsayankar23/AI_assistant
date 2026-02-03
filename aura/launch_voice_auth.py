#!/usr/bin/env python3
"""
Aura AI Voice Authentication Launcher
Easy launcher for the voice authentication GUI
"""

import sys
import os

def main():
    print("🚀 Launching Aura AI Voice Authentication GUI...")
    
    try:
        # Import and run the GUI
        from AuraWithVoiceGUI import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Please make sure all dependencies are installed:")
        print("pip install PyQt5 pyaudio librosa soundfile scikit-learn")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your installation and try again.")

if __name__ == "__main__":
    main()
