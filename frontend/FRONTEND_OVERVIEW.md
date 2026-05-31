# Frontend Overview — Smart Store Traffic Analyzer

Generated: 2026-05-31

This document lists what was added to the frontend, how the pieces interact, and notes for running and extending the app.

## Summary
- Tech: Vite + React 18 + TypeScript + Tailwind CSS
- Purpose: a chat UI that sends queries to the backend `/chat` endpoint, displays responses, optionally shows SQL (from `/chat/sql`), and provides a modern, production-like layout.

## Files added / changed (high level)
- `src/components/NavBar.tsx` — Fixed top navigation bar (reusable component).
- `src/components/Button.tsx` — Small reusable button component (variants `primary|secondary`, sizes `sm|md`, loading state).
- `src/components/BottomBar.tsx` — Floating bottom input panel (sticky floating card with shadow and blur).
- `src/components/Chat.tsx` — Main chat UI and message list. Handles input, Enter-to-send, shows Thinking indicator, renders assistant/user messages, and hooks `Show SQL` flow.
- `src/components/ChatMessage` (in `Chat.tsx`) — Message bubble renderer with inline SQL action and SQL result block.
- `src/App.tsx` — Uses `NavBar` and reserves spacing for the floating `BottomBar`.
- `src/services/api.ts` — API helpers: `postChat`, `postChatSql`, `getHealth`.
- `index.html` — cleaned stylesheet link and relies on `src/main.tsx` importing `index.css`.
- `src/index.css` & `tailwind.config.cjs` & `postcss.config.cjs` — Tailwind configuration and base styles used app-wide.

## UI flow (runtime)
1. User focuses input (floating BottomBar) and types a query.
2. Pressing `Enter` (no shift) or clicking the Send button triggers `send()` in `Chat.tsx`.
   - The typed message is appended locally as a user message immediately.
   - `loading` state is set to true and a small `Thinking...` status is shown below the last user message.
3. Frontend calls `postChat(baseUrl, query)` (POST `/chat`).
4. When the backend responds, frontend appends an assistant message containing:
   - `response`: text shown in the assistant bubble.
   - `intent` and other metadata (rendered when present).
   - If backend includes an `sql` field in the `/chat` response, the assistant message gets `hasSql:true` and the SQL is displayed immediately.
   - Otherwise, a small `Show SQL` button appears at the bottom-right of the assistant bubble (small, `sm` size). Clicking it calls `postChatSql(baseUrl, originalQuery)`.
5. `postChatSql` fetches SQL and the returned SQL is shown in a rounded, dark panel below the assistant message.

## Component responsibilities
- `NavBar` — top-left app name, simple actions on the right.
- `Chat` — orchestrates messages, loading, sending, and fetch for SQL.
- `ChatMessage` — renders a single message bubble and the `Show SQL` control.
- `Button` — unified styles for `Send`, `Show SQL` buttons with `loading` fallback.
- `BottomBar` — floating card that holds the input and Send button; visually elevated with a shadow and backdrop blur.
- `services/api.ts` — single place for HTTP calls and error handling.

## Important UI behaviours & UX decisions
- Floating BottomBar: centered, rounded panel with `backdrop-blur` and `shadow-2xl`, so it does not push the page content and makes the input behave like ChatGPT's footer. Content area has extra `pb-40` to avoid overlap.
- Thinking indicator: small italic `Thinking...` line under the most-recent user message while waiting for assistant response.
- SQL UX: `Show SQL` button appears only when SQL is not present in the assistant response but is available from the backend via `/chat/sql`. If backend returns SQL directly in `/chat`, it renders immediately and no extra call is required.
- Send control: compact paper-plane SVG icon inside the reusable `Button`; supports `loading` and `disabled` states.
- Enter key: `Enter` sends (unless `Shift+Enter`).

## Backend contract (what frontend expects)
- POST /chat
  - Request body: `{ "query": "..." }`
  - Response (expected shape):
    {
      "response": "user-facing text",
      "intent": "rca|...",
      "entities": { ... },
      "root_causes": [...],
      // optional: backend may include SQL directly
      "sql": "SELECT ..."
    }

- POST /chat/sql
  - Request body: `{ "query": "..." }` (the original user query or assistant-provided extraction)
  - Response: `{ "sql": "SELECT ..." }` or HTTP error if not supported

Environment: Frontend uses `import.meta.env.VITE_API_URL` (fallback `http://localhost:8000`) — set `VITE_API_URL` when running locally to your backend host/port.

## Build & run (local)
From the repo root:
```bash
cd frontend
npm install
npm run dev    # dev server (Vite)
npm run build  # production build (outputs to dist/)
```

Open `http://localhost:5173` (or the Vite-provided local URL).

## Notes on styling and libraries
- Styling: Tailwind CSS — small `src/index.css` with Tailwind directives and a few base tweaks.
- Component library: current UI uses Tailwind + small custom components.
  - Recommendation: adopt a component library if you want out-of-the-box accessibility, icons, and components. Options:
    - Chakra UI (React) — accessible primitives + themeable components.
    - Headless UI + Radix + Tailwind — for composability and custom visuals.
    - Use Heroicons (already compatible with Tailwind) or Phosphor icons for consistent icons.

## Next improvements (recommended roadmap)
1. Accessibility: add ARIA attributes and keyboard focus management for the floating BottomBar.
2. Animation: add slide/fade for BottomBar and subtle micro-interactions for Send button.
3. Error handling: centralize error toasts for network failures.
4. Tests: component unit tests and an integration test that mocks `/chat` and `/chat/sql`.
5. Storybook: document `Button`, `NavBar`, `BottomBar` for rapid iteration.
6. Replace manual SVGs with an icon library (Heroicons) for consistency.

## Files to review for details
- `src/components/Chat.tsx` — main logic and message rendering
- `src/components/Button.tsx` — reusable button interface
- `src/components/BottomBar.tsx` — floating input panel
- `src/components/NavBar.tsx` — top navigation
- `src/services/api.ts` — API helpers

----
If you'd like, I can also:
- produce a short README inside `frontend/` that contains run steps and environment variables, or
- add Storybook and initial stories for `Button` and `BottomBar`.

If you want the sheet in a different format (CSV, XLSX), tell me which and I'll add it.
