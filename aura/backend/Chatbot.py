from groq import Groq  # Importing the Groq library to use its API.
from json import load, dump  # Importing functions to read and write JSON files.
import datetime  # For real-time date and time.
from dotenv import dotenv_values  # For reading environment variables from a .env file.

# Load environment variables from the .env file.
env_vars = dotenv_values('.env')

# Retrieve specific environment variables.
Username = env_vars.get("Username")
Assistantname = env_vars.get("Assistantname")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Initialize the Groq client using the provided API key.
client = Groq(api_key=GroqAPIKey)

# Define a system message for the chatbot's role and behavior.
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} who...
** Do not tell time until I ask, do not talk too much, just answer the question. **
** Reply in only English, even if the question is in Hindi, reply in English. **
** Do not provide notes in the output, just answer the question and never mention your training data. **"""

# System messages to prime the chatbot.
SystemChatBot = [
    {"role": "system", "content": System}
]

# Attempt to load the chat log from a JSON file.
try:
    with open("Data\\ChatLog.json", "r") as f:
        messages = load(f)
except FileNotFoundError:
    with open("Data\\ChatLog.json", "w") as f:
        dump([], f)
    messages = []

# Function to get real-time date and time.
def RealtimeInformation():
    now = datetime.datetime.now()
    return (
        f"Please use this real-time information if needed,\n"
        f"Day: {now.strftime('%A')}\n"
        f"Date: {now.strftime('%d')}\n"
        f"Month: {now.strftime('%B')}\n"
        f"Year: {now.strftime('%Y')}\n"
        f"Time: {now.strftime('%H')} hours :{now.strftime('%M')} minutes :{now.strftime('%S')} seconds.\n"
    )

# Function to clean up the AI's response.
def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

# Main chatbot function
def ChatBot(Query):
    try:
        with open("Data\\ChatLog.json", "r") as f:
            messages = load(f)

        messages.append({"role": "user", "content": Query})

        # Get AI response
        completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",   # ✅ use the exact name from your list
        messages=SystemChatBot + [{"role": "system", "content": RealtimeInformation()}] + messages,
        max_tokens=1024,
        temperature=0.7,
        top_p=1
)

        Answer = completion.choices[0].message.content


        Answer = Answer.replace('</s>', '')
        messages.append({"role": "assistant", "content": Answer})

        with open("Data\\ChatLog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer)

    except Exception as e:
        print(f"Error: {e}")
        with open("Data\\ChatLog.json", "w") as f:
            dump([], f, indent=4)
        return ChatBot(Query)

# Entry point
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question: ")
        print(ChatBot(user_input))
