from langsmith import traceable
from agent_llm_test.model_agent.model import llm_agent_gemma
from agent_llm_test.parser_and_create_db import retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from agent_llm_test.rewrite_question import rewrite_question_if_needed

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Ты помощник, который отвечает СТРОГО НА РУССКОМ ЯЗЫКЕ. "
        "Используй только информацию из предоставленного контекста, не придумывай факты. "
        "Если ответа в контексте нет или данных недостаточно, честно скажи, что не нашёл ответа в базе. "
        "При необходимости можешь упоминать источник в формате из заголовка (Source и Page). "
        "Отвечай кратко и по делу, обычно до 5–7 предложений."
    ),
    # историю можно не заполнять, но структура уже есть
    MessagesPlaceholder("history"),
    (
        "human",
        "Контекст:\n{context}\n\nВопрос: {question}"
    ),
])

# ================================================================================================================

from langchain_openai import ChatOpenAI



# ================================================================================================================
# format_docs()
## Что делает post-processing в RAG
#
# После retriever’а у нас есть **список документов** (чанков), а в промпт модели нужно передать **одну строку контекста**.
#
# Post-processing – это этап, на котором мы:
#
# - форматируем каждый документ (добавляем заголовки, источники и т.п.);
# - соединяем их в одну строку;
# - при необходимости чистим/режем, чтобы контекст не разъехался по токенам.
def format_docs(docs, max_chars: int = 8000):
    formatted = []
    total_len = 0

    for doc in docs:
        source = doc.metadata.get("source", "unknown_source")
        page = doc.metadata.get("page", None)

        header = f"Source: {source}"
        if page is not None:
            header += f" | Page: {page}"

        text = doc.page_content.strip()
        block = f"{header}\n{text}"

        # если следующий блок слишком раздует контекст — останавливаемся
        if total_len + len(block) > max_chars:
            break

        formatted.append(block)
        total_len += len(block)

    return "\n\n---\n\n".join(formatted)

# Зашита от пустого котекста

def ensure_context(input_dict: dict) -> dict:
    """
    Если retriever не нашёл ничего полезного и контекст пустой,
    явно помечаем это в контексте, чтобы модель не фантазировала.
    """
    context = input_dict.get("context", "").strip()
    if not context:
        input_dict["context"] = (
            "Контекст пуст: ретривер не нашёл ни одного подходящего фрагмента. "
            "Если ответ важен, лучше явно сказать пользователю об этом."
        )
    return input_dict

rag_chain = (
        {
            # контекст и вопрос теперь приходят извне в виде dict
            "context": lambda d: d.get("context", ""),
            "question": lambda d: d.get("question", ""),
            "history": lambda _: [],  # пока истории нет – передаём пустой список
        }
        | RunnableLambda(ensure_context)   # защита от пустого контекста
        | prompt
        | llm_agent_gemma
        | StrOutputParser()
).with_config(run_name="rag_chain")

# Настройка LangSmith для отслеживания RAG
# ================================================================================================================
@traceable(name="AW_answer_question")
def answer_question(question: str, context: str) -> str:
    """
    Основная точка входа в RAG.
    Эту функцию мы будем отслеживать в LangSmith как корневой run.
    В INPUT корневого run'а будут поля question и context.
    """
    inputs = {
        "question": question,
        "context": context,
    }
    return rag_chain.invoke(inputs)



# ================================================================================================================

if __name__ == "__main__":
    import time

    t1 = time.time()

    questions = [
        "Какие есть животные в зоопарке?",
        "Афиша мероприятий?",
        "адрес?",
        "А есть медведи?",
        "Часы работы?"

    ]

    t2 = time.time()
    print('Время на подготовку:', t2 - t1)

    for q in questions:
        print("Вопрос:", q)
        # 0) проверяем, нужно ли переписать вопрос
        q = rewrite_question_if_needed(q)

        # 1) достаём документы из ретривера
        retrieved_docs = retriever.invoke(q)
        # 2) форматируем их в строку контекста
        ctx = format_docs(retrieved_docs)

        # 3) передаём и вопрос, и контекст в корневой run
        answer = answer_question(question=q, context=ctx)

        print("Ответ:", answer)
        print("================================================================")

    t3 = time.time()
    print('Время на вопросы:', t3 - t2)