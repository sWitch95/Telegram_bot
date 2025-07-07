from deep_translator import GoogleTranslator
from langdetect import detect  # ✅ Language detector
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 🧠 LLM + Embeddings
embedding_model = OllamaEmbeddings(model="mistral")
llm_model = Ollama(model="mistral")

# Vector DB
vectorstore = Chroma(
    persist_directory="embeddings/chroma",
    embedding_function=embedding_model
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
qa_chain = RetrievalQA.from_chain_type(llm=llm_model, retriever=retriever)

# 🌐 Translate
def translate(text: str, source: str, target: str) -> str:
    try:
        return GoogleTranslator(source=source, target=target).translate(text)
    except:
        return text

# 🎯 Main function
def answer_query(query: str) -> str:
    # Step 1: Detect user language
    lang = detect(query)
    if lang not in ['en', 'bn']:
        lang = 'en'  # fallback if unsure

    # Step 2: Translate query to English
    query_en = translate(query, source='auto', target='en')

    # Step 3: Run through RAG
    result = qa_chain.invoke({"query": query_en})
    answer_en = result.get("result", "").strip()

    if not answer_en:
        return "দুঃখিত, আমি আপনার প্রশ্নের উত্তর খুঁজে পাইনি।" if lang == "bn" else "Sorry, I couldn't find the answer."

    # Step 4: Translate back to original language
    if lang == "bn":
        return translate(answer_en, source='en', target='bn')
    else:
        return answer_en
