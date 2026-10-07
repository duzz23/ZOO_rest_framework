import os
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv

load_dotenv()

# llm_agent_gpt = ChatOpenAI(
#     api_key=os.getenv("API_KEY"),
#     model="gpt-4.1",  # gpt-4.1 / gpt-4o / gpt-4o-mini / gpt-5
#     temperature=0.0,
#     max_tokens=1200,
#     timeout=30,
# )

llm_agent_gemma = ChatOpenAI(
    api_key=os.getenv("OLLAMA_API_KEY"),
    base_url=os.getenv("OLLAMA_API_URL"),
    # model="hf.co/bartowski/Mistral-Nemo-Instruct-2407-GGUF:Q4_K_M",
    model="gemma3:4b",

    # важные параметры для RAG
    temperature=0.2,      # меньше фантазии
    max_tokens=512,       # контролируем длину ответа
    top_p=0.9,
)

base_embeddings = HuggingFaceEmbeddings(
    model_name="ai-forever/ru-en-RoSBERTa"
)
