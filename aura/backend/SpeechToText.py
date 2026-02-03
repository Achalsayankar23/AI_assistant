from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import os
import mtranslate as mt
import time

# Load environment variables from the .env file.
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage")

# HTML code for speech recognition interface.
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start" onclick="startRecognition()">Start Recognition</button>
    <button id="end" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent += transcript + ' ';
            };

            recognition.onend = function() {
                recognition.start();
            };
            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
        }
    </script>
</body>
</html>'''

# Inject the input language from .env into the HTML.
HtmlCode = HtmlCode.replace("recognition.lang = ''", f"recognition.lang = '{InputLanguage}'")

# Write the HTML to a file.
os.makedirs("Data", exist_ok=True)
with open("Data\\Voice.html", "w", encoding='utf-8') as f:
    f.write(HtmlCode)

# Paths and Chrome setup.
current_dir = os.getcwd()
Link = f"{current_dir}/Data/Voice.html"

chrome_options = Options()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
chrome_options.add_argument(f'user-agent={user_agent}')
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
# DO NOT use headless if microphone is needed.
# chrome_options.add_argument("--headless=new")

chrome_options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.media_stream_mic": 1
})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Define temp directory path.
TempDirPath = rf"{current_dir}/Frontend/Files"
os.makedirs(TempDirPath, exist_ok=True)

# Status setter
def SetAssistantStatus(Status):
    with open(rf"{TempDirPath}/Status.data", "w", encoding='utf-8') as file:
        file.write(Status)

# Query formatter
def QueryModifier(Query):
    new_query = Query.lower().strip()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom",
                      "can you", "what's", "who's", "is", "are", "do", "does", "did", "could", "would", "should"]
    
    if any(word + " " in new_query for word in question_words):
        if new_query[-1] not in ['?', '.', '!']:
            new_query += "?"
    else:
        if new_query[-1] not in ['?', '.', '!']:
            new_query += "."

    return new_query.capitalize()

# Translator to English
def UniversalTranslator(Text):
    english_translation = mt.translate(Text, "en", "auto")
    return english_translation.capitalize()

# Speech recognition function
def SpeechRecognition():
    driver.get("file:///" + Link)
    driver.find_element(by=By.ID, value="start").click()

    print("🎤 Listening...")

    timeout = 10  # Seconds before giving up
    start_time = time.time()
    last_text = ""

    while True:
        try:
            time.sleep(1.5)
            Text = driver.find_element(by=By.ID, value="output").text.strip()

            if Text and Text != last_text:
                last_text = Text
                driver.find_element(by=By.ID, value="end").click()

                if "en" in InputLanguage.lower():
                    return QueryModifier(Text)
                else:
                    SetAssistantStatus("Translating ...")
                    return QueryModifier(UniversalTranslator(Text))

            if time.time() - start_time > timeout:
                driver.find_element(by=By.ID, value="end").click()
                print("❌ Timeout: No speech detected.")
                return None

        except Exception as e:
            print("⚠️ Error:", e)
            continue

# Main loop
if __name__ == "__main__":
    try:
        while True:
            query = SpeechRecognition()
            if query:
                print("✅ Recognized Query:", query)
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
        driver.quit()
