from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType, SearchableField
)
from azure.core.credentials import AzureKeyCredential, TokenCredential
from azure.identity import DefaultAzureCredential

# Replace with your values
search_service_name = "tonysearch"  # no https or domain
index_name = "docs-index"
endpoint = f"https://{search_service_name}.search.windows.net"

# Use managed identity / az login / VS Code auth
credential = DefaultAzureCredential()

# Use this client with AAD token
index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

# Define the index
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String)
]

index = SearchIndex(name=index_name, fields=fields)

# Create the index
try:
    result = index_client.create_index(index)
    print(f"Index created: {result.name}")
except Exception as e:
    print(f"Error: {e}")
