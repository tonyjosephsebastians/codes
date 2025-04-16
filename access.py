from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from azure.search.documents.indexes.models import SimpleField, SearchFieldDataType
from azure.core.credentials import AccessToken
from datetime import datetime, timedelta

# Custom token credential using CLI token
class ManualTokenCredential:
    def __init__(self, token: str, expires_in_minutes: int = 60):
        self._token = token
        self._expires_on = int((datetime.utcnow() + timedelta(minutes=expires_in_minutes)).timestamp())

    def get_token(self, *scopes, **kwargs):
        return AccessToken(self._token, self._expires_on)

# 🔁 Replace this with your actual token from Azure CLI
access_token = "<PASTE-YOUR-ACCESS-TOKEN-HERE>"

# 🔁 Replace with your actual service endpoint
search_endpoint = "https://<your-search-service-name>.search.windows.net"
index_name = "sample-index"

# Initialize the client
credential = ManualTokenCredential(access_token)
client = SearchIndexClient(endpoint=search_endpoint, credential=credential)

# Define the index
fields = [
    SimpleField(name="page_no", type=SearchFieldDataType.String, key=True, filterable=True),
    SimpleField(name="text", type=SearchFieldDataType.String, searchable=True, sortable=True),
]

index = SearchIndex(name=index_name, fields=fields)

# Create the index
try:
    client.create_index(index)
    print(f"✅ Index '{index_name}' created successfully!")
except Exception as e:
    print(f"❌ Failed to create index: {e}")
