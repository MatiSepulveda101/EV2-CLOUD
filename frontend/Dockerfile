FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY angular.json ./
COPY tsconfig*.json ./
COPY public ./public
COPY src ./src

RUN npm run build -- --configuration production


FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/dist/CarritoCompra/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
