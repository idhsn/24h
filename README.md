# Shared Grunge Portal Timer for OBS

A synchronized browser-source countdown for two or more OBS installations.

The design follows a black-and-white distressed stream-poster aesthetic with:

- compressed oversized typography
- vertical 24-hour/live labels
- torn paper edges
- a restrained red accent
- a moving scratched portal ring
- transparent OBS background

## URLs

After deployment, replace `YOUR-DOMAIN`:

- Overlay for both OBS installations: `https://YOUR-DOMAIN/overlay.html`
- Private control panel: `https://YOUR-DOMAIN/control.html`

Both overlays calculate from the same server-side end time and periodically correct their clocks, so they stay synchronized.

## Security

The public overlay cannot edit anything.

The control page requires the `ADMIN_KEY` environment variable. Set it to a long private password on your hosting platform. Enter it once in the control page; the browser stores it locally.

Share the key with your friend only if your friend should also control the timer.

## Local test on Windows

1. Install Python 3.
2. Extract the folder.
3. Double-click `START_LOCAL.bat`.
4. Open `http://127.0.0.1:8765/control.html`.
5. The local test admin key is `change-me`.


## Timer-only transparent mode

In the control panel, enable:

`Timer only — hide all background, portal, labels and title`

The OBS browser source will immediately switch to a transparent view containing only the countdown digits. Disable it to restore the full grunge poster and animated portal.

## OBS

On both computers:

1. Add **Browser Source**.
2. Use `https://YOUR-DOMAIN/overlay.html`.
3. Set width to `1920`.
4. Set height to `1080`.
5. Keep **Shutdown source when not visible** disabled.
6. Refresh both sources once after the initial deployment.

## Railway deployment

1. Create a GitHub repository.
2. Upload all files from this folder.
3. In Railway, create a project from the GitHub repository.
4. Generate a public domain for the service.
5. Add the variable `ADMIN_KEY` with a strong private value.
6. Add the variable `DATA_DIR=/data`.
7. Attach a Railway Volume to the service and mount it at `/data`.
8. Redeploy.
9. Use the generated Railway domain for the overlay and control URLs.

The volume keeps the countdown configuration through deployments and restarts.

## Render deployment

1. Create a GitHub repository and upload these files.
2. In Render, create a Python Web Service from the repository.
3. Build command: `pip install -r requirements.txt`
4. Start command:
   `gunicorn --workers 1 --threads 8 --timeout 0 --bind 0.0.0.0:$PORT app:app`
5. Add a secret environment variable named `ADMIN_KEY`.
6. For persistent state, attach a persistent disk at `/var/data`.
7. Add `DATA_DIR=/var/data`.
8. Deploy and use the service domain.

Without persistent storage, synchronization still works while the service is running, but settings can reset after a restart or redeployment.

## Files

- `app.py` — shared state API and web server
- `overlay.html` — public transparent OBS overlay
- `control.html` — password-protected controls
- `Dockerfile` — Railway/Fly/Docker deployment
- `railway.json` — Railway service configuration
- `render.yaml` — Render blueprint
