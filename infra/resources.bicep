targetScope = 'resourceGroup'

// Parameters
@description('The name of the API Management service')
param apimServiceName string

@description('The location for all resources')
param location string

@description('The email address of the publisher')
param publisherEmail string

@description('The name of the publisher organization')
param publisherName string

@description('Tags to apply to all resources')
param tags object

@description('Environment to deploy (sandbox or production)')
@allowed(['sandbox', 'production'])
param environment string

@description('PHONE APPLI API Key')
@secure()
param phoneAppliApiKey string

// Module: API Management Service using Azure Verified Module (AVM)
module apimService 'br/public:avm/res/api-management/service:0.9.0' = {
  name: 'apim-deployment'
  params: {
    name: apimServiceName
    location: location
    tags: tags

    // SKU Configuration for Basic v2
    sku: 'BasicV2'
    skuCapacity: 1

    // Publisher information
    publisherEmail: publisherEmail
    publisherName: publisherName

    // Additional settings
    enableClientCertificate: false
    disableGateway: false

    // Managed Identity
    managedIdentities: {
      systemAssigned: true
    }

    // Named Values (for API keys)
    // Create a Named Value for the selected environment
    namedValues: [
      {
        name: environment == 'sandbox' ? 'phoneappli-api-key-sandbox' : 'phoneappli-api-key-production'
        displayName: environment == 'sandbox' ? 'phoneappli-api-key-sandbox' : 'phoneappli-api-key-production'
        secret: true
        value: phoneAppliApiKey
      }
    ]

    // Global API settings
    // Note: API-specific policies (including X-Pa-Api-Key header) are set at the API level during import
    policies: [
      {
        format: 'xml'
        value: '''
          <policies>
            <inbound>
              <cors allow-credentials="false">
                <allowed-origins>
                  <origin>*</origin>
                </allowed-origins>
                <allowed-methods>
                  <method>GET</method>
                  <method>POST</method>
                  <method>PUT</method>
                  <method>PATCH</method>
                  <method>DELETE</method>
                </allowed-methods>
                <allowed-headers>
                  <header>*</header>
                </allowed-headers>
              </cors>
            </inbound>
            <backend>
              <forward-request />
            </backend>
            <outbound />
            <on-error />
          </policies>
        '''
      }
    ]
  }
}

// Outputs
@description('The name of the API Management service')
output apimServiceName string = apimService.outputs.name

@description('The resource ID of the API Management service')
output apimResourceId string = apimService.outputs.resourceId

@description('The gateway URL of the API Management service')
output apimGatewayUrl string = 'https://${apimService.outputs.name}.azure-api.net'

@description('The system assigned principal ID')
output systemAssignedPrincipalId string = apimService.outputs.?systemAssignedMIPrincipalId ?? ''
