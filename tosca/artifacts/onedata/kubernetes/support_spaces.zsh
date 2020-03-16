#!/bin/zsh
# Obtain the Oneprovider ID
export _ONEPROVIDER_ID=$(onepanel-rest-cli getProvider | jq -r ".id")
echo "_ONEPROVIDER_ID=$_ONEPROVIDER_ID"

# Generate _SPACE_STORAGE_ID variable
for __STORAGE_ID in $(onepanel-rest-cli getStorages | jq ".ids" | jq -r '.[]' ); do 
    echo "__STORAGE_ID=$__STORAGE_ID"
    echo "name: $(onepanel-rest-cli getStorageDetails id=$__STORAGE_ID | jq -r ".name" )"
    onepanel-rest-cli getStorageDetails id=$__STORAGE_ID | case $(jq -r ".name") in $_SPACE_NAME) export _SPACE_STORAGE_ID=${__STORAGE_ID};; esac;
doneB_

echo  "_SPACE_STORAGE_ID=$_SPACE_STORAGE_ID"
onezone-rest-cli createSpaceSupportToken id=$_SPACE_ID | jq  .

# Support space
export _SPACE_SUPPORTTOKEN=$(onezone-rest-cli createSpaceSupportToken id=$_SPACE_ID | jq -r ".token")
echo  "_SPACE_SUPPORTTOKEN=$_SPACE_SUPPORTTOKEN"
onepanel-rest-cli supportSpace token==$_SPACE_SUPPORTTOKEN size:=$_SPACE_SIZE storageId==$_SPACE_STORAGE_ID
