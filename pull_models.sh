#!/bin/sh
# Script to pre-load required models into Ollama with verification
# POSIX-compliant for /bin/sh compatibility

set -e  # Exit on error

OLLAMA_URL="http://ollama:11434"

echo "Waiting for Ollama to start..."
RETRY_COUNT=0
MAX_RETRIES=30
until curl -s "$OLLAMA_URL/api/tags" >/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Ollama failed to start after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Attempt $RETRY_COUNT/$MAX_RETRIES: Waiting for Ollama..."
    sleep 2
done

echo "Ollama is ready!"
echo ""

# Function to pull and verify a model
pull_and_verify() {
    MODEL=$1
    ROLE=$2

    echo "Pulling $MODEL ($ROLE)..."

    # Pull the model
    curl -X POST "$OLLAMA_URL/api/pull" \
        -d "{\"name\": \"$MODEL\"}" \
        -H "Content-Type: application/json" \
        --silent --show-error

    echo ""
    echo "Verifying $MODEL..."

    # Verify the model is available
    if curl -s "$OLLAMA_URL/api/tags" | grep -q "$MODEL"; then
        echo "✓ $MODEL successfully installed"
        echo ""
        return 0
    else
        echo "ERROR: Failed to verify $MODEL"
        return 1
    fi
}

# Pull each model
pull_and_verify "llama3.1:8b" "Researcher" || exit 1
pull_and_verify "llama3.1:8b" "Generator" || exit 1
pull_and_verify "mistral:7b" "Auditor" || exit 1

echo ""
echo "All models pulled and verified successfully!"
echo ""
echo "Available models:"
curl -s "$OLLAMA_URL/api/tags" | grep -o '"name":"[^"]*"' | cut -d'"' -f4
