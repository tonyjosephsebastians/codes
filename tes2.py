import uuid
from langchain.chat_models import AzureChatOpenAI
from langchain.agents import Tool
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

# ----- 1. Set up FAISS RAG -----
raw_texts = ["Put your documents or 6M lines here"]
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents(raw_texts)

embedding_model = AzureOpenAIEmbeddings(
    deployment="embedding-deployment",
    model="text-embedding-ada-002"
)

vectorstore = FAISS.from_documents(docs, embedding_model)
retriever = vectorstore.as_retriever()

# ----- 2. LLM Setup -----
llm = AzureChatOpenAI(
    deployment_name="gpt-deployment",
    model_name="gpt-35-turbo",
    temperature=0.2
)

# ----- 3. Prompt + RAG Chain -----
rag_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""Answer the question using the context below:

Context:
{context}

Question: {question}

Answer:"""
)

rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    chain_type_kwargs={"prompt": rag_prompt}
)

def rag_tool_func(q):
    return rag_chain.run(q)

tools = [
    Tool(
        name="DocumentQA",
        func=rag_tool_func,
        description="Useful for answering questions about the provided documents"
    )
]

# ----- 4. LangGraph Agent with MemorySaver -----
system_message = "You are a helpful assistant. Answer concisely and clearly."

memory = MemorySaver()
agent_executor = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_message,
    checkpointer=memory
)

# Thread ID is used to simulate session-based memory
config = {"configurable": {"thread_id": "my-thread-001"}}

# ----- 5. Run Multiple Interactions -----
# Initial message
response1 = agent_executor.invoke(
    {
        "messages": [
            ("user", "Hi, I'm Tony. Can you summarize the API authentication section?")
        ]
    },
    config
)
print(response1["messages"][-1].content)
print("---")

# Ask follow-up question
response2 = agent_executor.invoke(
    {
        "messages": [("user", "Can you remember my name?")]
    },
    config
)
print(response2["messages"][-1].content)
print("---")

# Ask about previous output
response3 = agent_executor.invoke(
    {
        "messages": [("user", "What was that summary again?")]
    },
    config
)
print(response3["messages"][-1].content)
