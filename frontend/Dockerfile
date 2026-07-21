# --- Estágio de build: compila o SPA com Vite ---
FROM node:20-slim AS build

WORKDIR /app

# Instala dependências primeiro (melhor cache de camadas).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# --- Estágio de runtime: serve os estáticos com nginx ---
FROM nginx:1.27-alpine

# Configuração que serve o SPA e faz proxy de /api para o backend.
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://localhost/ >/dev/null 2>&1 || exit 1

CMD ["nginx", "-g", "daemon off;"]
