#!/bin/bash

# URL for authentication service
export OS_AUTH_URL=http://10.0.2.15:5000/v2.0

# Tenant name
export OS_TENANT_NAME="demo"

# Username
export OS_USERNAME="demo"

# Password
echo "Please enter your OpenStack Password: "
read -sr OS_PASSWORD_INPUT
export OS_PASSWORD=$OS_PASSWORD_INPUT
