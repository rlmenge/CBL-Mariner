#!/bin/bash
set -euxo pipefail

SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- Configuration ---
SUBSCRIPTION_ID="b8f169b2-5b23-444a-ae4b-19a31b5e3652"
RESOURCE_GROUP_NAME="rachel-azl4-test-rg"
GALLERY_NAME="rachelazl4gallery"
GALLERY_IMAGE_DEFINITION="azl4-vm-base-aarch64"
IMAGE_VERSION="0.1.0"
LOCATION="westus3"
REPLICATION_MODE="Full"

# Storage account for the uploaded VHD (in your RG)
STORAGE_ACCOUNT_NAME="rachelazl4imageswestus3"
STORAGE_CONTAINER_NAME="azl4-vhds"

# Local VHD file (downloaded via azcopy from Tobias' managed disk)
VHD_FILE="./AzureLinuxAlpha1-arm64-0.1.0.vhd"
STORAGE_BLOB_NAME="$(basename "$VHD_FILE")"

# --- Step 0: Validate VHD exists ---
if [ ! -f "$VHD_FILE" ]; then
    echo "ERROR: VHD file not found: $VHD_FILE"
    echo ""
    echo "Download it first:"
    echo "  1. az disk grant-access \\"
    echo "       --resource-group tobiasb-alpha1-disk-westus3 \\"
    echo "       --name AzureLinuxAlpha1-arm64-0.1.0-disk \\"
    echo "       --duration-in-seconds 3600 --access-level Read"
    echo "  2. azcopy copy '<sas-url>' $VHD_FILE"
    exit 1
fi

# --- Step 1: Set subscription ---
az account set --subscription "$SUBSCRIPTION_ID"

# --- Step 2: Ensure storage account exists ---
STORAGE_ACCOUNT_ID="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP_NAME/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"

if ! az storage account show --ids "$STORAGE_ACCOUNT_ID" -o none 2>/dev/null; then
    echo "Creating storage account $STORAGE_ACCOUNT_NAME..."
    az storage account create \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --name "$STORAGE_ACCOUNT_NAME" \
        --location "$LOCATION" \
        --allow-shared-key-access false
fi

# --- Step 3: Ensure storage container exists ---
containerExists=$(az storage container exists \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --name "$STORAGE_CONTAINER_NAME" \
    --auth-mode login | jq -r .exists)

if [ "$containerExists" != "true" ]; then
    echo "Creating container $STORAGE_CONTAINER_NAME..."
    az storage container create \
        --account-name "$STORAGE_ACCOUNT_NAME" \
        --name "$STORAGE_CONTAINER_NAME" \
        --auth-mode login
fi

# --- Step 4: Upload VHD as page blob ---
echo "Uploading VHD to storage account..."
az storage blob upload \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --container-name "$STORAGE_CONTAINER_NAME" \
    --name "$STORAGE_BLOB_NAME" \
    --file "$VHD_FILE" \
    --type page \
    --auth-mode login \
    --overwrite

SOURCE_VHD_URI="https://$STORAGE_ACCOUNT_NAME.blob.core.windows.net/$STORAGE_CONTAINER_NAME/$STORAGE_BLOB_NAME"
echo "VHD uploaded to: $SOURCE_VHD_URI"

# --- Step 5: Ensure arm64 image definition exists ---
imageDefinitionExists=$(az sig image-definition list \
    -r "$GALLERY_NAME" \
    -g "$RESOURCE_GROUP_NAME" \
    --query "[?name=='$GALLERY_IMAGE_DEFINITION'].name" -o tsv)

if [ -z "$imageDefinitionExists" ]; then
    echo "Creating arm64 image definition '$GALLERY_IMAGE_DEFINITION'..."
    az sig image-definition create \
        --gallery-image-definition "$GALLERY_IMAGE_DEFINITION" \
        --publisher "AzureLinux" \
        --offer "AzureLinux4" \
        --sku "$GALLERY_IMAGE_DEFINITION" \
        --gallery-name "$GALLERY_NAME" \
        --resource-group "$RESOURCE_GROUP_NAME" \
        --location "$LOCATION" \
        --os-type Linux \
        --architecture Arm64 \
        --hyper-v-generation V2
fi

# --- Step 6: Deploy image version ---
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
                 sourceStorageAccountId="$STORAGE_ACCOUNT_ID" \
                 sourceVhdUri="$SOURCE_VHD_URI" \
                 replicationMode="$REPLICATION_MODE"

echo "Successfully published arm64 image version $IMAGE_VERSION to $GALLERY_NAME/$GALLERY_IMAGE_DEFINITION"
