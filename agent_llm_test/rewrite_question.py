# from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from agent_llm_test.model_agent.model import llm_agent_gemma

# Промт

question_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Ты подготавливаешь вопрос для RAG по Зоопарку в Екатеринбурге.\n"
     "Верни результат СТРОГО в JSON без лишнего текста.\n"
     "Формат: {{\"question\": \"...\"}}\n"
     "Правила:\n"
     "- Если вопрос хороший — верни его как есть.\n"
     "- Если плохой — перепиши в чёткий самодостаточный вопрос.\n"
     "- Не добавляй префиксы вроде 'Формулировка для поиска:'\n"
     "- Не используй кавычки-ёлочки «» и двойные кавычки вокруг всего вопроса.\n"
     "- Всегда упоминай 'Зоопарк в Екатеринбурге', если уместно.\n"
     ),
    ("human", "{question}")
])

# ================================================================================================================
question_rewrite_chain = (
        question_rewrite_prompt
        | llm_agent_gemma
        # | StrOutputParser() # используем StrOutputParser так как возвращаем строку
        | JsonOutputParser() # используем JsonOutputParser так как возвращаем JSON
)

# ================================================================================================================

def rewrite_question_if_needed(question: str) -> str:
    # для json
    data = question_rewrite_chain.invoke({"question": question})

    return data["question"].strip()
    # для стр
    # rewritten = question_rewrite_chain.invoke({"question": question}).strip()
    # return rewritten

# ================================================================================================================


if __name__ == "__main__":
    print(rewrite_question_if_needed('Стоимость входа'))
    print(rewrite_question_if_needed('Время работы'))
    print(rewrite_question_if_needed('Какой адрес'))


