# Client Jenkins Deployment

This project can be developed locally, pushed to Git, and deployed on the client PC by Jenkins using Docker.

## Recommended deployment model

- You write code on your machine.
- You push code to your Git repository.
- Jenkins on the client machine pulls the latest source.
- Jenkins runs `docker compose -f docker-compose.deploy.yml up -d --build`.
- SQL Server data stays inside the named Docker volume `society_modern_mssql_data`.
- Because the database is stored in a named volume, app publishes do not wipe client data.

## Important note about data safety

The database is already configured to use a named Docker volume:

- `society_modern_mssql_data:/var/opt/mssql`

That means:

- `docker compose up -d --build` is safe for app republish
- `docker compose down` is safe
- `docker compose down -v` is **not** safe for production because it removes volumes

Never use `down -v` on the client server unless you intentionally want to destroy database data.

## First-time server setup

### 1. Install prerequisites on client PC

- Docker Desktop
- Git
- Jenkins

Make sure Jenkins can run Docker commands. On Windows, this usually means Jenkins runs under a user that has Docker Desktop access.

### 2. Create a stable deployment folder

Recommended:

```powershell
C:\deploy\makan-society
```

Jenkins will publish into this folder.

### 3. Put environment file on the server

Create:

```powershell
C:\deploy\makan-society\.env
```

Start from `.env.example` and update production values.

Minimum important values:

```env
MSSQL_SA_PASSWORD=your-strong-password
MSSQL_DB=SocietyApp
MSSQL_HOST=mssql
MSSQL_PORT=1433
MSSQL_USER=sa
REDIS_URL=redis://redis:6379/0
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET_KEY=replace-with-a-long-random-secret
VITE_API_BASE_URL=http://SERVER_IP:8000
SMS_PROVIDER_MODE=simulated
BULKSMSBD_API_KEY=
BULKSMSBD_SENDER_ID=
BULKSMSBD_BASE_URL=https://bulksmsbd.net/api/
BULKSMSBD_TIMEOUT_SECONDS=15
BULKSMSBD_ENABLED=false
BULKSMSBD_DRY_RUN=true
```

If users will access the app from other PCs, replace `SERVER_IP` with the actual client server IP.

### 4. Put the database backup on the server

Recommended folder:

```powershell
C:\deploy\backups
```

Copy your prepared `.bak` file there.

### 5. Restore the database one time

Use:

```powershell
powershell -ExecutionPolicy Bypass -File C:\deploy\makan-society\deployment\jenkins\restore-database.ps1 `
  -BackupFile C:\deploy\backups\SocietyApp_pre_client_cutover_20260508_151345.bak `
  -SaPassword "your-strong-password"
```

This restore is only needed for first setup or when you intentionally want to replace the database.

## Jenkins job setup

## Recommended Jenkins style

- Pipeline job
- Use repo `Jenkinsfile`
- Trigger by webhook or manual build

### Jenkins source setup

- Point Jenkins to your Git repository
- Branch: your deployment branch, usually `main`

### First Jenkins run behavior

The pipeline will:

1. check out source
2. mirror files into `C:\deploy\makan-society`
3. verify `C:\deploy\makan-society\.env` exists
4. build Docker images from source
5. start or update containers with `docker-compose.deploy.yml`
6. run health checks

## Publish flow after first setup

After the initial database restore:

1. you code locally
2. commit and push to Git
3. Jenkins build runs
4. Jenkins rebuilds `api`, `worker`, and `frontend`
5. SQL Server container keeps using the same named volume
6. client data remains intact

## Commands you should use on the client server

### Normal publish

```powershell
docker compose -f C:\deploy\makan-society\docker-compose.deploy.yml up -d --build
```

### Check running services

```powershell
docker compose -f C:\deploy\makan-society\docker-compose.deploy.yml ps
```

### Stop services

```powershell
docker compose -f C:\deploy\makan-society\docker-compose.deploy.yml down
```

### Never run in production

```powershell
docker compose -f C:\deploy\makan-society\docker-compose.deploy.yml down -v
```

## Database backup strategy

Recommended:

- keep the live DB in Docker volume
- take scheduled `.bak` backups outside the container
- copy backups to a server folder outside Git

Suggested backup locations:

- `C:\deploy\backups`
- external drive
- cloud or NAS copy

## Good practice

- keep `.env` only on the server, not in Git
- keep `.bak` files out of Git
- restore database manually only when needed
- let Jenkins deploy app code only
- do not let Jenkins reset the DB on each publish

## Current limitation

This repo still uses development-style app containers for frontend and backend Dockerfiles. They can be deployed this way, but later we should harden them further for full production runtime optimization.
