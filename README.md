# PitchCraft Matchup Agent

Milestone 1 is a static, cache-first product shell for a capstone demo. It renders the provided JSON file at `public/data/pitchcraft-demo.json` with a typed Server Component data path and client-only Recharts chart wrappers.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- Recharts

## Local Development

```bash
npm run dev
```

Open `http://127.0.0.1:3000`.

## Verification

```bash
npm run lint
npm run build
```

The app does not call live APIs, LLMs, databases, auth services, or scheduled jobs in this milestone.
