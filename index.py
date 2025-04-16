from azure.identity import ManagedIdentityCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType, SearchableField
)

# Replace with your values
client_id = "<your-user-assigned-managed-identity-client-id>"
search_service_name = "tonysearch"
endpoint = f"https://{search_service_name}.search.windows.net"

# Authenticate with User Assigned Managed Identity
credential = ManagedIdentityCredential(client_id=client_id)

# Connect to the Search Index Client
index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

# Define the index schema
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String)
]
index = SearchIndex(name="docs-index", fields=fields)

# Create the index
try:
    result = index_client.create_index(index)
    print(f"Index created: {result.name}")
except Exception as e:
    print("Error creating index:", e)
