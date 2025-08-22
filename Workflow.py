import random
from langgraph.graph import StateGraph, END

# Define workflow state
class WorkflowState(dict):
    pass


# --- Function Implementations ---

def upload_cobol_files(state: WorkflowState) -> WorkflowState:
    # Simulate file upload
    print("Uploading COBOL/JCL files...")
    cobol_files = ["account.cob", "payment.jcl", "proc1.proc"]
    state["cobol_files"] = cobol_files
    return state


def upload_copybooks(state: WorkflowState) -> WorkflowState:
    # Simulate copybook upload
    print("Uploading copybooks...")
    copybooks = ["account_copy.cpy", "transaction_copy.cpy"]
    state["copybooks"] = copybooks
    return state


def extract_fields_from_copybooks(state: WorkflowState) -> WorkflowState:
    # Mock field extraction from copybooks
    print("Extracting fields from copybooks...")
    # Imagine parsing COPYBOOK fields
    extracted_fields = {
        "ACCOUNT_NO": {"type": "X(10)", "desc": "Account number"},
        "AMOUNT": {"type": "9(9)V99", "desc": "Transaction amount"},
        "DATE": {"type": "X(8)", "desc": "Transaction date"}
    }
    state["fields"] = extracted_fields
    return state


def embed_documents(state: WorkflowState) -> WorkflowState:
    print("Embedding COBOL/JCL documents...")
    cobol_files = state.get("cobol_files", [])
    embeddings = {file: f"vec_{i}" for i, file in enumerate(cobol_files)}
    state["embeddings"] = embeddings
    return state


def ingest_into_ai_search(state: WorkflowState) -> WorkflowState:
    print("Ingesting documents into AI search index...")
    state["ai_index"] = {
        "documents": state.get("embeddings", {}),
        "index_name": "cobol_ai_index"
    }
    return state


def store_field_dictionary(state: WorkflowState) -> WorkflowState:
    print("Storing extracted fields into dictionary...")
    dictionary = state.get("fields", {})
    state["dictionary"] = dictionary
    return state


def ai_search(state: WorkflowState) -> WorkflowState:
    print("Running AI search over indexed documents + fields...")
    # Fake retrieval: choose top docs randomly
    docs = list(state.get("ai_index", {}).get("documents", {}).keys())
    retrieved = random.sample(docs, min(2, len(docs)))
    state["retrieved_docs"] = retrieved
    return state


def generate_response(state: WorkflowState) -> WorkflowState:
    print("Generating AI response using retrieved docs + fields...")
    docs = state.get("retrieved_docs", [])
    fields = state.get("dictionary", {})
    response = f"Docs: {docs}, Fields used: {list(fields.keys())}"
    state["response"] = response
    return state


def validate_response(state: WorkflowState) -> WorkflowState:
    print("Validating AI response...")
    response = state.get("response", "")
    # Mock validation: random accept/reject
    state["valid"] = random.choice([True, False])
    print(f"Validation result: {state['valid']}")
    return state


def query_transform(state: WorkflowState) -> WorkflowState:
    print("Transforming query / retrieving more docs...")
    state.setdefault("retrieved_docs", [])
    state["retrieved_docs"].append("fallback_proc")
    return state


def append_to_dictionary(state: WorkflowState) -> WorkflowState:
    print("Appending final response to dictionary...")
    state.setdefault("dictionary", {})
    state["dictionary"]["last_response"] = state["response"]
    return state


# --- Build LangGraph workflow ---

workflow = StateGraph(WorkflowState)

# Nodes
workflow.add_node("upload_cobol", upload_cobol_files)
workflow.add_node("upload_copybooks", upload_copybooks)
workflow.add_node("extract_fields", extract_fields_from_copybooks)
workflow.add_node("embedding", embed_documents)
workflow.add_node("ingest_ai_search", ingest_into_ai_search)
workflow.add_node("store_dictionary", store_field_dictionary)
workflow.add_node("ai_search", ai_search)
workflow.add_node("generate_response", generate_response)
workflow.add_node("validate", validate_response)
workflow.add_node("query_transform", query_transform)
workflow.add_node("append_dictionary", append_to_dictionary)

# Edges based on your diagram
workflow.set_entry_point("upload_cobol")
workflow.add_edge("upload_cobol", "embedding")
workflow.add_edge("embedding", "ingest_ai_search")

workflow.add_edge("upload_copybooks", "extract_fields")
workflow.add_edge("extract_fields", "store_dictionary")

workflow.add_edge("ingest_ai_search", "ai_search")
workflow.add_edge("store_dictionary", "ai_search")

workflow.add_edge("ai_search", "generate_response")
workflow.add_edge("generate_response", "validate")

# Validation branch
workflow.add_conditional_edges(
    "validate",
    lambda state: "yes" if state["valid"] else "no",
    {
        "yes": "append_dictionary",
        "no": "query_transform"
    }
)

workflow.add_edge("query_transform", "ai_search")
workflow.add_edge("append_dictionary", END)

graph = workflow.compile()


# --- Run workflow demo ---
if __name__ == "__main__":
    state = graph.invoke({})
    print("\n--- FINAL STATE ---")
    print(state)
