# Synapse Setup - Initialization Guide

This directory contains the logic required to configure and manage the Matrix messaging server (Synapse). For the **SecChat** system to function, Synapse must be properly initialized and linked to the Backend via an Administrator Token.

## Prerequisites

1. A configured `.env` file in the project root (based on `.env.example`).
2. Docker and Docker Compose installed.
3. **(Optional)** The default domain `fed.local` should point to your local IP in the `/etc/hosts` file.

---

## Execution Order (Step-by-Step)

For a successful deployment, this order must be followed strictly:

### Step 1: Generate Base Configuration

> [!IMPORTANT]
> Before starting the containers, Synapse needs to generate its configuration files and signing keys.

```bash
./generate_config.sh
```

*This will create the `data/` folder containing the `homeserver.yaml` file.*

### Step 2: Start the Infrastructure

Bring up all services defined in the Compose file.

```bash
docker compose up -d
```

*Wait for `chatsender_synapse` and `chatsender_db` to appear as `(healthy)` before continuing.*

### Step 3: Register the Administrator User

You need a user with administrator privileges so that the Backend can manage the creation and deletion of ephemeral users.

```bash
./register_admin.sh
```

> *Follow the prompts to assign a username (e.g., `admin`) and a strong password.*

### Step 4: Obtain the Access Token (Admin Token)

The Backend requires the `SYNAPSE_ADMIN_TOKEN` to communicate with the Matrix API. This script performs the login and extracts the token.

```bash
./synapse_admin_setup.sh
```

> [!IMPORTANT]
> Copy the resulting token and paste it into your `.env` file in the `SYNAPSE_ADMIN_TOKEN` variable.

---

## Script Dictionary

| Script | Function | When to use it |
| --- | --- | --- |
| `generate_config.sh` | Creates the initial `homeserver.yaml`. | Only the first time (First run). |
| `register_admin.sh` | Registers an admin user in the DB. | After starting the containers. |
| `synapse_admin_setup.sh` | Obtains the Token via API (HTTPS). | Whenever the token expires or changes. |
| `cleanup_users.py` *Deprecated* | Purges expired users and messages. | Automated (Cron) or manual for cleanup. |

---

## Security and Nginx Notes

Due to the security configuration in the Reverse Proxy (Nginx):

1. **SSL/HTTPS**: Scripts targeting the API (`synapse_admin_setup.sh`) must use the `-k` flag in `curl` if you are using self-signed certificates.
2. **Browser Blocking**: Nginx blocks requests with a `text/html` header. Administration scripts work because `curl` sends API-compatible headers by default.
3. **Internal Access**: If you run scripts from outside the container, ensure you target `https://fed.local` instead of `localhost` so that Nginx recognizes the `server_name`.

---

### What's next?

Once you have pasted the `SYNAPSE_ADMIN_TOKEN` into your `.env`, restart the backend to load the new configuration:

```bash
docker compose restart backend
```