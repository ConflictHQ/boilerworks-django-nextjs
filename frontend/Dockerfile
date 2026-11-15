# The production web image (the Astrolift web workload in astrolift.toml).
# Next.js standalone output on Node; Dockerfile.dev is the compose dev server.
#
#   docker build -t app-web --build-arg NEXT_PUBLIC_API_ROOT=https://api.example.com frontend
#   docker run --rm -p 3000:3000 app-web

# --- Build stage ---
FROM node:24-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .

# NEXT_PUBLIC_* values are compiled into the browser bundle, so they are
# build arguments: the backend's public URL (no trailing slash) and the
# page a signed-in person lands on.
ARG NEXT_PUBLIC_API_ROOT=http://localhost:8000
ARG NEXT_PUBLIC_MAIN_PAGE=/dashboard
ENV NEXT_PUBLIC_API_ROOT=$NEXT_PUBLIC_API_ROOT \
    NEXT_PUBLIC_MAIN_PAGE=$NEXT_PUBLIC_MAIN_PAGE \
    NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- Production stage ---
FROM node:24-alpine

WORKDIR /app
RUN addgroup -S -g 1001 nodejs && adduser -S -u 1001 -G nodejs nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000
ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0 \
    NEXT_TELEMETRY_DISABLED=1

CMD ["node", "server.js"]
