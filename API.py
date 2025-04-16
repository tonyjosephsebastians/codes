# Using Azure CLI (recommended)
az search admin-key show --resource-group your-resource-group --service-name your-search-service-name

# Or using REST API
curl -X GET \
-H "Authorization: Bearer $(az account get-access-token --query accessToken -o tsv)" \
-H "Content-Type: application/json" \
"https://management.azure.com/subscriptions/your-subscription-id/resourceGroups/your-resource-group/providers/Microsoft.Search/searchServices/your-search-service-name/listAdminKeys?api-version=2020-08-01"
