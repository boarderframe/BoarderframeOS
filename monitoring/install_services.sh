#!/bin/bash
# Install BoarderframeOS monitoring services

echo "Installing BoarderframeOS monitoring services..."

# Copy service files
sudo cp /Users/cosburn/BoarderframeOS/monitoring/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
for service in boarderframeos-metrics boarderframeos-health boarderframeos-alerts; do
    sudo systemctl enable $service
    sudo systemctl start $service
    echo "Started $service"
done

echo "Monitoring services installed and started!"
