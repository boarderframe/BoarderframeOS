#!/bin/bash

# Advanced packet capture script to analyze HTTP traffic with tshark
# Focuses on finding the exact point where JSON gets converted to SSE

echo "🔍 Starting advanced packet capture with tshark..."
echo "Capturing all traffic on ports 8080, 9004, 8081, 9005"

# Kill any existing tcpdump processes
sudo pkill -f tcpdump
sleep 2

# Start comprehensive packet capture
echo "📦 Starting packet capture..."
sudo tshark -i lo0 -f "port 8080 or port 9004 or port 8081 or port 9005" \
    -Y "http" \
    -T fields \
    -e frame.number \
    -e frame.time \
    -e ip.src \
    -e ip.dst \
    -e tcp.srcport \
    -e tcp.dstport \
    -e http.request.method \
    -e http.request.uri \
    -e http.host \
    -e http.accept \
    -e http.content_type \
    -e http.response.code \
    -e http.transfer_encoding \
    -e http.connection \
    -E header=y \
    -E separator="|" \
    -E quote=d \
    -w /tmp/http_capture.pcap > /tmp/http_analysis.txt &

TSHARK_PID=$!
echo "tshark PID: $TSHARK_PID"

# Also run a raw HTTP content capture
echo "📝 Starting HTTP content capture..."
sudo tshark -i lo0 -f "port 8080 or port 9004" \
    -Y "http" \
    -T text \
    -V > /tmp/http_detailed.txt &

TSHARK_DETAIL_PID=$!
echo "Detailed capture PID: $TSHARK_DETAIL_PID"

# Monitor for specific patterns
echo "🔍 Starting pattern monitoring..."
sudo tshark -i lo0 -f "port 8080 or port 9004" \
    -Y 'http.content_type contains "event-stream" or http.accept contains "event-stream" or data contains "data:"' \
    -T fields \
    -e frame.time \
    -e http.content_type \
    -e http.accept \
    -e data \
    > /tmp/sse_patterns.txt &

PATTERN_PID=$!
echo "Pattern monitoring PID: $PATTERN_PID"

echo "🎯 Packet capture started. PIDs: $TSHARK_PID, $TSHARK_DETAIL_PID, $PATTERN_PID"
echo "   - Summary: /tmp/http_analysis.txt"
echo "   - Detailed: /tmp/http_detailed.txt"  
echo "   - SSE patterns: /tmp/sse_patterns.txt"
echo "   - Raw pcap: /tmp/http_capture.pcap"
echo ""
echo "⏰ Capture will run for 5 minutes, then analyze results..."

# Wait for 5 minutes of capture
sleep 300

# Stop all captures
echo "🛑 Stopping packet capture..."
sudo kill $TSHARK_PID $TSHARK_DETAIL_PID $PATTERN_PID 2>/dev/null
sleep 2

# Analyze the results
echo "📊 Analyzing captured traffic..."

echo "=== HTTP REQUEST/RESPONSE SUMMARY ==="
if [ -f /tmp/http_analysis.txt ]; then
    echo "Total HTTP packets captured:"
    wc -l < /tmp/http_analysis.txt
    
    echo -e "\nContent-Type headers:"
    grep -i "content-type" /tmp/http_analysis.txt | sort | uniq -c
    
    echo -e "\nAccept headers:"
    grep -i "text/event-stream" /tmp/http_analysis.txt || echo "No SSE Accept headers found"
    
    echo -e "\nResponse codes:"
    cut -d'|' -f8 /tmp/http_analysis.txt | grep -E '^[0-9]{3}$' | sort | uniq -c
fi

echo -e "\n=== SSE PATTERN ANALYSIS ==="
if [ -f /tmp/sse_patterns.txt ] && [ -s /tmp/sse_patterns.txt ]; then
    echo "SSE patterns found:"
    cat /tmp/sse_patterns.txt
else
    echo "No SSE patterns detected in traffic"
fi

echo -e "\n=== DETAILED ANALYSIS ==="
if [ -f /tmp/http_detailed.txt ]; then
    echo "Searching for data: prefixes in responses..."
    grep -n "data:" /tmp/http_detailed.txt | head -10
    
    echo -e "\nSearching for streaming indicators..."
    grep -i -E "(transfer-encoding|connection.*keep-alive|text/event-stream)" /tmp/http_detailed.txt
fi

echo -e "\n=== PCAP ANALYSIS WITH TSHARK ==="
if [ -f /tmp/http_capture.pcap ]; then
    echo "HTTP requests by content type:"
    tshark -r /tmp/http_capture.pcap -T fields -e http.content_type | sort | uniq -c
    
    echo -e "\nHTTP responses by content type:"
    tshark -r /tmp/http_capture.pcap -Y "http.response" -T fields -e http.content_type | sort | uniq -c
    
    echo -e "\nLooking for SSE conversion points:"
    tshark -r /tmp/http_capture.pcap -Y 'http.accept contains "event-stream" or http.content_type contains "event-stream"' -T text
fi

echo -e "\n🎯 ANALYSIS COMPLETE"
echo "Files available:"
echo "  - /tmp/http_analysis.txt (structured analysis)"
echo "  - /tmp/http_detailed.txt (detailed packet content)"
echo "  - /tmp/sse_patterns.txt (SSE-specific patterns)"
echo "  - /tmp/http_capture.pcap (raw packet capture)"
echo ""
echo "Use 'wireshark /tmp/http_capture.pcap' for visual analysis"