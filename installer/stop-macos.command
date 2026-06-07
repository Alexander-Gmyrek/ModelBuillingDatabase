#!/bin/zsh
set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

clear
echo "Health Insurance Billing Database"
echo "---------------------------------"
echo ""
echo "This will stop the local app containers without deleting database data."
echo ""

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker was not found. There is nothing this launcher can stop."
  echo ""
  read "REPLY?Press Enter to close."
  exit 1
fi

cd "$PROJECT_DIR" || exit 1

echo "Stopping the app..."
docker compose down
if [ $? -ne 0 ]; then
  echo ""
  echo "The app did not stop cleanly. Open Docker Desktop and stop the containers named billing-db, backend, and frontend."
  echo ""
  read "REPLY?Press Enter to close."
  exit 1
fi

echo ""
echo "The app is stopped. Your database data is still saved in Docker."
echo ""
read "REPLY?Press Enter to close."
