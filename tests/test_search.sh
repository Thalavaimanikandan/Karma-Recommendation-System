#!/bin/bash

API_URL="http://localhost:5000"

echo "🔍 Search Test Tool"
echo "=================="
echo ""

# Get user input
read -p "Enter your search text: " query

# URL encode the query
encoded_query=$(echo "$query" | sed 's/ /+/g')

echo ""
echo "🚀 Searching for: $query"
echo ""

# Call search API
response=$(curl -s "$API_URL/api/search?q=$encoded_query&user_id=production_user&limit=5")

# Check if response is empty
if [ -z "$response" ]; then
    echo "⚠️ Empty response from API"
    echo "{}"
else
    echo "$response" | python -m json.tool
fi


echo ""
echo "✅ Done!"
