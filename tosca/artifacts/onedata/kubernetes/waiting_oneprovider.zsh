#!/bin/zsh
while true; do 
onepanel-rest-cli getProviderClusterIps | jq -r '.isConfigured' > /res || echo "ERROR: Some problem executing onepanel-rest-cli" ;
if [ "$(cat /res)" = "true" ]; then 
    echo "Oneprovider is configured!"; 
    break ; 
else 
    echo -e "Configuring Oneprovider:\n$(cat /res)"; 
fi; 
sleep 30;  
done