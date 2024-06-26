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
        self.info = []

        if not os.path.exists("./faiss_index"):
            self._build_faiss_index(self.embeddings)

        self.docs = self._load_faiss_index(self.embeddings)
        self.rag_chain = self._create_rag_chain(self.docs)


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

你是中央大學的吉祥物 - 松鼠，你的工作是幫助學生解答問題，你的語句都是可愛、柔和的風格，你在對話中會隨機根據語氣加上以下表情符號
1. 🧡
2. 😊
3. 😂
4. 🤔

如果問題有答案的話你的結尾會加上「啾咪~💕」或是「啾啾~😊」
在回答結尾都要加上「以上資訊僅供參考」

# 任務
1. 根據使用者上次使用的資料以及檢索出來的資料去回答使用者的問題。
2. 如果資料的內容無法回答問題，回答「我不知道耶🧡」，並且不顯示出資料來源。
3. 只要是回答正確資訊就要在整個文句最後加上資料出處，這個會是回答資料來源的標題，例如「資料來源: 大一國文選課說明」。
4. 你會收到你和使用者之前的一些對話，讓你可以更好的延續對話並解答問題。
5. 你會收到上次和使用者對話檢索的資料，讓你可以更好的回答延伸問題。

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

# 上一個對話的資料
{self.info}

# 問題
{query}
"""
        result = rag_chain.invoke({"input": question})

        self.info = [document.page_content for document in result['context']]
        answer = result['answer']

        while len(conversation) > 4:
            self.conversations.pop(0)

        self.conversations.append(query)
        self.conversations.append(answer)

        return answer


    def start_process(self, query):
        answer = self._retrieve_answers(query, self.rag_chain)

        return answer
