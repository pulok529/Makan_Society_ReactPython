# Client Deployment Pack

This folder contains the scripts and notes needed to move the project to a client server.

## What to transfer

Minimum:

- the packaged project folder created by `make-client-pack.ps1`
- the latest database backup

Optional for offline servers:

- exported Docker images tar file

## Quick paths

If the client server has internet:

1. copy the packaged folder to the client server
2. copy `.env.client.template` to `.env`
3. update values in `.env`
4. run `03-start-stack.ps1`
5. run `04-restore-database.ps1`
6. run `05-check-stack.ps1`

If the client server is offline:

1. run `01-export-images.ps1` on your machine
2. copy the packaged folder and `society-modern-images.tar` to the client server
3. run `02-load-images.ps1`
4. copy `.env.client.template` to `.env`
5. update values in `.env`
6. run `03-start-stack-images.ps1`
7. run `04-restore-database.ps1`
8. run `05-check-stack.ps1`

## Important notes

- The current frontend expects the API at `http://localhost:8000`.
- If the client will use the system from other computers on the LAN, change `VITE_API_BASE_URL` in `.env` before starting containers.
- This pack does not copy your live `.env` secrets automatically.
- `docker-compose.images.yml` is the image-only startup file for offline deployment.
- The prepared backup included in the pack is:
  `SocietyApp_pre_client_cutover_20260508_151345.bak`

## Default URLs after start

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- SQL Server: `localhost,14334`
