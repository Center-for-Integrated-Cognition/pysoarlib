# LanguageModelConnector
Support for remote connection of language model to Soar agents, that supports different templates and models.

# ENV variables
Make sure you have the following environment keys set:

export OPENAI_API_KEY="openai key"

export LANGCHAIN_TRACING_V2=true

export LANGCHAIN_API_KEY="langchain key"

export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"

The last three are optional for access to langsmith (for tracing input and output)

# Dependencies
python 3.12 or higher


## Langchain
pip install langchain

## Langsmith
Not required, but langsmith enables tracing and logging of prompts and responses.

pip install -U langsmith

To use langsmith you must create an account and get an api key.


# I/0
    (I3 ^lm-request L3)
    
        (L3 ^argument-count 1 ^argument1 |container ship| ^type vehicle-speed-query)

The response on the input link is:

    (I2 ^language-model L2)
    
        (L2 ^response R7)
        
            (R7 ^id |L3| ^response 25)
        
# Templates
templates are specified in /templates/"template-name"/
Three files are expected.

system.txt contains the system prompt

user.txt contains the user prompt

response_type contains the response type (string, float, int)

In the user prompt argument variables are specified as ?argument1, ?argument2, etc.

See vehicle-speed-query for an example.