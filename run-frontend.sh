#!/usr/bin/env bash
# Sobe o frontend Community Link (Vite dev).
set -e
cd "$(dirname "$0")/frontend"
exec npm run dev
