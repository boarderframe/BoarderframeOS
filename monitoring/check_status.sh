#!/bin/bash
# BoarderframeOS Monitoring Status

echo "BoarderframeOS Monitoring Status"
echo "================================"

# Check if monitoring services are running
echo -e "\nMonitoring Services:"
for service in metrics_collector health_monitor alert_manager; do
    if pgrep -f "$service.py" > /dev/null; then
        echo "✓ $service is running"
    else
        echo "✗ $service is not running"
    fi
done

# Check log files
echo -e "\nLog Files:"
for logfile in logs/boarderframeos.log logs/errors/errors.log; do
    if [ -f "$logfile" ]; then
        size=$(du -h "$logfile" | cut -f1)
        echo "✓ $logfile ($size)"
    else
        echo "✗ $logfile not found"
    fi
done

# Show recent alerts
echo -e "\nRecent Alerts:"
if [ -f "monitoring/alerts/alerts.log" ]; then
    tail -5 monitoring/alerts/alerts.log
else
    echo "No alerts log found"
fi

echo -e "\nMonitoring Dashboard: file://$(pwd)/monitoring/dashboard.html"
