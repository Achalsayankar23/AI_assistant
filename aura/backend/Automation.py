# =========================
# Imports
# =========================
from AppOpener import close, open as appopen
from webbrowser import open as webopen
from pywhatkit import search, playonyt
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from rich import print
from groq import Groq
import webbrowser
import subprocess
import requests
import keyboard
import asyncio
import os

# =========================
# Load Environment Variables
# =========================
# This will load aura/.env
load_dotenv()

# Groq client (reads GROQ_API_KEY automatically)
client = Groq()

# =========================
# Constants
# =========================
classes = [
    "zCubwf", "hgKElc", "LTKOO sY7ric", "Z0LcW",
    "gsrt vk_bk FzvWSb YwPhnf", "pclqee",
    "tw-Data-text tw-text-small tw-ta",
    "IZ6rdc", "O5uR6d LTKOO", "vLzY6d",
    "webanswers-webanswers_table__webanswers-table",
    "dDoNo ikb4Bb gsrt", "sXLa0e", "LWkfKe",
    "VQF4g9", "qv3Wpe", "kno-rdesc", "SPZz6b"
]

useragent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/100.0.4896.75 Safari/537.36"
)

messages = []

SystemChatBot = {
    "role": "system",
    "content": (
        f"Hello, I am {os.getenv('Username', 'Aura')}. "
        "You are a professional content writer. "
        "You write letters, articles, essays, speeches, etc."
    )
}

# =========================
# Utility Functions
# =========================
def GoogleSearch(topic):
    search(topic)
    return True


def Content(topic):
    def open_notepad(file):
        subprocess.Popen(["notepad.exe", file])

    def content_writer_ai(prompt):
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[SystemChatBot] + messages,
            max_tokens=2048,
            temperature=0.7,
            top_p=1,
            stream=True,
        )

        answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                answer += chunk.choices[0].delta.content

        messages.append({"role": "assistant", "content": answer})
        return answer

    topic = topic.replace("content ", "")
    result = content_writer_ai(topic)

    os.makedirs("Data", exist_ok=True)
    filepath = f"Data/{topic.lower().replace(' ', '')}.txt"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(result)

    open_notepad(filepath)
    return True


def YouTubeSearch(topic):
    url = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(url)
    return True


def PlayYoutube(query):
    try:
        query = query.replace("play ", "").strip()
        webopen(f"https://www.youtube.com/results?search_query={query}")
        return True
    except Exception as e:
        print(e)
        return False


def OpenApp(app):
    try:
        appopen(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        webopen(f"https://www.google.com/search?q={app}")
        return True


def CloseApp(app):
    try:
        close(app, match_closest=True, output=True, throw_error=True)
        return True
    except:
        return False


def System(command):
    if command == "mute":
        keyboard.press_and_release("volume mute")
    elif command == "unmute":
        keyboard.press_and_release("volume mute")
    elif command == "volume up":
        keyboard.press_and_release("volume up")
    elif command == "volume down":
        keyboard.press_and_release("volume down")
    return True

# =========================
# Async Command Engine
# =========================
async def TranslateAndExecute(commands: list[str]):
    tasks = []

    for command in commands:
        if command.startswith("open "):
            tasks.append(asyncio.to_thread(OpenApp, command.replace("open ", "")))

        elif command.startswith("close "):
            tasks.append(asyncio.to_thread(CloseApp, command.replace("close ", "")))

        elif command.startswith("play "):
            tasks.append(asyncio.to_thread(PlayYoutube, command))

        elif command.startswith("content "):
            tasks.append(asyncio.to_thread(Content, command))

        elif command.startswith("google search "):
            tasks.append(asyncio.to_thread(GoogleSearch, command.replace("google search ", "")))

        elif command.startswith("youtube search "):
            tasks.append(asyncio.to_thread(YouTubeSearch, command.replace("youtube search ", "")))

        elif command.startswith("system "):
            tasks.append(asyncio.to_thread(System, command.replace("system ", "")))

        else:
            print(f"[red]No function found for:[/red] {command}")

    results = await asyncio.gather(*tasks)
    for r in results:
        yield r


async def Automation(commands: list[str]):
    async for _ in TranslateAndExecute(commands):
        pass
    return True
