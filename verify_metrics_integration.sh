
# Quick verification that metrics are being used
grep -n "metrics_layer" corporate_headquarters.py | wc -l
echo "↑ Number of times metrics_layer is referenced"

grep -n "get_metric_value\|get_dashboard_summary_cards\|get_agent_cards_html\|get_department_cards_html" corporate_headquarters.py | wc -l  
echo "↑ Number of metric method calls"
