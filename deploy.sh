#!/bin/bash

# WOL API Deployment Script
# This script deploys the WOL API Docker container to a remote server

set -e

REMOTE_HOST="svrclapp1.cloudwise.ca"
REMOTE_USER="cwappadmin"
REMOTE_DIR="~/docker/wol-api"
LOCAL_DIR="."

echo "Deploying WOL API to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}"

# Check if directory exists and create if needed
if ssh ${REMOTE_USER}@${REMOTE_HOST} "[ -d ${REMOTE_DIR} ]"; then
    echo "Directory exists - updating deployment..."
else
    echo "Creating new deployment directory..."
    ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_DIR}"
fi

# Copy all necessary files (respecting .gitignore)
echo "Copying files..."
rsync -av \
  --exclude-from='.gitignore' \
  --exclude='.git/' \
  --exclude='.gitignore' \
  docker-compose.yml \
  backend/ \
  scripts/ \
  data/ \
  ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/

# Deploy and start the containers
echo "Starting containers on remote server..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_DIR} && docker-compose down && docker-compose up -d --build"

echo "Deployment complete!"
echo "API should be available at: http://${REMOTE_HOST}:8000"
echo "Database available at: ${REMOTE_HOST}:5432"