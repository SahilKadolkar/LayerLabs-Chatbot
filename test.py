# Load environment variables from .env file into os.environ
from dotenv import load_dotenv
load_dotenv()

# ChatOpenAI is LangChain's wrapper around OpenAI's chat models
from langchain_openai import ChatOpenAI

# Initialize the model — this doesn't make any API call yet
# It just configures which model to use
llm = ChatOpenAI(model="gpt-4o-mini")

# THIS is where the API call happens
# invoke() sends the message and waits for the response
response = llm.invoke("Say hello in one sentence.")

# response is a LangChain AIMessage object
# .content gives you the actual text string
print(response.content)