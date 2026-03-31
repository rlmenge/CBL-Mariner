#!/bin/bash
set -euxo pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- Configuration ---
SUBSCRIPTION_ID="b8f169b2-5b23-444a-ae4b-19a31b5e3652"
RESOURCE_GROUP_NAME="rachel-azl4-test-rg"
GALLERY_NAME="rachelazl4gallery"
GALLERY_IMAGE_DEFINITION="azl4-vm-base-x86_64"
IMAGE_VERSION="0.1.0"
LOCATION="westus3"

# Source VHD (already uploaded)
SOURCE_VHD_URI="https://tobiasbazl4imageswestus3.blob.core.windows.net/azl4-vhds/azl4-vm-base.x86_64-20260320-195827.vhdfixed"
SOURCE_STORAGE_ACCOUNT_NAME="tobiasbazl4imageswestus3"
REPLICATION_MODE="Full"

# --- Script ---
az account set --subscription "$SUBSCRIPTION_ID"

# Resolve the storage account resource ID
SOURCE_STORAGE_ACCOUNT_ID=$(az storage account show \
    --name "$SOURCE_STORAGE_ACCOUNT_NAME" \
    --query "id" -o tsv)

echo "Storage account resource ID: $SOURCE_STORAGE_ACCOUNT_ID"

# Ensure the image definition exists
imageDefinitionExists=$(az sig image-definition list \
    -r "$GALLERY_NAME" \
    -g "$RESOURCE_GROUP_NAME" \
    --query "[?name=='$GALLERY_IMAGE_DEFINITION'].name" -o tsv)

if [ -z "$imageDefinitionExists" ]; then
    echo "Creating image definition '$GALLERY_IMAGE_DEFINITION' in gallery '$GALLERY_NAME'..."
    az sig image-definition create \
        --gallery-image-definition "$GALLERY_IMAGE_DEFINITION" \
        --publisher "AzureLinux" \
        --offer "AzureLinux4" \
        --sku "$GALLERY_IMAGE_DEFINITION" \
        --gallery-name "$GALLERY_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$LOCATION" \
        --os-type Linux \
        --hyper-v-generation V2
fi

# Create the image version from the existing VHD
REGIONS_JSON="[\"$LOCATION\"]"

az deployment group create \
    --name "${GALLERY_IMAGE_DEFINITION}-${IMAGE_VERSION}" \
    --resource-group "$RESOURCE_GROUP_NAME" \
    --template-file "$SCRIPTS_DIR/azure-gallery-image-base.bicep" \
    --parameters galleryName="$GALLERY_NAME" \
                 imageDefinitionName="$GALLERY_IMAGE_DEFINITION" \
                 versionName="$IMAGE_VERSION" \
                 location="$LOCATION" \
                 regions="$REGIONS_JSON" \
                 sourceStorageAccountId="$SOURCE_STORAGE_ACCOUNT_ID" \
                 sourceVhdUri="$SOURCE_VHD_URI" \
                 replicationMode="$REPLICATION_MODE"

echo "Successfully published image version $IMAGE_VERSION to $GALLERY_NAME/$GALLERY_IMAGE_DEFINITION"
