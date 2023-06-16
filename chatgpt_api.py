
import openai
import pandas as pd
import os
from dotenv import load_dotenv


load_dotenv()

OPENAI_MdP = os.getenv('OPENAI_MdP')

openai.api_key = OPENAI_MdP

# Set up the model and prompt
model_engine = "text-davinci-003"
#nlp = spacy.load ("en_core_web_sm")

df = pd.read_csv('earthquake.csv', index_col=0).sample(frac = 0.05)
df.drop(['geometry', 'time', 'date', 'location'], axis = 1, inplace = True)

# Preprocess user input and modify conversation history
def chatbot(prompt):
    conversation = [
        {
            'role': 'system',
            'content': 'You are a helpful assistant.'
        },
        {
            'role': 'user',
            'content': prompt
        },
        {
            'role': 'assistant',
            'content': ''
        }
    ]

    # Convert the conversation to a string
    chat_history = '\n'.join ([f'{message["role"]}: {message["content"]}' for message in conversation])

    print(chat_history)

    completion = openai.Completion.create (
                engine=model_engine,
                prompt=chat_history,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.7,
            )

    response = completion.choices[0].text.strip()
    # Split the response into lines
    lines = response.split ('\n')

    # Identify the code portion
    code_lines = []
    for line in lines:
        if line.startswith ("import ") or line.startswith ("#") or line.startswith ("df['"):
            code_lines.append (line)

    # Extract the code and explanation
    code = '\n'.join (code_lines)
    explanation = response.replace (code, "").strip ()

    return explanation, code
