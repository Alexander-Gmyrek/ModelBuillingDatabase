#!/bin/zsh
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_URL="http://localhost:8080/setup.html"
BACKEND_URL="http://localhost:3000/api"

clear
echo "Health Insurance Billing Database"
echo "---------------------------------"
echo ""
echo "This wizard will start the local database, API, and app UI."
echo ""

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker Desktop is required before this app can run."
  echo "Install Docker Desktop, start it, then run this wizard again."
  echo ""
  echo "Download: https://www.docker.com/products/docker-desktop/"
  echo ""
  read "REPLY?Press Enter to close."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed, but it is not running yet."
  echo "Start Docker Desktop, wait for it to finish loading, then run this wizard again."
  echo ""
  read "REPLY?Press Enter to close."
  exit 1
fi

cd "$PROJECT_DIR" || exit 1

echo "Starting the app. The first run can take a few minutes..."
docker compose up --build -d
if [ $? -ne 0 ]; then
  echo ""
  echo "The app did not start successfully. See the Docker output above."
  echo ""
  read "REPLY?Press Enter to close."
  exit 1
fi

echo ""
echo "Waiting for the API to respond..."
for i in {1..60}; do
  if curl -fsS "$BACKEND_URL" >/dev/null 2>&1; then
    echo "The app is ready."
    open "$FRONTEND_URL"
    echo ""
    echo "Opened $FRONTEND_URL"
    echo "You can close this window after the app opens."
    exit 0
  fi
  sleep 2
done

echo ""
echo "The containers started, but the API did not respond yet."
echo "Try these steps:"
echo "1. Wait one more minute, then refresh the setup page."
echo "2. Open Docker Desktop and check that billing-db, backend, and frontend are running."
echo "3. Make sure ports 8080, 3000, and 3307 are not being used by another app."
echo ""
echo "Setup page:"
echo "$FRONTEND_URL"
echo ""
read "REPLY?Press Enter to close."
