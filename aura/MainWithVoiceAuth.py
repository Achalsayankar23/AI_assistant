import subprocess
import threading
import os
import json
from asyncio import run
from time import sleep

from dotenv import dotenv_values

from frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,
    TempDirectoryPath,
    SetMicrophoneStatus,
    AnswerModifier,
    QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

from backend.Automation import Automation
from backend.SpeechToText import SpeechRecognition
from backend.TextToSpeech import TextToSpeech
from backend.Chatbot import ChatBot
from backend.Model import FirstLayerDMM
from backend.RealtimeSearchEngine import RealtimeSearchEngine
from backend.VoiceActivation import VoiceActivationSystem

# Load assistant settings
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Assistant")

# Set default messages
DefaultMessage = f"""{Username} : Hello {Assistantname}, How are you?
{Assistantname} : Welcome {Username}, I am doing well. How may I help you?"""

subprocesses = []  # Hold subprocess references if needed
Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]

# Voice activation system
voice_activation = None
Aura_activated = False

def ShowDefaultChatIfNoChats():
    if not os.path.exists('data/ChatLog.json'):
        return
    with open('data/ChatLog.json', 'r', encoding='utf-8') as file:
        if len(file.read()) <= 5:
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as f:
                f.write(DefaultMessage)
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as f:
                f.write(DefaultMessage)

def ReadChatLogJson():
    with open('data/ChatLog.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def ChatLogIntegration():
    json_data = ReadChatLogJson()
    formatted_chatlog = ""
    for entry in json_data:
        if entry["role"] == "user":
            formatted_chatlog += f"{Username} : {entry['content']}\n"
        elif entry["role"] == "assistant":
            formatted_chatlog += f"{Assistantname} : {entry['content']}\n"

    with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as f:
        f.write(AnswerModifier(formatted_chatlog))

def ShowChatsOnGUI():
    with open(TempDirectoryPath('Database.data'), "r", encoding='utf-8') as file:
        data = file.read()
    if data:
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as f:
            f.write(data)

def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()

def VoiceActivationThread():
    """Thread for voice activation system"""
    global voice_activation, Aura_activated
    
    print("🎯 Starting Voice Activation System...")
    voice_activation = VoiceActivationSystem()
    
    # Start voice activation
    if voice_activation.start_voice_activation():
        Aura_activated = True
        authenticated_user = voice_activation.get_authenticated_user()
        print(f"✅ Aura activated for {authenticated_user}!")
        SetAssistantStatus(f"Activated for {authenticated_user}")
        ShowTextToScreen(f"🎯 Aura activated for {authenticated_user}!\nYou can now use voice commands.")
    else:
        print("❌ Voice activation failed")
        print("💡 Starting Aura in manual mode...")
        SetAssistantStatus("Manual mode - Click 'Start Listening' to activate")
        # Allow manual activation
        Aura_activated = True
        authenticated_user = "Manual User"
        print("✅ Aura ready for manual activation!")

def MainExecution():
    global Aura_activated
    
    # Check if Aura is activated
    if not Aura_activated:
        SetAssistantStatus("Please activate Aura first by saying 'Hey Aura'")
        return
    
    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    SetAssistantStatus("Listening...")
    Query = SpeechRecognition()
    if not Query or Query.strip() == "":
        SetAssistantStatus("Didn't catch that, please try again...")
        return

    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Thinking...")
    Decision = FirstLayerDMM(Query)

    print(f"Decision: {Decision}")

    G = any(i.startswith("general") for i in Decision)
    R = any(i.startswith("realtime") for i in Decision)

    MergedQuery = " and ".join(
        ["-".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
    )

    for item in Decision:
        if "generate" in item:
            ImageGenerationQuery = str(item)
            ImageExecution = True

    for item in Decision:
        if not TaskExecution:
            if any(item.startswith(func) for func in Functions):
                run(Automation(Decision))
                TaskExecution = True

    if ImageExecution:
        with open(TempDirectoryPath("ImageGeneration.data"), "w") as file:
            file.write(f"{ImageGenerationQuery},True")
        try:
            p1 = subprocess.Popen(
                ['python', r'backend/ImageGeneration.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=False
            )
            subprocesses.append(p1)
        except Exception as e:
            print(f"Error starting ImageGeneration.py: {e}")

    if G or R:
        SetAssistantStatus("Searching..." if R else "Answering...")
        Answer = (
            RealtimeSearchEngine(QueryModifier(MergedQuery)) if R
            else ChatBot(QueryModifier(MergedQuery))
        )
        ShowTextToScreen(f"{Assistantname} : {Answer}")
        SetAssistantStatus("Answering...")
        TextToSpeech(Answer)
        return True

    # Fallback
    TextToSpeech("Okay, I'll do that for you.")
    return False

def FirstThread():
    while True:
        if GetMicrophoneStatus() == "True" and Aura_activated:
            MainExecution()
        elif "Available..." not in GetAssistantStatus() and Aura_activated:
            SetAssistantStatus("Available...")
        elif not Aura_activated:
            SetAssistantStatus("Say 'Hey Aura' to activate")
        sleep(0.1)

def SecondThread():
    GraphicalUserInterface()

if __name__ == "__main__":
    print("🚀 Starting Aura AI with Voice Authentication...")
    
    # Initialize the system
    InitialExecution()
    
    # Start voice activation in a separate thread
    voice_thread = threading.Thread(target=VoiceActivationThread, daemon=True)
    voice_thread.start()
    
    # Start main execution thread
    main_thread = threading.Thread(target=FirstThread, daemon=True)
    main_thread.start()
    
    # Start GUI
    SecondThread()
