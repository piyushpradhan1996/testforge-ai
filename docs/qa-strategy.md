# QA Strategy

This project is intentionally small, so the test strategy focuses on high-value risks rather than broad tooling.

## Risk Areas

| Risk | Why It Matters | Current Coverage |
| --- | --- | --- |
| Invalid requirement payloads | Bad inputs should fail clearly and not write junk data | FastAPI/Pydantic validation test |
| Provider configuration | Portfolio reviewers should be able to run the app without keys | Mock fallback tests |
| Deterministic generation | CI should not depend on nondeterministic AI output | Mock provider determinism test |
| Persistence | Saved generations must be retrievable and ordered predictably | History and detail endpoint tests |
| Export quality | Markdown output is a primary deliverable | Export endpoint section/header tests |
| Frontend workflow | The main user journey must work from form to results | React Testing Library generate-flow test |
| History navigation | Saved outputs are part of the MVP value | Frontend history test |
| RAG relevance | Supporting docs should influence generation | Document indexing and retrieved-context tests |
| LLM guardrails | Generated output should be structured and reviewable | Duplicate, missing-section, and endpoint checks |
| Evals | QA output should be scored consistently | Fixture-based eval runner tests |

## Automated Checks

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

A GitHub Actions template for these checks is included at `docs/github-actions-ci.yml`.

Local browser smoke test:

```bash
cd frontend
npm run test:e2e
```

Run it while the backend and frontend are already running.

## Manual Smoke Test Charter

1. Start the backend and frontend.
2. Generate QA output using `docs/sample-input.json`.
3. Confirm each output section is populated:
   - Positive test cases
   - Negative test cases
   - Edge cases
   - API test scenarios
   - Bug report draft
   - QA checklist
4. Copy Markdown and confirm it includes all major headings.
5. Download Markdown and verify the filename is based on the generation title.
6. Open History and confirm the newest generation appears first.
7. Open a saved generation from History and compare it with the original result.
8. Submit a blank required field and confirm validation blocks submission.
9. Add supporting context and confirm the result shows retrieved context and model metadata.
10. Run the Eval Dashboard and confirm coverage scores render.

## Deliberate Non-Goals

- No paid AI dependency in tests.
- No authentication, authorization matrix, or role-based data isolation.
- No browser E2E test yet, because the MVP already has backend contract tests and frontend component-flow tests.
- No load or performance testing, because this is a local portfolio MVP with SQLite.
- No paid embedding dependency; RAG uses keyword retrieval for repeatable local behavior.

## Good Next Test Additions

- Playwright smoke test against running backend and frontend.
- Contract fixture test that compares Markdown export against a saved approved snapshot.
- Accessibility checks for form labels, focus states, and keyboard navigation.
