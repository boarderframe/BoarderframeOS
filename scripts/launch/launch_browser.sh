#!/usr/bin/env bash
# Launch script for the BoarderframeOS Department Browser

echo "🏢 BoarderframeOS Department Browser Launcher 🏢"
echo "---------------------------------------------"
echo "1) Launch Basic Browser (Simpler, faster loading)"
echo "2) Launch Enhanced Browser (With visualizations & analytics)"
echo "q) Quit"
echo "---------------------------------------------"

read -p "Select an option [1/2/q]: " option

case $option in
    1)
        echo "Launching Basic Department Browser..."
        streamlit run department_browser.py
        ;;
    2)
        echo "Launching Enhanced Department Browser..."
        streamlit run enhanced_department_browser.py
        ;;
    q|Q)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid option. Exiting."
        exit 1
        ;;
esac
