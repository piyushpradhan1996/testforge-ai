# TestForge AI Frontend

React + Vite + TypeScript frontend for the TestForge AI MVP.

## Run

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` and expects the backend at `http://localhost:8000`.

To point the frontend at another API URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Build

```bash
npm run build
```

## Tests

```bash
npm test
```

The frontend tests use Vitest, jsdom, and React Testing Library. They cover form rendering, generate flow, results display, history navigation, and Markdown copy behavior with mocked API responses.

## E2E Smoke Test

Start the backend and frontend, then run:

```bash
npm run test:e2e
```

## Screenshots

Start the backend and frontend, then run:

```bash
npm run screenshots
```

Screenshots are written to `../docs/screenshots`.

## LLM/RAG UI Additions

- Generate page includes optional supporting context that is passed into generation as inline retrieved context.
- Results page displays retrieved context, model metadata, and guardrail results.
- Evals page runs the backend evaluation harness and displays coverage scores.
