# Development Workflow

## Branching Strategy

This project implements a structured Git workflow to ensure code stability and streamlined deployments.

### Main Branches

#### develop
- Primary branch for active development.
- Integration point for all feature branches.
- Configuration: `docker-compose.dev.yml`
- Dockerfiles: `Dockerfile.dev`
- Runtime characteristics:
  - Hot reload enabled.
  - Source code volumes mounted for real-time updates.
  - Backend execution as root for SELinux compatibility.
  - Frontend configured with HMR (Hot Module Replacement).

#### main
- Stable branch for production-ready code.
- Deployment target for released versions.
- Configuration: `docker-compose.prod.yml`
- Dockerfiles: `Dockerfile.prod`
- Runtime characteristics:
  - Static builds.
  - No source code volumes.
  - Backend execution as non-privileged user.
  - Optimized frontend assets.

---

## Development Cycle

### 1. Feature Implementation
1. Ensure the `develop` branch is up to date: `git pull origin develop`.
2. Create a specific feature branch: `git checkout -b feature/description`.
3. Commit changes following Conventional Commits (see below).
4. Push the branch and initiate a Pull Request to `develop`.

### 2. Bug Resolution
1. Create a fix branch from `develop`: `git checkout -b fix/description`.
2. Implement the correction and verify functionality.
3. Push the branch and initiate a Pull Request to `develop`.

### 3. Production Release
1. Merge the stable `develop` branch into `main`.
2. Apply a version tag: `git tag -a vX.Y.Z -m "Release description"`.
3. Push `main` and tags to the remote repository.

---

## Commit Conventions

All commits must adhere to the Conventional Commits specification:

- `feat:` New feature implementation.
- `fix:` Bug correction.
- `docs:` Documentation updates.
- `style:` Formatting or UI changes without logic modification.
- `refactor:` Code restructuring.
- `perf:` Performance optimizations.
- `test:` Test additions or updates.
- `chore:` General maintenance or construction tasks.

Example: `feat: implement Ed25519 signature verification`

---

---

## Service Workflow

The project operates through the interaction of several independent services coordinated via Docker Compose.

### Request Flow
1. **Entry Point**: All external traffic is received by the **Nginx** reverse proxy on port 80.
2. **Routing**:
    - Requests to `/` are routed to the **Astro Frontend**.
    - Requests to `/api/*` are routed to the **FastAPI Backend**.
    - Requests to `/_matrix/*` and `/_synapse/*` are routed to **Synapse**.
3. **Frontend logic**: The **Astro** application serves the UI and performs client-side cryptographic operations (Ed25519 signatures).
4. **Backend logic**: The **FastAPI** server manages business logic, user session state, and interfacing with the Matrix API.
5. **Core Services**:
    - **Synapse** handles the Matrix protocol, federation, and messaging.
    - **MariaDB** provides persistent storage for both Synapse and the Backend.
    - **Redis** is utilized for caching and session management.

### Authentication Workflow
1. Client requests an authentication challenge from the Backend.
2. Backend generates a challenge and transmits it to the Client.
3. Client signs the challenge locally using their private key and sends the signature to the Backend.
4. Backend verifies the signature against the stored public key in MariaDB.
5. Upon successful verification, the Backend issues a JWT and initializes the Matrix session.

---

## Privacy and Security Architecture

The application is designed with a "Privacy by Default" philosophy, ensuring that user identity and data remain under the complete control of the administrator and the users themselves.

### Cryptographic Identity Control
- **Ed25519 Key Pairs**: Authentication is based on Ed25519 elliptic curve cryptography. Access is not granted via passwords but through verified ownership of a private key.
- **Local Signing**: Private keys are never transmitted to the server. Authentication challenges are signed locally within the user's browser environment.
- **Authorized Keys**: The server only stores the public component of the key pair. 

### Identity and Anonymity
- **No Real Names**: The system does not require or store real names. User identities within the Matrix ecosystem are derived from the registered public keys, ensuring pseudonymity.
- **Controlled Discovery**: Users are not discoverable via public directories. Communication requires explicit knowledge of the target's Matrix User ID or public key alias.
- **Local Infrastructure**: By hosting the Synapse server locally, all metadata and message content remain within the controlled infrastructure, preventing third-party data harvesting.

### Session and Access Management
- **Immediate Revocation**: Access can be terminated instantly by revoking the associated public key on the server. This invalidates future authentication attempts and terminates active sessions.
- **Session Isolation**: Each login session generates a unique JWT with a defined expiration period, ensuring that access is temporary and must be re-validated periodically.
- **VPN Restricted Access**: (Optional) The infrastructure is prepared for WireGuard integration, allowing the administrator to restrict the entire service to a private network, ensuring that only users with VPN credentials can reach the entry point.

---

## Deployment Procedures

### Development Environment
To deploy the development stack, use the following commands:
```bash
make dev
# or
./deploy.sh dev
# or (default)
docker-compose up -d
```

### Production Environment
To deploy the production stack, use the following commands:
```bash
make prod
# or
./deploy.sh prod
# or
docker-compose -f docker-compose.prod.yml up -d
```


