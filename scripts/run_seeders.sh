#!/bin/bash

SEEDERS_DIR="scripts/seeders"

echo "🌱 Running database seeders in dependency order..."

# Run the master seeder script that handles all dependencies
python3 "$SEEDERS_DIR/run_all_seeders.py"

if [ $? -eq 0 ]; then
    echo "✅ All seeders executed successfully!"
else
    echo "❌ Some seeders failed. Please check the output above."
    exit 1
fi
