from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchFieldDataType, SearchableField
)
from azure.identity import DefaultAzureCredential

search_service_endpoint = "https://<your-search-service-name>.search.windows.net"
index_name = "docs-index"

# Authenticate with Managed Identity (DefaultAzureCredential)
credential = DefaultAzureCredential()
index_client = SearchIndexClient(endpoint=search_service_endpoint, credential=credential)

# Define the index schema
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
    SearchableField(name="content", type=SearchFieldDataType.String)
]
index = SearchIndex(name=index_name, fields=fields)

# Create the index
index_client.create_index(index)
