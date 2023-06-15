from thefuzz import fuzz
from thefuzz import process
import openai
import pandas as pd
import os
from dotenv import load_dotenv
import gc


load_dotenv()

OPENAI_MdP = os.getenv('OPENAI_MdP')

openai.api_key = OPENAI_MdP

# Set up the model and prompt
model_engine = "text-davinci-003"
#nlp = spacy.load ("en_core_web_sm")

df = pd.read_csv('earthquake.csv', index_col=0).sample(frac = 0.05)


parameter1 = []
parameter2 = []

for i in ['City', 'Town']:
    parameter1.append({i: df[i].unique ()})


parameter2 = parameter1[0]['City'].tolist() + parameter1[1]['Town'].tolist()


def process_prompt(prompt, df):
    # Convert prompt to lowercase for case-insensitive matching
    print('prompt1', prompt)


    if len(prompt) > 1 and prompt[0] =='File' and prompt[-1] !='file' and prompt[-1] !='stop':
        #prompt = ''.join (i for i in prompt[-1])
        prompt = prompt[-1].lower ()

        print('prompt3', prompt)

        # Find the best matching column in the dataframe

        best_match = process.extractOne (prompt, parameter2, scorer=fuzz.partial_ratio)

        print('best_match', best_match)

        if best_match and best_match[1] >= 80:  # Adjust the threshold as needed
            column = best_match[0]

            # Retrieve the corresponding values from the dataframe
            if best_match[0] in parameter1[0]['City'] :
                values = df[df['City'] == best_match[0]]

                response = values.to_json(orient='records')
            if best_match[0] in parameter1[1]['Town'] :
                values = df[df['Town'] == best_match[0]]
                response = values.to_json(orient='records')

        else:
            response = False
            return response
    elif prompt == 'file' or prompt[-1] == 'file'  :
        return 'Ok, Let\'s start work on your file, prompt your questions'
    elif prompt[-1] == 'stop' :

        return 'Thank you for your prompts'




    return response

# Preprocess user input and modify conversation history
def chatbot(prompt):

    if process_prompt (prompt, df):
        response = process_prompt (prompt, df)
        return response

    else:
        print('it responses here')

        if type(prompt) == str:
            prompt = prompt
        else :

            prompt = ''.join (i for i in prompt[-1])
            print('propt last', prompt)
            completion = openai.Completion.create (
                engine=model_engine,
                prompt=prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.7,
            )

        response = completion.choices[0].text.strip()
        return response
