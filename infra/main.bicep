targetScope = 'resourceGroup'

// Parameters
@description('The name of the API Management service')
param apimServiceName string

@description('The location for all resources')
param location string = resourceGroup().location

@description('The email address of the publisher')
param publisherEmail string

@description('The name of the publisher organization')
param publisherName string

@description('Tags to apply to all resources')
param tags object = {}

@description('Environment to deploy (sandbox or production)')
@allowed(['sandbox', 'production'])
param environment string = 'sandbox'

// Variables
var defaultTags = {
  environment: 'development'
  project: 'phoneappli-api-mcp-server'
}

var allTags = union(defaultTags, tags)

// Module: Deploy resources
module resources './resources.bicep' = {
  name: 'resources-deployment'
  params: {
    apimServiceName: apimServiceName
    location: location
    publisherEmail: publisherEmail
    publisherName: publisherName
    tags: allTags
    environment: environment
  }
}

// Outputs
@description('The name of the API Management service')
output apimServiceName string = resources.outputs.apimServiceName

@description('The resource ID of the API Management service')
output apimResourceId string = resources.outputs.apimResourceId

@description('The gateway URL of the API Management service')
output apimGatewayUrl string = resources.outputs.apimGatewayUrl

@description('The system assigned principal ID')
output systemAssignedPrincipalId string = resources.outputs.systemAssignedPrincipalId
