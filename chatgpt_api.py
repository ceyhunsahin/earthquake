import openai

openai.api_key = "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"

# Set up the model and prompt
model_engine = "text-davinci-003"
#nlp = spacy.load ("en_core_web_sm")


def chatbot(prompt):
# Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.5,
    )

    response = completion.choices[0].text.strip()
    print(response)
    return response
