// Additional resources can be defined here
// This file is a placeholder for future resource additions such as:
// - Application Insights for monitoring
// - Key Vault for secrets management
// - Storage Account for API logs
// - Virtual Network for network isolation

// Example structure for future resources:
/*
param apimServiceName string
param location string
param tags object

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${apimServiceName}-insights'
  location: location
  kind: 'web'
  tags: tags
  properties: {
    Application_Type: 'web'
    RetentionInDays: 90
  }
}

output appInsightsId string = appInsights.id
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
*/
