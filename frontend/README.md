# Frontend App

Next.js 16 (App Router) + TypeScript, Apollo Client, Auth0, Tailwind CSS + shadcn/ui.

## Prerequisites

- Node.js 20+
- npm

## Setup

**1. Install dependencies**

```bash
npm install
```

**2. Configure environment variables**

```bash
cp .env.example .env
```

Then fill in the values in `.env`:

| Variable                 | Description                                                                          |
| ------------------------ | ------------------------------------------------------------------------------------ |
| `NEXT_PUBLIC_API_ROOT`   | Backend API base URL                                                                 |
| `NEXT_PUBLIC_API_TOKEN`  | Static bearer token for API requests                                                 |
| `NEXT_PUBLIC_MAIN_PAGE`  | Default redirect after login (e.g. `/dashboard`)                                     |
| `APP_BASE_URL`           | Public URL of this app (used by Auth0 callbacks)                                     |
| `AUTH_REDIRECT_URL`      | Auth0 redirect URL after login                                                       |
| `AUTH0_SECRET`           | Random secret for Auth0 session encryption — generate with `openssl rand -base64 32` |
| `AUTH0_DOMAIN`           | Auth0 tenant domain (e.g. `your-tenant.us.auth0.com`)                                |
| `AUTH0_CLIENT_ID`        | Auth0 application client ID                                                          |
| `AUTH0_CLIENT_SECRET`    | Auth0 application client secret                                                      |
| `METABASE_SITE_URL`      | _(optional)_ Metabase instance URL                                                   |
| `METABASE_SECRET_KEY`    | _(optional)_ Metabase embedding secret key                                           |
| `SENTRY_AUTH_TOKEN`      | _(optional)_ Sentry auth token for source map uploads                                |
| `NEXT_PUBLIC_SENTRY_DSN` | _(optional)_ Sentry DSN                                                              |

## Running

```bash
# Development (with hot reload)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

```bash
# Production build
npm run build
npm run start
```

## Other commands

```bash
npm run lint          # ESLint
npm run format        # Prettier (rewrite in-place)
npm run format:check  # Prettier (CI check)
```
