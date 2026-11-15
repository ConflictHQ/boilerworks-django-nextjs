# The web app's Storybook as a static site, for its own private Astrolift app
# (storybook/astrolift.toml), composed into the Calliope AI UX front door.
# Builds from the repository root, like the manifest's build context:
#
#   docker build -f storybook/Dockerfile -t app-storybook .
#   docker run --rm -p 8080:8080 app-storybook

# Build: frontend/'s install, then its Storybook build.
FROM node:24-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build-storybook

# Serve: static files only, nginx as an unprivileged user on 8080.
FROM nginx:1.29-alpine
COPY storybook/nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/storybook-static /usr/share/nginx/html
USER 101:101
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1
