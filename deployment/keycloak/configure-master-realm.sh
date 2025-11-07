#!/bin/bash
# Keycloak Master Realm SSL Configuration Script
# This script disables SSL requirement for the master realm in Keycloak
# Run this after Keycloak starts to allow HTTP access to admin console

set -e

echo "🔐 Configuring Keycloak master realm SSL settings..."

# Get the Keycloak container name
KEYCLOAK_CONTAINER=$(docker ps --filter "name=keycloak" --format "{{.Names}}" | head -n 1)

if [ -z "$KEYCLOAK_CONTAINER" ]; then
  echo "❌ Error: Keycloak container not found. Make sure it's running."
  exit 1
fi

echo "📦 Found Keycloak container: $KEYCLOAK_CONTAINER"

# Wait for Keycloak to be ready
echo "⏳ Waiting for Keycloak to be ready..."
sleep 20

# Detect kcadm.sh location (different in various Keycloak versions)
echo "� Detecting kcadm.sh location..."
if docker exec "$KEYCLOAK_CONTAINER" test -f /opt/keycloak/bin/kcadm.sh; then
  KCADM_PATH="/opt/keycloak/bin/kcadm.sh"
elif docker exec "$KEYCLOAK_CONTAINER" test -f /opt/jboss/keycloak/bin/kcadm.sh; then
  KCADM_PATH="/opt/jboss/keycloak/bin/kcadm.sh"
else
  echo "❌ Error: kcadm.sh not found in container"
  exit 1
fi

echo "✅ Found kcadm.sh at: $KCADM_PATH"

# Configure kcadm credentials
echo "📝 Configuring kcadm credentials..."
docker exec "$KEYCLOAK_CONTAINER" "$KCADM_PATH" config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password admin

# Update master realm to disable SSL requirement
echo "🔓 Disabling SSL requirement for master realm..."
docker exec "$KEYCLOAK_CONTAINER" "$KCADM_PATH" update realms/master \
  -s sslRequired=NONE

echo "✅ Master realm SSL configuration complete!"
echo "🌐 You can now access the admin console at: http://localhost:8090"
