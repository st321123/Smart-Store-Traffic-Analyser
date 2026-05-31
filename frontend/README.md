# Smart Store Traffic — Frontend

This is a lightweight Vite + React UI for interacting with the backend Chat API.

Quickstart

1. Install dependencies

```bash
cd frontend
npm install
```

2. Start dev server

```bash
npm run dev
```

3. Configure backend URL

Copy `.env.example` to `.env` and adjust `VITE_API_URL` if your backend runs on a different host/port.

Usage

- Open http://localhost:5173
- Enter a natural language query and press `Send`.

Notes

- The UI calls `POST ${VITE_API_URL}/chat` and `GET ${VITE_API_URL}/health`.
- For production build run `npm run build` and serve the `dist/` directory.
