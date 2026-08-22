FROM node:20-alpine

WORKDIR /app

# Instala dependências primeiro para cache
COPY package*.json ./
RUN npm install

# Copia o código
COPY . .

# Em dev, o Next.js usa a porta 3000
EXPOSE 3000

CMD ["npm", "run", "dev"]