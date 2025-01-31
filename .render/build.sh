#!/usr/bin/env bash

# Update system and install stockfish
apt-get update
apt-get install -y stockfish

# Verify Stockfish installation
which stockfish
stockfish --version

# Make sure script exits with success
exit 0
