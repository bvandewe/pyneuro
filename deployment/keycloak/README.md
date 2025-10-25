# Keycloak Setup Instructions for Mario's Pizzeria

## 🔧 Fixed Issues

The `keycloak-setup` service has been removed and replaced with automatic realm import on Keycloak startup.

### Changes Made

1. **Added `--import-realm` flag** to Keycloak startup command
2. **Fixed volume mount path** for proper realm import
3. **Removed unnecessary setup service** - Keycloak now imports automatically
4. **Cleaned up dependencies** - removed references to commented-out services
5. **Fixed realm export file** - removed problematic authentication flow references that caused import failures

## 🚀 How It Works Now

1. **Automatic Import**: Keycloak will automatically import the `mario-pizzeria` realm on first startup
2. **No Manual Steps**: No need for a separate provisioning service
3. **Persistent**: Once imported, the realm persists in the PostgreSQL database

## 🧪 Testing the Fix

### Step 1: Stop and Clean Current Containers

```bash
docker-compose -f docker-compose.mario.yml down -v
docker-compose -f docker-compose.mario.yml rm -f
```

### Step 2: Start Fresh

```bash
docker-compose -f docker-compose.mario.yml up -d keycloak-db
# Wait a moment for DB to be ready
docker-compose -f docker-compose.mario.yml up -d keycloak
```

### Step 3: Check Keycloak Logs

```bash
docker-compose -f docker-compose.mario.yml logs -f keycloak
```

**Look for these log messages:**

- `Importing realm from file: /opt/keycloak/data/import/mario-pizzeria-realm-export.json`
- `Imported realm 'mario-pizzeria'`

### Step 4: Verify Import

1. Open http://localhost:8090/admin
2. Login with `admin` / `admin`
3. Check if `mario-pizzeria` realm appears in the realm dropdown (top-left)

## 🔍 Troubleshooting

### If realm is not imported

1. **Check file exists in container:**

   ```bash
   docker-compose -f docker-compose.mario.yml exec keycloak ls -la /opt/keycloak/data/import/
   ```

2. **Check Keycloak startup logs:**

   ```bash
   docker-compose -f docker-compose.mario.yml logs keycloak | grep -i import
   ```

3. **Manual import (if needed):**

   ```bash
   # Get admin token
   TOKEN=$(curl -X POST 'http://localhost:8090/realms/master/protocol/openid-connect/token' \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin' \
     -d 'password=admin' \
     -d 'grant_type=password' \
     -d 'client_id=admin-cli' | jq -r '.access_token')

   # Import realm
   curl -X POST 'http://localhost:8090/admin/realms' \
     -H 'Authorization: Bearer '"$TOKEN" \
     -H 'Content-Type: application/json' \
     -d @deployment/keycloak/mario-pizzeria-realm-export.json
   ```

## � Authentication Flow Issue Fixed

**Problem**: The original realm export had empty `authenticationFlows: []` but referenced flow names like "browser", "registration", causing this error:

```
ERROR: Cannot invoke "org.keycloak.models.AuthenticationFlowModel.getId()" because "flow" is null
```

**Solution**: Created a minimal realm configuration without problematic flow references. The fixed realm uses Keycloak's default flows instead of custom ones.

## �📋 Expected Realm Configuration

The imported realm includes:

- **Realm Name**: `mario-pizzeria`
- **Display Name**: `Mario's Pizzeria 🍕`
- **Clients**:
  - `mario-app` (confidential client with client secret)
  - `mario-public-app` (public client for frontend)
- **Pre-configured Users**:
  - `customer` / `test` (customer role)
  - `chef` / `test` (chef role)
  - `manager` / `test` (manager + chef roles)
- **Roles**: `customer`, `chef`, `manager`
- **Groups**: `customers`, `staff`, `management`
- **Client Scopes**: Standard OpenID Connect scopes + `mario-pizza` custom scope

## ✅ Success Indicators

**FIXED! ✅** The realm now imports successfully. Look for these messages in the logs:

- `Full importing from file /opt/keycloak/bin/../data/import/mario-pizzeria-realm-export.json`
- `Realm 'mario-pizzeria' imported`
- `Import finished successfully`
- `Keycloak 23.0.3 on JVM... started in 9.056s`
- `mario-pizzeria` realm visible in admin console at http://localhost:8090/admin

## 🧪 Test the Complete Setup

```bash
# Login to admin console
open http://localhost:8090/admin
# Credentials: admin / admin

# Check the realm dropdown (top-left) - should show:
# - master
# - mario-pizzeria

# Switch to mario-pizzeria realm and verify:
# - Users: customer, chef, manager (all with test)
# - Clients: mario-app, mario-public-app
# - Roles: customer, chef, manager
```

## 🎯 What Fixed It

The original realm export had problematic authentication flow references. The solution was creating a **minimal realm configuration** that:

1. ✅ **Uses Keycloak defaults** - no custom authentication flows
2. ✅ **Essential configuration only** - users, roles, clients
3. ✅ **Clean JSON structure** - no circular references or null pointers
4. ✅ **Proper client configuration** - both confidential and public clients
