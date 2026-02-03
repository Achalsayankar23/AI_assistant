# Import required libraries
from AppOpener import close, open as appopen  # Import functions to open and close apps.
from webbrowser import open as webopen         # Import web browser functionality.
from pywhatkit import search, playonyt         # Import functions for Google search and YouTube playback.
from dotenv import dotenv_values                # Import dotenv to manage environment variables.
from bs4 import BeautifulSoup                   # Import BeautifulSoup for parsing HTML content.
from rich import print                          # Import rich for styled console output.
from groq import Groq                           # Import Groq for AI chat functionalities.
import webbrowser                               # Import webbrowser for opening URLs.
import subprocess                               # Import subprocess for interacting with the system.
import requests                                 # Import requests for making HTTP requests.
import keyboard                                 # Import keyboard for keyboard-related actions.
import asyncio                                  # Import asyncio for asynchronous programming.
import os                                       # Import os for operating system functionalities.

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")  # Retrieve the Groq API key.

# Define CSS classes for parsing specific elements in HTML content.
classes = ["zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW", "gsrt vk_bk FzvWSb YwPhnf", "pclqee", "tw-Data-text tw-text-small tw-ta",
           "IZ6rdc", "O5uR6d LTKOO", "vLzY6d", "webanswers-webanswers_table__webanswers-table", "dDoNo ikb4Bb gsrt", "sXLa0e",
           "LWkfKe", "VQF4g9", "qv3Wpe", "kno-rdesc", "SPZz6b"]

# Define a user-agent for making web requests.
useragent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36'

# Initialize the Groq client with the API key.
client = Groq(api_key=GroqAPIKey)

# Predefined professional responses for user interactions.
professional_responses = [
    "Your satisfaction is my top priority; feel free to reach out if there's anything else I can help you with.",
    "I'm at your service for any additional questions or support you may need—don't hesitate to ask.",
]

# List to store chatbot messages.
messages = []

# System message to provide context to the chatbot.
SystemChatBot = {"role": "system", "content": f"Hello, I am {os.environ['Username']}, You're a content writer. You have to write content like letters, articles, speeches, essays, etc."}

# Function to perform a Google search.
def GoogleSearch(Topic):
    search(Topic)
    return True

# Function to generate content using AI and save it to a file.
def Content(Topic):
    def OpenNotepad(File):
        default_text_editor = 'notepad.exe'
        subprocess.Popen([default_text_editor, File])

    def ContentWriterAI(prompt):
        messages.append({"role": "user", "content": f"{prompt}"})

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=SystemChatBot + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})
        return Answer

    Topic = Topic.replace("Content ", "")
    ContentByAI = ContentWriterAI(Topic)

    with open(rf"Data\{Topic.lower().replace(' ', '')}.txt", "w", encoding="utf-8") as file:
        file.write(ContentByAI)
        file.close()

    OpenNotepad(rf"Data\{Topic.lower().replace(' ', '')}.txt")
    return True

# Function to search for a topic on YouTube.
def YouTubeSearch(Topic):
    Url4Search = f"https://www.youtube.com/results?search_query={Topic}"
    webbrowser.open(Url4Search)
    return True

# Function to play a video on YouTube.
def PlayYoutube(query):
    try:
        # Use webbrowser to open YouTube search
        search_query = query.replace("play ", "").strip()
        youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
        webopen(youtube_url)
        print(f"Opened YouTube search for: {search_query}")
        return True
    except Exception as e:
        print(f"Failed to open YouTube: {e}")
        return False

# Function to open an application or a relevant webpage.
def OpenApp(app, sess=requests.session()):
    # Map common app names to their proper names
    app_mapping = {
        'youtube': 'youtube',
        'chrome': 'chrome',
        'browser': 'chrome',
        'notepad': 'notepad',
        'calculator': 'calculator',
        'firefox': 'firefox',
        'edge': 'edge',
        'word': 'word',
        'excel': 'excel',
        'powerpoint': 'powerpoint',
        'spotify': 'spotify',
        'discord': 'discord',
        'telegram': 'telegram',
        'whatsapp': 'whatsapp'
    }
    
    # Get the proper app name
    app_name = app_mapping.get(app.lower(), app)
    
    try:
        print(f"Attempting to open: {app_name}")
        appopen(app_name, match_closest=True, output=True, throw_error=True)
        print(f"Successfully opened: {app_name}")
        return True
    except Exception as e:
        print(f"Failed to open {app_name} with AppOpener: {e}")
        # Fallback to web search
        try:
            if app_name.lower() in ['youtube']:
                webopen("https://www.youtube.com")
            elif app_name.lower() in ['chrome', 'browser']:
                webopen("https://www.google.com")
            else:
                webopen(f"https://www.google.com/search?q={app_name}")
            print(f"Opened {app_name} in browser as fallback")
            return True
        except Exception as e2:
            print(f"Failed to open {app_name} in browser: {e2}")
            return False

# Function to close an application.
def CloseApp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app, match_closest=True, output=True, throw_error=True)
            return True
        except:
            return False

# Function to execute system-level commands.
def System(command):
    def mute():
        keyboard.press_and_release("volume mute")

    def unmute():
        keyboard.press_and_release("volume mute")

    def volume_up():
        keyboard.press_and_release("volume up")

    def volume_down():
        keyboard.press_and_release("volume down")

    if command == "mute":
        mute()
    elif command == "unmute":
        unmute()
    elif command == "volume up":
        volume_up()
    elif command == "volume down":
        volume_down()

    return True

# Asynchronous function to translate and execute user commands.
async def TranslateAndExecute(commands: list[str]):
    funcs = []  # List to store asynchronous tasks.

    for command in commands:

        if command.startswith("open "):  # Handle "open" commands.
            if "open it" in command:  # Ignore "open it" commands.
                pass

            if "open file" == command:  # Ignore "open file" commands.
                pass

            else:
                fun = asyncio.to_thread(OpenApp, command.removeprefix("open "))  # Schedule app opening.
                funcs.append(fun)

        elif command.startswith("general "):  # Placeholder for general commands.
            pass

        elif command.startswith("realtime "):  # Placeholder for real-time commands.
            pass

        elif command.startswith("close "):  # Handle "close" commands.
            fun = asyncio.to_thread(CloseApp, command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("play "):  # Handle "play" commands.
            fun = asyncio.to_thread(PlayYoutube, command.removeprefix("play "))
            funcs.append(fun)

        elif command.startswith("content "):  # Handle "content" commands.
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("google search "):  # Handle Google search commands.
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)

        elif command.startswith("youtube search "):  # Handle YouTube search commands.
            fun = asyncio.to_thread(YouTubeSearch, command.removeprefix("youtube search "))
            funcs.append(fun)

        elif command.startswith("system "):  # Handle system commands.
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)

        else:
            print(f"No Function Found. For {command}")  # Print an error for unrecognized commands.

    results = await asyncio.gather(*funcs)  # Execute all tasks concurrently.

    for result in results:  # Process the results.
        if isinstance(result, str):
            yield result
        else:
            yield result

# Asynchronous function to automate command execution.
async def Automation(commands: list[str]):
    async for result in TranslateAndExecute(commands):  # Translate and execute commands.
        pass
    return True  # Indicate success.
