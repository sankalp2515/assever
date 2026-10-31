FROM node:22-slim AS frontend
WORKDIR /console
COPY apps/console/package.json apps/console/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/console ./
ARG VITE_API_KEY=assever-public-readonly
ENV VITE_API_BASE="" VITE_API_KEY=$VITE_API_KEY VITE_PRODUCT_NAME=Assever
RUN npm run build

FROM nginx:1.28-alpine
COPY deploy/google/frontend-nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend /console/dist /usr/share/nginx/html
EXPOSE 8080
