from groq import Groq
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

client = Groq(api_key=GroqAPIKey)

models = client.models.list()
for m in models.data:
    print(m.id)
