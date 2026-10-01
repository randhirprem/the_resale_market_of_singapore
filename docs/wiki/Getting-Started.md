# Getting started

[Wiki home](Home.md) · [Dashboard guide](Dashboard-Guide.md)

## Requirements

Use Node.js 20.19+ (or 22.12+) and Python 3.9+. Run commands from the project root. The app backend uses Python's standard library, so there are no application Python packages to install.

```sh
npm install
npm run build
npm start
```

Open **http://127.0.0.1:8000**. The first start imports root-level CSVs if `data/hdb.sqlite3` does not exist. Later starts reuse that database. Stop the server with Ctrl+C.

The local app does not require accounts or API keys. Online basemap tiles and optional Google Fonts require internet; local records and bundled planning-area geometry do not.

## Development

Keep `npm start` running in one terminal. Run `npm run dev` in a second terminal and open the Vite URL printed there. Vite forwards `/api` requests to port 8000. Rebuild with `npm run build` before using the production server to view changed frontend code.

Use `npm start -- --port 8001` for an alternate production port. The Vite proxy still targets 8000 unless changed in `vite.config.js`.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Browser cannot connect | Start the server and use the URL printed in the terminal. |
| Address already in use | Check whether the app is already running; use another port if needed. Do not stop an unidentified process. |
| Missing production assets / 404 at the root | Run `npm run build`, then restart the server. |
| Python not found | Install Python 3.9+ or set `HDB_PYTHON` to its executable path. |
| Old values after a CSV refresh | Stop the server, run `npm run import`, and restart to clear cached API responses. |
| Blank or unavailable basemap | Check internet access. Locally bundled planning-area geometry still provides geographic context. |
| No transactions | Widen the date range or change the town/flat type. Try Reset for the default 2024 view. |
| Invalid dates | Ensure From is before or equal to To and both use valid months. |

The server binds to localhost and is intended for local use, not public deployment.
