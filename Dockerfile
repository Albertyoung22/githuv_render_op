FROM python:3.11-alpine

WORKDIR /usr/src/app

COPY . .

ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "python3 -m http.server ${PORT:-10000}"]
