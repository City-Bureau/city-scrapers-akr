#!/bin/bash
echo "Starting akr_metro_regional_transit with proxy..."
env HTTP_PROXY="$HTTP_PROXY" HTTPS_PROXY="$HTTPS_PROXY" \
pipenv run scrapy crawl akr_metro_regional_transit -s LOG_ENABLED=True

echo "🚀 Starting other spiders WITHOUT proxy..."
pipenv run scrapy list | grep -v akr_metro_regional_transit | \
xargs -I {} pipenv run scrapy crawl {} -s LOG_ENABLED=True &

# Output to the screen every 9 minutes to prevent a travis timeout
# https://stackoverflow.com/a/40800348
export PID=$!
while [[ `ps -p $PID | tail -n +2` ]]; do
  echo 'Deploying'
  sleep 540
done
