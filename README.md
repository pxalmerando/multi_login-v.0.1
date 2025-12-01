# url_scraper

A distributed URL scraper using MultiLogin-managed browser profiles + Selenium. Processes URL batches concurrently, detects CAPTCHAs, and reports progress via WebSockets.

## Quick facts
- Language: Python 3.11+
- Uses: MultiLogin (desktop + launcher API), Redis, Selenium, WebSockets
- Web app: FastAPI (uvicorn)

## Requirements
- Python 3.11+
- Redis (default: `redis://127.0.0.1:6379`)
- MultiLogin desktop app installed and running
- MultiLogin Launcher API reachable:
    - `BASE_URL=https://api.multilogin.com/`
    - `LAUNCHER_URL=https://launcher.mlx.yt:45001/`
- `.env` in project root (see `.env.example`)

## Environment variables (.env)
Place a `.env` file in the repository root. At minimum provide:
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `EMAIL` / `PASSWORD` (MultiLogin API credentials)

Use the provided `.env.example` as a template.

## Quick setup
1. Clone and install:
     ```
     git clone https://github.com/pxalmerando/multi_login-v.0.1.git
     cd multi_login-v.0.1
     pip install -r requirements.txt
     ```
2. Configure `.env` in the project root (use `.env.example`).
3. Ensure MultiLogin desktop app is running and Launcher API is reachable.
4. Start Redis (system service or `redis-server`).
5. Run the API:
     ```
     uvicorn app.main:app --reload
     ```

## Running the API & getting an auth token
Register or login (browser or curl):
- `http://127.0.0.1:8000/auth/register`
- `http://127.0.0.1:8000/auth/login`

Copy the returned token. The API auth flows use `app/security.py` and validators.

## Running a batch (WebSocket)
Connect to the WebSocket endpoint with the token:
```
ws://127.0.0.1:8000/ws/process_urls?token=<token-from-auth>
```

Send a JSON payload with URLs to process:
```json
{
    "urls": ["https://www.example.com"]
}
```

The server will process the batch concurrently using MultiLogin-managed Selenium profiles, detect CAPTCHAs, and stream progress updates and results back over the WebSocket.

WebSocket handlers live in:
- `app/api/websocket/`

## Notes
- Ensure MultiLogin desktop app is running and the Launcher API is reachable before starting scraper jobs.
- Redis is used for coordination/state; make sure the configured Redis URL is reachable.
- Use provided examples and config files as templates for production deployment.

## Troubleshooting
- If MultiLogin profiles fail to start, verify `LAUNCHER_URL` and that the desktop app allows API connections.
- If WebSocket connections fail, confirm token validity and that `uvicorn` is running.

For more details, inspect the `app/` package and `.env.example`.