Test
import uuid
from typing import TypedDict, List, Optional

from langchain.chat_models import AzureChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph

# ----- 1. Set up vector store tool (RAG) -----
raw_texts = ["Put your documents or 6M lines here"]
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.create_documents(raw_texts)

embedding_model = AzureOpenAIEmbeddings(
    deployment="embedding-deployment",
    model="text-embedding-ada-002"
)

vectorstore = FAISS.from_documents(docs, embedding_model)
retriever = vectorstore.as_retriever()

llm = AzureChatOpenAI(
    deployment_name="gpt-deployment",
    model_name="gpt-35-turbo",
    temperature=0.2
)

# ----- 2. Define RAG tool -----
rag_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
Answer the question using the context below:

Context:
{context}

Question: {question}

Answer:
"""
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

# ----- 3. Set up agent executor -----
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# ----- 4. Chat memory persistence -----
session_id = "session-1234"  # can use uuid or user ID
history = ChatMessageHistory(session_id=session_id)
memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=history,
    return_messages=True
)

# ----- 5. LangGraph state -----
class AgentState(TypedDict):
    input: str
    output: Optional[str]
    chat_history: List

# Agent node
def agent_node(state: AgentState) -> AgentState:
    memory.chat_memory.messages = state["chat_history"]

    # Agent uses tools to answer
    result = agent.run(input=state["input"])

    memory.chat_memory.add_user_message(state["input"])
    memory.chat_memory.add_ai_message(result)

    return {
        "input": state["input"],
        "output": result,
        "chat_history": memory.chat_memory.messages
    }

# ----- 6. LangGraph setup -----
graph = StateGraph(AgentState)
graph.add_node("agent_executor", agent_node)
graph.set_entry_point("agent_executor")
graph.set_finish_point("agent_executor")

agent_app = graph.compile()

# ----- 7. Use the agent -----
initial_state = {
    "input": "Summarize the section about API authentication",
    "output": None,
    "chat_history": history.messages
}

final_state = agent_app.invoke(initial_state)

print("Agent Response:", final_state["output"])
print("Chat History:")
for msg in final_state["chat_history"]:
    print(f"{msg.type.upper()}: {msg.content}")
	◦
