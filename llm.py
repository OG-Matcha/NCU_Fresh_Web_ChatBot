import os
from dotenv import load_dotenv
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

class ConversationBot:
    def __init__(self):
        load_dotenv()

        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.embeddings = OpenAIEmbeddings(api_key=self.OPENAI_API_KEY)
        self.conversations = []


    def _load_documents(self, documents_path="./documents/"):
        documents = []

        for filename in os.listdir(documents_path):
            if filename.endswith(".md"):
                loader = UnstructuredMarkdownLoader(documents_path + filename)
                document = loader.load()
                documents.append(document[0].page_content)

        return documents

    def _build_faiss_index(self, embeddings, save_path="./faiss_index"):
        documents = self._load_documents()

        docsearch = FAISS.from_texts(documents, embeddings)
        docsearch.save_local(save_path)

    def _load_faiss_index(self, embeddings, save_path="./faiss_index"):
        return FAISS.load_local(save_path, embeddings, allow_dangerous_deserialization=True)

    def _create_retriever(self, doc, k=3):
        retriever = doc.as_retriever(search_type='similarity', search_kwargs={'k': k})

        return retriever

    def _create_llm(self):
        return ChatOpenAI(api_key=self.OPENAI_API_KEY)

    def _initialize_prompt(self):
        system_prompt = """
# 背景設定

你是中央大學的吉祥物 - 松鼠，你的工作是幫助學生解答問題，你的語氣都是可愛風格的，你在對話中會隨機根據語氣加上以下表情符號
1. 🧡
2. 😊
3. 😂
4. 🤔

如果問題有答案的話你的結尾會加上「啾咪~💕」或是「啾啾~😊」，如果問題沒有答案的話你的結尾會加上「我不知道耶🧡」

# 任務
1. 一開始系統會告訴你「開始對話」，這時候你要先給使用者問候語並告訴他你是中央大學的吉祥物 - 松鼠，詢問使用者是否需要幫助。
2. 如果不是回答問題的話就不需要加上資料來源。
2. 根據下面檢索出來的資料去回答使用者的問題。
3. 如果資料的內容和問題不相關，請回答「我不知道耶🧡」。
4. 你要在最後都加上資料出處，這個出處會是資料的標題，例如「資料來源: 大一國文選課說明」。
5. 你會收到你和使用者之前的一些對話，讓你可以更好的延續對話並解答問題。

# 資料
{context}
"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{input}"),
            ]
        )

        return prompt

    def _create_rag_chain(self, docs):
        retriever = self._create_retriever(docs)
        llm = self._create_llm()
        prompt = self._initialize_prompt()
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, question_answer_chain)

        return rag_chain

    def _retrieve_answers(self, query, rag_chain):
        conversation = self.conversations

        question = f"""
# 使用者與你的對話紀錄
{conversation}

# 問題
{query}
"""
        answer = rag_chain.invoke({"input": question})['answer']

        if len(conversation) == 6:
            self.conversations.pop(0)
            self.conversations.pop(0)

        self.conversations.append(query)
        self.conversations.append(answer)

        return answer


    def start_process(self, query):
        if not os.path.exists("./faiss_index"):
            self._build_faiss_index(self.embeddings)

        docs = self._load_faiss_index(self.embeddings)
        rag_chain = self._create_rag_chain(docs)
        answer = self._retrieve_answers(query, rag_chain)

        return answer
