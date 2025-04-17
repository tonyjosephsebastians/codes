az rest --method get \
    --url https://<your-openai-endpoint>.openai.azure.com/openai/models?api-version=2024-10-21 \
    --headers "Authorization=Bearer $(az account get-access-token --query accessToken -o tsv)" 
