ACCESS_TOKEN=$(az account get-access-token --resource https://cognitiveservices.azure.com/ --query accessToken -o tsv)

az rest --method get \
  --url "https://<your-openai-endpoint>.openai.azure.com/openai/models?api-version=2024-10-21" \
  --headers "Authorization=Bearer $ACCESS_TOKEN"

