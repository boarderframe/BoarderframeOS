#!/usr/bin/env python3
"""
Jarvis Web Chat - Simple and Working
Uses .env file for API key
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import List
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import LLMClient, CLAUDE_OPUS_CONFIG

app = FastAPI(title="Jarvis Chat")
connections: List[WebSocket] = []

# Initialize Claude client
claude_client = None

async def init_claude():
    global claude_client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        claude_client = LLMClient(CLAUDE_OPUS_CONFIG)
        print(f"✅ Claude initialized with key: ...{api_key[-8:]}")
        return True
    else:
        print("❌ No ANTHROPIC_API_KEY found in .env file")
        return False

@app.get("/", response_class=HTMLResponse)
async def get_chat():
    # Add cache control headers to ensure fresh content
    from fastapi import Response
    
    def add_no_cache_headers(response: Response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis AI Assistant - Enhanced UI v2.0</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            /* Enhanced Color System */
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --dark-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            --warning-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            
            /* Glass Morphism */
            --glass-bg: rgba(255, 255, 255, 0.12);
            --glass-border: rgba(255, 255, 255, 0.18);
            --glass-hover: rgba(255, 255, 255, 0.22);
            --glass-active: rgba(255, 255, 255, 0.28);
            
            /* Shadows */
            --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
            --shadow-medium: 0 12px 40px rgba(31, 38, 135, 0.25);
            --shadow-strong: 0 20px 60px rgba(31, 38, 135, 0.4);
            --shadow-inset: inset 0 2px 4px rgba(0, 0, 0, 0.1);
            
            /* Text Colors */
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --text-muted: #bdc3c7;
            --text-white: rgba(255, 255, 255, 0.98);
            --text-white-secondary: rgba(255, 255, 255, 0.85);
            
            /* Status Colors */
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --info: #3b82f6;
            
            /* Layout */
            --sidebar-width: 320px;
            --sidebar-collapsed: 60px;
            --header-height: 80px;
            --border-radius: 16px;
            --border-radius-small: 8px;
            --border-radius-large: 24px;
            
            /* Transitions */
            --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-medium: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-slow: 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        html, body {
            height: 100%;
            overflow: hidden;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--primary-gradient);
            color: var(--text-primary);
            font-size: 14px;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.08) 0%, transparent 60%),
                radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.06) 0%, transparent 60%),
                radial-gradient(circle at 50% 50%, rgba(102, 126, 234, 0.1) 0%, transparent 80%);
            pointer-events: none;
            z-index: 0;
        }
        
        
        /* Sidebar Styles */
        .mcp-sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: var(--sidebar-width);
            height: 100vh;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-right: 1px solid var(--glass-border);
            display: flex;
            flex-direction: column;
            z-index: 1000;
            transition: transform var(--transition-medium);
            box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
        }
        
        .mcp-sidebar.collapsed {
            transform: translateX(calc(-1 * (var(--sidebar-width) - var(--sidebar-collapsed))));
        }
        
        .mcp-sidebar.collapsed .sidebar-content {
            padding: 10px 8px;
        }
        
        .mcp-sidebar.collapsed .mcp-server-card {
            width: 44px;
            height: 44px;
            padding: 0;
            margin-bottom: 8px;
            border-radius: 12px;
            justify-content: center;
            position: relative;
            overflow: visible;
        }
        
        .mcp-sidebar.collapsed .server-icon {
            width: 28px;
            height: 28px;
            font-size: 14px;
        }
        
        .mcp-sidebar.collapsed .server-info,
        .mcp-sidebar.collapsed .server-indicator {
            display: none;
        }
        
        .mcp-sidebar.collapsed .sidebar-title span,
        .mcp-sidebar.collapsed .sidebar-footer {
            display: none;
        }
        
        .mcp-sidebar.collapsed .sidebar-header {
            padding: 20px 8px;
            justify-content: center;
        }
        
        .mcp-sidebar.collapsed .sidebar-title {
            justify-content: center;
        }
        
        .mcp-sidebar.collapsed .sidebar-title i {
            font-size: 20px;
        }
        
        .mcp-sidebar.collapsed .sidebar-toggle {
            position: absolute;
            top: 50%;
            right: -16px;
            transform: translateY(-50%);
            background: var(--primary-gradient);
            border: 2px solid var(--glass-border);
            box-shadow: var(--shadow-medium);
        }
        
        /* Collapsed sidebar tooltips */
        .mcp-sidebar.collapsed .mcp-server-card::after {
            content: attr(data-tooltip);
            position: absolute;
            left: calc(100% + 12px);
            top: 50%;
            transform: translateY(-50%);
            background: var(--dark-gradient);
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: all var(--transition-fast);
            z-index: 1001;
            pointer-events: none;
        }
        
        .mcp-sidebar.collapsed .mcp-server-card:hover::after {
            opacity: 1;
            visibility: visible;
        }
        
        /* Status indicator on collapsed cards */
        .mcp-sidebar.collapsed .mcp-server-card::before {
            content: '';
            position: absolute;
            top: -2px;
            right: -2px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--danger);
            border: 2px solid white;
            opacity: 0;
            transition: all var(--transition-fast);
        }
        
        .mcp-sidebar.collapsed .mcp-server-card.online::before {
            background: var(--success);
            opacity: 1;
        }
        
        .mcp-sidebar.collapsed .mcp-server-card.offline::before {
            background: var(--danger);
            opacity: 1;
        }
        
        .sidebar-header {
            padding: 20px;
            border-bottom: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 80px;
            background: rgba(255, 255, 255, 0.02);
        }
        
        .sidebar-title {
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-white);
            font-weight: 700;
            font-size: 15px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .sidebar-title i {
            color: var(--info);
            font-size: 18px;
        }
        
        .sidebar-toggle {
            width: 32px;
            height: 32px;
            border: none;
            border-radius: var(--border-radius-small);
            background: var(--glass-hover);
            color: var(--text-white-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-fast);
        }
        
        .sidebar-toggle:hover {
            background: var(--glass-active);
            color: var(--text-white);
            transform: scale(1.05);
        }
        
        .sidebar-content {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
        }
        
        .mcp-server-card {
            background: var(--glass-hover);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            padding: 14px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all var(--transition-medium);
            position: relative;
            overflow: hidden;
            animation: yoloCardFloat 6s ease-in-out infinite;
        }
        
        .mcp-server-card:nth-child(1) { animation-delay: 0s; }
        .mcp-server-card:nth-child(2) { animation-delay: 2s; }
        .mcp-server-card:nth-child(3) { animation-delay: 4s; }
        
        @keyframes yoloCardFloat {
            0%, 100% {
                transform: translateX(0px) scale(1);
            }
            33% {
                transform: translateX(5px) scale(1.02);
            }
            66% {
                transform: translateX(-3px) scale(0.98);
            }
        }
        
        .mcp-server-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent, 
                rgba(255, 0, 255, 0.2), 
                rgba(0, 255, 255, 0.2), 
                rgba(255, 255, 0, 0.2), 
                transparent);
            transition: left 0.6s ease;
            animation: yoloShimmer 3s linear infinite;
        }
        
        @keyframes yoloShimmer {
            0% {
                left: -100%;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(255, 0, 255, 0.2), 
                    transparent);
            }
            50% {
                left: 0%;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(0, 255, 255, 0.3), 
                    transparent);
            }
            100% {
                left: 100%;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(255, 255, 0, 0.2), 
                    transparent);
            }
        }
        
        .mcp-server-card:hover::before {
            left: 100%;
        }
        
        .mcp-server-card:hover {
            background: var(--glass-active);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .server-icon {
            width: 36px;
            height: 36px;
            border-radius: var(--border-radius-small);
            background: var(--primary-gradient);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
            box-shadow: var(--shadow-soft);
            flex-shrink: 0;
        }
        
        .server-info {
            flex: 1;
        }
        
        .server-name {
            font-weight: 700;
            color: var(--text-white);
            margin-bottom: 3px;
            font-size: 14px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        .server-status {
            font-size: 11px;
            color: var(--text-white-secondary);
            margin-bottom: 6px;
            font-weight: 500;
        }
        
        .server-capabilities {
            display: flex;
            gap: 6px;
            flex-wrap: wrap;
        }
        
        .capability-tag {
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 10px;
            padding: 2px 6px;
            font-size: 9px;
            color: var(--text-white-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .server-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--danger);
            box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
            animation: pulse 2s infinite;
            flex-shrink: 0;
            margin-left: auto;
        }
        
        .server-indicator.online {
            background: var(--success);
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
        }
        
        .sidebar-footer {
            padding: 16px 20px;
            border-top: 1px solid var(--glass-border);
            background: rgba(255, 255, 255, 0.02);
            margin-top: auto;
        }
        
        .system-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 6px;
            color: var(--text-white-secondary);
            font-size: 11px;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.08);
            padding: 6px 10px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stat-item i {
            color: var(--info);
            font-size: 11px;
            width: 12px;
            text-align: center;
        }
        
        /* Main Container */
        .main-container {
            margin-left: var(--sidebar-width);
            height: 100vh;
            display: flex;
            flex-direction: column;
            transition: margin-left var(--transition-medium);
        }
        
        .main-container.sidebar-collapsed {
            margin-left: var(--sidebar-collapsed);
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            margin: 16px 20px 20px 20px;
            border-radius: var(--border-radius-large);
            overflow: hidden;
            box-shadow: var(--shadow-medium);
        }
        
        .header {
            background: var(--dark-gradient);
            color: white;
            padding: 20px 32px;
            position: relative;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 80px;
            display: flex;
            align-items: center;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.05) 50%, transparent 70%);
            animation: shimmer 3s ease-in-out infinite;
        }
        
        @keyframes shimmer {
            0%, 100% { transform: translateX(-100%); }
            50% { transform: translateX(100%); }
        }
        
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 1;
            width: 100%;
            max-width: 100%;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo {
            width: 44px;
            height: 44px;
            background: conic-gradient(from 0deg, #ff0080, #8000ff, #0080ff, #00ff80, #ff8000, #ff0080);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 
                0 4px 12px rgba(255, 0, 128, 0.5),
                0 0 20px rgba(128, 0, 255, 0.3);
            animation: yoloLogoRave 2s ease-in-out infinite;
            position: relative;
            overflow: hidden;
        }
        
        @keyframes yoloLogoRave {
            0%, 100% {
                transform: scale(1) rotate(0deg);
                filter: hue-rotate(0deg) brightness(1);
            }
            25% {
                transform: scale(1.1) rotate(5deg);
                filter: hue-rotate(90deg) brightness(1.2);
            }
            50% {
                transform: scale(1.05) rotate(-3deg);
                filter: hue-rotate(180deg) brightness(0.9);
            }
            75% {
                transform: scale(1.15) rotate(2deg);
                filter: hue-rotate(270deg) brightness(1.1);
            }
        }
        
        .logo::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent 30%, rgba(255, 255, 255, 0.1) 50%, transparent 70%);
            animation: shimmer 3s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .title-section h1 {
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 2px;
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            line-height: 1.2;
        }
        
        .subtitle {
            font-size: 13px;
            opacity: 0.7;
            font-weight: 400;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .model-badge {
            background: var(--accent-gradient);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: white;
            box-shadow: 0 2px 8px rgba(79, 172, 254, 0.3);
        }
        
        .divider {
            color: rgba(255, 255, 255, 0.4);
            font-weight: 300;
        }
        
        .status-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        
        .status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--danger);
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 0 8px rgba(255, 107, 107, 0.6);
        }
        
        .status.connected {
            background: var(--success);
            box-shadow: 0 0 8px rgba(0, 212, 170, 0.6);
        }
        
        .status.connected::after {
            content: '';
            position: absolute;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--success);
            animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        }
        
        @keyframes ping {
            75%, 100% {
                transform: scale(2);
                opacity: 0;
            }
        }
        
        .status-text {
            font-size: 11px;
            opacity: 0.8;
            font-weight: 500;
            color: var(--text-white);
        }
        
        .messages {
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            background: linear-gradient(180deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                rgba(255, 255, 255, 0.08) 100%);
            position: relative;
        }
        
        .messages::-webkit-scrollbar {
            width: 6px;
        }
        
        .messages::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .messages::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.3);
            border-radius: 3px;
        }
        
        .message {
            margin: 20px 0;
            display: flex;
            align-items: flex-start;
            gap: 12px;
            animation: slideIn 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        @keyframes slideIn {
            from { 
                opacity: 0; 
                transform: translateY(20px) scale(0.95); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .avatar {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            font-size: 14px;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .user .avatar {
            background: var(--secondary-gradient);
            color: white;
            order: 2;
        }
        
        .jarvis .avatar {
            background: var(--dark-gradient);
            color: white;
        }
        
        .message-content {
            max-width: 70%;
            padding: 16px 20px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.5;
            font-weight: 400;
            position: relative;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        }
        
        .user .message-content {
            background: var(--secondary-gradient);
            color: white;
            border-bottom-right-radius: 6px;
        }
        
        .jarvis .message-content {
            background: rgba(255, 255, 255, 0.95);
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-bottom-left-radius: 6px;
            backdrop-filter: blur(8px);
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
        }
        
        .system .message-content {
            background: rgba(52, 152, 219, 0.15);
            color: #2980b9;
            border: 1px solid rgba(52, 152, 219, 0.3);
            text-align: center;
            font-style: italic;
            font-weight: 600;
            margin: 0 auto;
            backdrop-filter: blur(8px);
        }
        
        .timestamp {
            font-size: 11px;
            color: rgba(255, 255, 255, 0.6);
            margin-top: 6px;
            font-weight: 400;
        }
        
        .jarvis .timestamp {
            color: var(--text-secondary);
        }
        
        .input-area {
            padding: 20px 24px 24px;
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(16px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .input-group {
            display: flex;
            gap: 16px;
            align-items: flex-end;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 24px;
            padding: 8px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(16px);
        }
        
        #messageInput {
            flex: 1;
            padding: 14px 16px;
            border: none;
            background: transparent;
            font-size: 15px;
            outline: none;
            resize: none;
            max-height: 120px;
            min-height: 20px;
            font-family: inherit;
            color: var(--text-primary);
            font-weight: 400;
            line-height: 1.4;
            animation: yoloInputGlow 4s ease-in-out infinite;
        }
        
        #messageInput:focus {
            animation: yoloInputFocusRave 1s ease-in-out infinite;
        }
        
        @keyframes yoloInputGlow {
            0%, 100% {
                text-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
            }
            50% {
                text-shadow: 0 0 15px rgba(255, 0, 128, 0.6);
            }
        }
        
        @keyframes yoloInputFocusRave {
            0%, 100% {
                text-shadow: 
                    0 0 5px rgba(255, 0, 0, 0.8),
                    0 0 10px rgba(0, 255, 0, 0.6),
                    0 0 15px rgba(0, 0, 255, 0.4);
            }
            33% {
                text-shadow: 
                    0 0 5px rgba(0, 255, 0, 0.8),
                    0 0 10px rgba(0, 0, 255, 0.6),
                    0 0 15px rgba(255, 0, 0, 0.4);
            }
            66% {
                text-shadow: 
                    0 0 5px rgba(0, 0, 255, 0.8),
                    0 0 10px rgba(255, 0, 0, 0.6),
                    0 0 15px rgba(0, 255, 0, 0.4);
            }
        }
        
        #messageInput::placeholder {
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        #sendBtn {
            width: 56px;
            height: 56px;
            border: none;
            border-radius: 50%;
            background: var(--primary-gradient);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            font-size: 20px;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
        }
        
        #sendBtn:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        #sendBtn:active {
            transform: scale(0.95);
        }
        
        #sendBtn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            box-shadow: none;
            transform: scale(1);
        }
        
        .typing {
            color: var(--text-secondary);
            font-style: italic;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--text-secondary);
            animation: typingBounce 1.4s ease-in-out infinite;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes typingBounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1.2);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            .mcp-sidebar {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            
            .mcp-sidebar.show {
                transform: translateX(0);
                box-shadow: 0 0 30px rgba(0, 0, 0, 0.3);
            }
            
            .main-container {
                margin-left: 0;
            }
            
            .chat-container {
                margin: 10px;
                border-radius: 16px;
            }
            
            .header {
                padding: 16px 20px;
                min-height: 70px;
            }
            
            .header-controls {
                gap: 12px;
            }
            
            .tool-indicators {
                padding: 6px 8px;
                gap: 6px;
            }
            
            .tool-indicator {
                width: 28px;
                height: 28px;
                font-size: 12px;
            }
            
            .logo {
                width: 36px;
                height: 36px;
                font-size: 16px;
            }
            
            .title-section h1 {
                font-size: 18px;
            }
            
            .subtitle {
                font-size: 12px;
            }
            
            .model-badge {
                font-size: 10px;
                padding: 1px 6px;
            }
            
            .messages {
                padding: 20px 16px;
            }
            
            .message-content {
                max-width: 85%;
                padding: 12px 16px;
                font-size: 14px;
            }
            
            .input-area {
                padding: 16px;
            }
            
            .input-group {
                gap: 6px;
                padding: 4px 6px;
            }
            
            #messageInput {
                padding: 12px 14px;
                font-size: 16px;
            }
            
            .send-btn {
                width: 44px;
                height: 44px;
                font-size: 15px;
            }
            
            .input-addon, .action-btn {
                width: 36px;
                height: 36px;
                font-size: 14px;
            }
            
            .fab-container {
                bottom: 80px;
                right: 16px;
            }
            
            .fab {
                width: 48px;
                height: 48px;
                font-size: 18px;
            }
            
            .welcome-message {
                margin: 20px 16px;
                padding: 32px 24px;
            }
            
            .welcome-icon {
                width: 56px;
                height: 56px;
                font-size: 24px;
            }
            
            .welcome-content h3 {
                font-size: 20px;
            }
            
            .welcome-features {
                gap: 12px;
            }
            
            .feature-item {
                padding: 8px 12px;
                font-size: 12px;
            }
        }
        
        /* Jarvis Startup Animation */
        .jarvis-startup {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 40px 32px;
            margin: 32px;
            min-height: 500px;
            position: relative;
        }
        
        .startup-animation {
            margin-bottom: 40px;
            position: relative;
        }
        
        .jarvis-core {
            position: relative;
            width: 150px;
            height: 150px;
            margin: 0 auto;
            animation: yoloCoreFloat 4s ease-in-out infinite;
        }
        
        @keyframes yoloCoreFloat {
            0%, 100% {
                transform: translateY(0px) rotate(0deg);
            }
            50% {
                transform: translateY(-10px) rotate(5deg);
            }
        }
        
        .core-ring {
            position: absolute;
            border-radius: 50%;
            border: 3px solid;
            opacity: 0.8;
            animation: yoloCoreRing 2s ease-in-out infinite;
            box-shadow: 0 0 20px currentColor;
        }
        
        .core-ring-1 {
            width: 150px;
            height: 150px;
            border-color: #ff00ff;
            animation-delay: 0s;
        }
        
        .core-ring-2 {
            width: 120px;
            height: 120px;
            top: 15px;
            left: 15px;
            border-color: #00ffff;
            animation-delay: 0.3s;
        }
        
        .core-ring-3 {
            width: 90px;
            height: 90px;
            top: 30px;
            left: 30px;
            border-color: #ffff00;
            animation-delay: 0.6s;
        }
        
        .jarvis-avatar {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 80px;
            height: 80px;
            background: conic-gradient(from 0deg, #ff0080, #8000ff, #0080ff, #00ff80, #ff8000, #ff0080);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 40px;
            box-shadow: 
                0 0 30px rgba(255, 0, 128, 0.8),
                0 0 60px rgba(128, 0, 255, 0.6),
                0 0 90px rgba(0, 128, 255, 0.4);
            animation: yoloAvatarSpin 3s linear infinite;
        }
        
        @keyframes yoloAvatarSpin {
            0% {
                transform: translate(-50%, -50%) rotate(0deg) scale(1);
                filter: hue-rotate(0deg);
            }
            50% {
                transform: translate(-50%, -50%) rotate(180deg) scale(1.1);
                filter: hue-rotate(180deg);
            }
            100% {
                transform: translate(-50%, -50%) rotate(360deg) scale(1);
                filter: hue-rotate(360deg);
            }
        }
        
        @keyframes yoloCoreRing {
            0%, 100% {
                transform: scale(1) rotate(0deg);
                opacity: 0.8;
                border-color: currentColor;
            }
            25% {
                transform: scale(1.2) rotate(90deg);
                opacity: 0.4;
                border-color: #ff0080;
            }
            50% {
                transform: scale(0.9) rotate(180deg);
                opacity: 1;
                border-color: #80ff00;
            }
            75% {
                transform: scale(1.3) rotate(270deg);
                opacity: 0.5;
                border-color: #0080ff;
            }
        }
        
        @keyframes avatarGlow {
            0% {
                box-shadow: 0 0 20px rgba(102, 126, 234, 0.6);
            }
            100% {
                box-shadow: 0 0 40px rgba(102, 126, 234, 0.8), 0 0 60px rgba(102, 126, 234, 0.4);
            }
        }
        
        .startup-sequence {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin-bottom: 30px;
            font-family: 'Courier New', monospace;
        }
        
        .startup-line {
            color: var(--text-white-secondary);
            font-size: 14px;
            opacity: 0;
            transform: translateX(-20px);
            animation: startupLine 0.6s ease-out forwards;
        }
        
        .startup-line.success {
            color: var(--success);
            font-weight: 600;
        }
        
        .startup-line:nth-child(1) { animation-delay: 0s; }
        .startup-line:nth-child(2) { animation-delay: 0.8s; }
        .startup-line:nth-child(3) { animation-delay: 1.6s; }
        .startup-line:nth-child(4) { animation-delay: 2.4s; }
        
        @keyframes startupLine {
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        .welcome-message-new {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius-large);
            padding: 32px;
            backdrop-filter: blur(16px);
            box-shadow: var(--shadow-soft);
            animation: fadeInUp 0.8s ease-out forwards;
            max-width: 600px;
            margin: 0 auto;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .jarvis-greeting {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-white);
            margin-bottom: 16px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .jarvis-intro {
            font-size: 16px;
            color: var(--text-white-secondary);
            margin-bottom: 24px;
            line-height: 1.5;
        }
        
        .capability-showcase {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }
        
        .capability-card {
            background: var(--glass-hover);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            padding: 16px;
            text-align: left;
            transition: all var(--transition-medium);
            opacity: 0;
            transform: translateY(20px);
            animation: slideInUp 0.6s ease-out forwards;
        }
        
        .capability-card:hover {
            background: var(--glass-active);
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        @keyframes slideInUp {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .capability-icon {
            width: 40px;
            height: 40px;
            background: var(--primary-gradient);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            margin-bottom: 12px;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .capability-info h4 {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-white);
            margin-bottom: 4px;
        }
        
        .capability-info p {
            font-size: 12px;
            color: var(--text-white-secondary);
            margin: 0;
            line-height: 1.4;
        }
        
        .quick-start {
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.2);
            border-radius: var(--border-radius);
            padding: 16px;
            color: var(--text-white-secondary);
            font-size: 14px;
            opacity: 0;
            animation: fadeIn 0.6s ease-out forwards;
        }
        
        .quick-start strong {
            color: var(--text-white);
            background: rgba(102, 126, 234, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }
        
        @keyframes fadeIn {
            to {
                opacity: 1;
            }
        }
        
        @keyframes yoloConnectionExplosion {
            0% {
                transform: scale(1) rotate(0deg);
                filter: hue-rotate(0deg) brightness(1);
            }
            25% {
                transform: scale(1.5) rotate(90deg);
                filter: hue-rotate(90deg) brightness(1.5);
            }
            50% {
                transform: scale(2) rotate(180deg);
                filter: hue-rotate(180deg) brightness(2);
            }
            75% {
                transform: scale(1.5) rotate(270deg);
                filter: hue-rotate(270deg) brightness(1.5);
            }
            100% {
                transform: scale(1) rotate(360deg);
                filter: hue-rotate(360deg) brightness(1);
            }
        }
        
        @keyframes yoloDiscoMode {
            0% {
                filter: hue-rotate(0deg) contrast(1) brightness(1);
            }
            10% {
                filter: hue-rotate(36deg) contrast(1.1) brightness(1.1);
            }
            20% {
                filter: hue-rotate(72deg) contrast(1.2) brightness(1.2);
            }
            30% {
                filter: hue-rotate(108deg) contrast(1.1) brightness(1.1);
            }
            40% {
                filter: hue-rotate(144deg) contrast(1) brightness(1);
            }
            50% {
                filter: hue-rotate(180deg) contrast(1.1) brightness(1.1);
            }
            60% {
                filter: hue-rotate(216deg) contrast(1.2) brightness(1.2);
            }
            70% {
                filter: hue-rotate(252deg) contrast(1.1) brightness(1.1);
            }
            80% {
                filter: hue-rotate(288deg) contrast(1) brightness(1);
            }
            90% {
                filter: hue-rotate(324deg) contrast(1.1) brightness(1.1);
            }
            100% {
                filter: hue-rotate(360deg) contrast(1) brightness(1);
            }
        }
        
        /* YOLO MODE: Insane breathing animation */
        .tool-indicator.active,
        .server-indicator.online {
            animation: yoloBreatheInsane 1s ease-in-out infinite;
        }
        
        @keyframes yoloBreatheInsane {
            0%, 100% {
                opacity: 1;
                transform: scale(1);
                filter: hue-rotate(0deg);
            }
            25% {
                opacity: 0.8;
                transform: scale(1.2);
                filter: hue-rotate(90deg);
            }
            50% {
                opacity: 0.6;
                transform: scale(0.8);
                filter: hue-rotate(180deg);
            }
            75% {
                opacity: 0.9;
                transform: scale(1.1);
                filter: hue-rotate(270deg);
            }
        }
        
        /* Pulse animation for activity */
        .activity-pulse {
            animation: activityPulse 0.6s ease-out;
        }
        
        @keyframes activityPulse {
            0% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
            }
            70% {
                transform: scale(1.05);
                box-shadow: 0 0 0 10px rgba(102, 126, 234, 0);
            }
            100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(102, 126, 234, 0);
            }
        }
        
        /* Floating Action Button */
        .fab-container {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 1000;
        }
        
        .fab {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: conic-gradient(from 0deg, #ff1493, #00bfff, #32cd32, #ffd700, #ff6347, #ff1493);
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 
                0 8px 32px rgba(255, 20, 147, 0.6),
                0 0 40px rgba(0, 191, 255, 0.4),
                0 0 60px rgba(50, 205, 50, 0.3);
            transition: all var(--transition-medium);
            position: relative;
            z-index: 2;
            animation: yoloFabOrbit 8s linear infinite;
        }
        
        @keyframes yoloFabOrbit {
            0% {
                transform: rotate(0deg) scale(1);
                filter: hue-rotate(0deg);
            }
            25% {
                transform: rotate(90deg) scale(1.1);
                filter: hue-rotate(90deg);
            }
            50% {
                transform: rotate(180deg) scale(0.9);
                filter: hue-rotate(180deg);
            }
            75% {
                transform: rotate(270deg) scale(1.05);
                filter: hue-rotate(270deg);
            }
            100% {
                transform: rotate(360deg) scale(1);
                filter: hue-rotate(360deg);
            }
        }
        
        .fab:hover {
            transform: scale(1.3) rotate(720deg);
            animation-duration: 2s;
            box-shadow: 
                0 12px 48px rgba(255, 20, 147, 0.8),
                0 0 60px rgba(0, 191, 255, 0.6),
                0 0 80px rgba(50, 205, 50, 0.4),
                0 0 100px rgba(255, 215, 0, 0.3);
        }
        
        .fab-menu {
            position: absolute;
            bottom: 80px;
            right: 0;
            display: flex;
            flex-direction: column;
            gap: 12px;
            opacity: 0;
            visibility: hidden;
            transform: translateY(20px);
            transition: all var(--transition-medium);
        }
        
        .fab-menu.active {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }
        
        .fab-action {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            color: var(--text-white);
            font-size: 16px;
            cursor: pointer;
            transition: all var(--transition-medium);
            position: relative;
        }
        
        .fab-action:hover {
            background: var(--glass-active);
            transform: scale(1.05);
            color: var(--info);
        }
        
        .fab-action::before {
            content: attr(title);
            position: absolute;
            right: 60px;
            top: 50%;
            transform: translateY(-50%);
            background: var(--dark-gradient);
            color: white;
            padding: 6px 12px;
            border-radius: var(--border-radius-small);
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: all var(--transition-fast);
            pointer-events: none;
        }
        
        .fab-action:hover::before {
            opacity: 1;
            visibility: visible;
        }
        
        /* Header Tool Indicators */
        .header-controls {
            display: flex;
            align-items: center;
            gap: 16px;
            height: 100%;
        }
        
        .tool-indicators {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            backdrop-filter: blur(8px);
        }
        
        .tool-indicator {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-white-secondary);
            font-size: 14px;
            transition: all var(--transition-medium);
            position: relative;
            cursor: pointer;
            animation: yoloToolBounce 3s ease-in-out infinite;
        }
        
        .tool-indicator:nth-child(1) { animation-delay: 0s; }
        .tool-indicator:nth-child(2) { animation-delay: 1s; }
        .tool-indicator:nth-child(3) { animation-delay: 2s; }
        
        @keyframes yoloToolBounce {
            0%, 100% {
                transform: translateY(0px) scale(1);
            }
            50% {
                transform: translateY(-3px) scale(1.05);
                box-shadow: 0 5px 15px rgba(255, 255, 255, 0.3);
            }
        }
        
        .tool-indicator:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .tool-indicator.active {
            background: conic-gradient(from 0deg, #00ff00, #ffff00, #ff00ff, #00ffff, #00ff00);
            border-color: var(--success);
            color: white;
            box-shadow: 
                0 0 12px rgba(0, 255, 0, 0.6),
                0 0 24px rgba(255, 255, 0, 0.4),
                0 0 36px rgba(255, 0, 255, 0.3);
            animation: yoloActiveGlow 2s ease-in-out infinite;
        }
        
        @keyframes yoloActiveGlow {
            0%, 100% {
                filter: brightness(1) hue-rotate(0deg);
                transform: scale(1);
            }
            50% {
                filter: brightness(1.3) hue-rotate(180deg);
                transform: scale(1.1);
            }
        }
        
        .tool-indicator.active::after {
            content: '';
            position: absolute;
            top: -3px;
            right: -3px;
            width: 6px;
            height: 6px;
            background: #00ff88;
            border: 1px solid white;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .settings-btn {
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-medium);
            font-size: 16px;
            border: 1px solid rgba(255, 255, 255, 0.15);
            position: relative;
            overflow: hidden;
        }
        
        .settings-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.6s ease;
        }
        
        .settings-btn:hover::before {
            left: 100%;
        }
        
        .settings-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: rotate(90deg) scale(1.05);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .connection-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
            backdrop-filter: blur(8px);
        }
        
        /* Enhanced Input Area */
        .input-container {
            position: relative;
        }
        
        .input-group {
            display: flex;
            gap: 8px;
            align-items: flex-end;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            padding: 6px 8px;
            box-shadow: var(--shadow-medium);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .input-addon {
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: 50%;
            transition: all var(--transition-medium);
        }
        
        .input-addon:hover {
            background: var(--glass-hover);
            color: var(--info);
        }
        
        .input-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .action-btn {
            width: 40px;
            height: 40px;
            border: none;
            border-radius: 50%;
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-medium);
            font-size: 15px;
        }
        
        .action-btn:hover {
            background: var(--glass-hover);
            color: var(--info);
            transform: scale(1.1);
        }
        
        .send-btn {
            width: 48px;
            height: 48px;
            border: none;
            border-radius: 50%;
            background: conic-gradient(from 0deg, #ff0080, #8000ff, #0080ff, #00ff80, #ff8000, #ff0080);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-medium);
            font-size: 16px;
            font-weight: 600;
            box-shadow: 
                0 4px 16px rgba(255, 0, 128, 0.6),
                0 0 20px rgba(128, 0, 255, 0.4);
            position: relative;
            overflow: hidden;
            animation: yoloSendSpin 4s linear infinite;
        }
        
        @keyframes yoloSendSpin {
            0% {
                filter: hue-rotate(0deg);
                box-shadow: 
                    0 4px 16px rgba(255, 0, 128, 0.6),
                    0 0 20px rgba(128, 0, 255, 0.4);
            }
            25% {
                filter: hue-rotate(90deg);
                box-shadow: 
                    0 4px 16px rgba(0, 255, 128, 0.6),
                    0 0 20px rgba(255, 128, 0, 0.4);
            }
            50% {
                filter: hue-rotate(180deg);
                box-shadow: 
                    0 4px 16px rgba(128, 255, 0, 0.6),
                    0 0 20px rgba(0, 128, 255, 0.4);
            }
            75% {
                filter: hue-rotate(270deg);
                box-shadow: 
                    0 4px 16px rgba(255, 128, 0, 0.6),
                    0 0 20px rgba(128, 0, 255, 0.4);
            }
            100% {
                filter: hue-rotate(360deg);
                box-shadow: 
                    0 4px 16px rgba(255, 0, 128, 0.6),
                    0 0 20px rgba(128, 0, 255, 0.4);
            }
        }
        
        .send-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transition: left 0.6s ease;
        }
        
        .send-btn:hover::before {
            left: 100%;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: scale(1.2) rotate(180deg);
            animation-duration: 1s;
            box-shadow: 
                0 6px 20px rgba(255, 0, 128, 0.8),
                0 0 40px rgba(128, 0, 255, 0.6),
                0 0 60px rgba(0, 128, 255, 0.4);
        }
        
        .send-btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            box-shadow: none;
        }
        
        
        .typing-indicator {
            position: absolute;
            bottom: -40px;
            left: 20px;
            display: none;
            align-items: center;
            gap: 8px;
            color: var(--text-white-secondary);
            font-size: 14px;
            font-style: italic;
        }
        
        .typing-indicator.active {
            display: flex;
        }
        
        /* Settings Panel */
        .settings-panel {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(8px);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        }
        
        .settings-panel.active {
            display: flex;
        }
        
        .settings-content {
            width: 90%;
            max-width: 600px;
            max-height: 80vh;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border-radius: 20px;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-light);
            overflow: hidden;
            animation: slideUp 0.3s ease;
        }
        
        @keyframes slideUp {
            from { transform: translateY(20px) scale(0.95); opacity: 0; }
            to { transform: translateY(0) scale(1); opacity: 1; }
        }
        
        .settings-header {
            background: var(--dark-gradient);
            color: white;
            padding: 20px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .settings-header h2 {
            font-size: 20px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .close-btn {
            width: 32px;
            height: 32px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .close-btn:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .settings-body {
            padding: 24px;
            max-height: 400px;
            overflow-y: auto;
        }
        
        .setting-group {
            margin-bottom: 32px;
        }
        
        .setting-group h3 {
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .setting-item {
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
        }
        
        .setting-item label {
            font-weight: 500;
            color: var(--text-primary);
            min-width: 120px;
        }
        
        .setting-item select,
        .setting-item input[type="number"] {
            flex: 1;
            max-width: 200px;
            padding: 8px 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            font-size: 14px;
        }
        
        .setting-item input[type="range"] {
            flex: 1;
            max-width: 150px;
        }
        
        .setting-item input[type="checkbox"] {
            width: 20px;
            height: 20px;
        }
        
        #tempValue {
            min-width: 30px;
            text-align: center;
            font-weight: 600;
        }
        
        .mcp-servers {
            space-y: 12px;
        }
        
        .mcp-server {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 8px;
        }
        
        .mcp-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .mcp-name {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .mcp-status {
            font-size: 12px;
            color: var(--text-secondary);
        }
        
        .mcp-toggle {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            background: var(--primary-gradient);
            color: white;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .mcp-toggle:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
        }
        
        .setting-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .btn-secondary,
        .btn-danger,
        .btn-primary {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .btn-danger {
            background: var(--danger);
            color: white;
        }
        
        .btn-primary {
            background: var(--primary-gradient);
            color: white;
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        .btn-danger:hover {
            background: #e74c3c;
        }
        
        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .settings-footer {
            padding: 20px 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: flex-end;
        }
        
        /* Responsive Sidebar */
        @media (max-width: 1024px) {
            .mcp-sidebar {
                transform: translateX(-100%);
                width: 280px;
            }
            
            .mcp-sidebar.show {
                transform: translateX(0);
            }
            
            .main-container {
                margin-left: 0;
            }
            
            .fab-container {
                bottom: 90px;
            }
            
            .sidebar-toggle {
                display: none;
            }
        }
        
        /* Add mobile sidebar toggle button */
        @media (max-width: 1024px) {
            .mobile-sidebar-toggle {
                position: fixed;
                top: 20px;
                left: 20px;
                width: 44px;
                height: 44px;
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                color: var(--text-white);
                font-size: 18px;
                cursor: pointer;
                z-index: 1001;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all var(--transition-medium);
            }
            
            .mobile-sidebar-toggle:hover {
                background: var(--glass-hover);
                transform: scale(1.05);
            }
        }
        
        @media (min-width: 1025px) {
            .mobile-sidebar-toggle {
                display: none;
            }
        }

        /* Dark mode enhancements */
        @media (prefers-color-scheme: dark) {
            .jarvis .message-content {
                background: rgba(44, 62, 80, 0.9);
                color: white;
                border-color: rgba(255, 255, 255, 0.1);
            }
            
            .input-group {
                background: rgba(44, 62, 80, 0.9);
            }
            
            #messageInput {
                color: white;
            }
            
            #messageInput::placeholder {
                color: rgba(255, 255, 255, 0.6);
            }
            
            .setting-item select,
            .setting-item input[type="number"] {
                background: rgba(44, 62, 80, 0.9);
                color: white;
                border-color: rgba(255, 255, 255, 0.2);
            }
        }
    </style>
</head>
<body>
    <!-- Mobile Sidebar Toggle -->
    <button class="mobile-sidebar-toggle" id="mobileSidebarToggle">
        <i class="fas fa-bars"></i>
    </button>
    
    <!-- MCP Status Sidebar -->
    <div class="mcp-sidebar" id="mcpSidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">
                <i class="fas fa-plug"></i>
                <span>MCP Servers</span>
            </div>
            <button class="sidebar-toggle" id="sidebarToggle">
                <i class="fas fa-chevron-left"></i>
            </button>
        </div>
        
        <div class="sidebar-content">
            <div class="mcp-server-card" id="fsCard" data-tooltip="Filesystem Server">
                <div class="server-icon">
                    <i class="fas fa-folder"></i>
                </div>
                <div class="server-info">
                    <div class="server-name">Filesystem</div>
                    <div class="server-status" id="sidebarFsStatus">Checking...</div>
                    <div class="server-capabilities">
                        <span class="capability-tag">Read</span>
                        <span class="capability-tag">Write</span>
                        <span class="capability-tag">List</span>
                    </div>
                </div>
                <div class="server-indicator" id="fsIndicator"></div>
            </div>
            
            <div class="mcp-server-card" id="gitCard" data-tooltip="Git Server">
                <div class="server-icon">
                    <i class="fas fa-code-branch"></i>
                </div>
                <div class="server-info">
                    <div class="server-name">Git</div>
                    <div class="server-status" id="sidebarGitStatus">Checking...</div>
                    <div class="server-capabilities">
                        <span class="capability-tag">Status</span>
                        <span class="capability-tag">Commit</span>
                        <span class="capability-tag">Push</span>
                    </div>
                </div>
                <div class="server-indicator" id="gitIndicator"></div>
            </div>
            
            <div class="mcp-server-card" id="terminalCard" data-tooltip="Terminal Server">
                <div class="server-icon">
                    <i class="fas fa-terminal"></i>
                </div>
                <div class="server-info">
                    <div class="server-name">Terminal</div>
                    <div class="server-status" id="sidebarTerminalStatus">Checking...</div>
                    <div class="server-capabilities">
                        <span class="capability-tag">Execute</span>
                        <span class="capability-tag">Python</span>
                        <span class="capability-tag">Install</span>
                    </div>
                </div>
                <div class="server-indicator" id="terminalIndicator"></div>
            </div>
        </div>
        
        <div class="sidebar-footer">
            <div class="system-stats">
                <div class="stat-item">
                    <i class="fas fa-comments"></i>
                    <span id="messageCount">0</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Chat Container -->
    <div class="main-container" id="mainContainer">
        <div class="chat-container">
            <div class="header">
                <div class="header-content">
                    <div class="logo-section">
                        <div class="logo">
                            🤖
                        </div>
                        <div class="title-section">
                            <h1>Jarvis AI Assistant</h1>
                            <div class="subtitle">
                                <span class="model-badge" id="modelBadge">Claude 4 Opus</span>
                                <span class="divider">•</span>
                                <span>BoarderframeOS</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="header-controls">
                        <div class="tool-indicators" id="toolIndicators">
                            <div class="tool-indicator" id="fsToolIndicator" title="Filesystem Access">
                                <i class="fas fa-folder"></i>
                            </div>
                            <div class="tool-indicator" id="gitToolIndicator" title="Git Operations">
                                <i class="fas fa-code-branch"></i>
                            </div>
                            <div class="tool-indicator" id="terminalToolIndicator" title="Terminal Commands">
                                <i class="fas fa-terminal"></i>
                            </div>
                        </div>
                        
                        <button id="settingsBtn" class="settings-btn">
                            <i class="fas fa-cog"></i>
                        </button>
                        
                        <div class="connection-status">
                            <div class="status" id="status"></div>
                            <div class="status-text" id="statusText">Connecting...</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="messages" id="messages">
                <div class="jarvis-startup">
                    <div class="startup-animation">
                        <div class="jarvis-core">
                            <div class="core-ring core-ring-1"></div>
                            <div class="core-ring core-ring-2"></div>
                            <div class="core-ring core-ring-3"></div>
                            <div class="jarvis-avatar">
                                🤖
                            </div>
                        </div>
                    </div>
                    
                    <div class="startup-sequence">
                        <div class="startup-line" data-delay="0">◉ Initializing Jarvis Neural Network...</div>
                        <div class="startup-line" data-delay="800">◉ Loading Claude 4 Opus Intelligence...</div>
                        <div class="startup-line" data-delay="1600">◉ Connecting to MCP Servers...</div>
                        <div class="startup-line success" data-delay="2400">✓ Jarvis is Online and Ready</div>
                    </div>
                    
                    <div class="welcome-message-new" style="opacity: 0; animation-delay: 3s;">
                        <h2 class="jarvis-greeting" style="animation: yoloTextRave 3s ease-in-out infinite;">🚀 YOLO MODE ACTIVATED! 🚀 I'm Jarvis, your SUPERCHARGED AI assistant!</h2>
                        <p class="jarvis-intro" style="animation: yoloTextGlow 2s ease-in-out infinite;">🔥 EXTREME MODE ENABLED! 🔥 I'm turbocharged with Claude 4 and ready to DEMOLISH your coding challenges! Let's build something EPIC! 💫</p>
                        
                        <div class="capability-showcase">
                            <div class="capability-card" style="animation-delay: 3.5s;">
                                <div class="capability-icon">
                                    <i class="fas fa-folder-open"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>File Management</h4>
                                    <p>Read, write, and organize your project files</p>
                                </div>
                            </div>
                            
                            <div class="capability-card" style="animation-delay: 3.7s;">
                                <div class="capability-icon">
                                    <i class="fas fa-code-branch"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>Version Control</h4>
                                    <p>Git operations, commits, and repository management</p>
                                </div>
                            </div>
                            
                            <div class="capability-card" style="animation-delay: 3.9s;">
                                <div class="capability-icon">
                                    <i class="fas fa-terminal"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>Command Execution</h4>
                                    <p>Run scripts, install packages, and execute commands</p>
                                </div>
                            </div>
                        </div>
                        
                        <div class="quick-start" style="animation: yoloQuickStart 2s ease-in-out infinite; animation-delay: 4.2s;">
                            <p>🎮 READY TO ROCK? Try: <strong>"SHOW ME THE MATRIX!"</strong> or <strong>"HACK THE GIBSON!"</strong> 🎮</p>
                        </div>
                        
                        @keyframes yoloTextRave {
                            0%, 100% {
                                color: #ff00ff;
                                text-shadow: 0 0 10px #ff00ff;
                            }
                            25% {
                                color: #00ffff;
                                text-shadow: 0 0 20px #00ffff;
                            }
                            50% {
                                color: #ffff00;
                                text-shadow: 0 0 15px #ffff00;
                            }
                            75% {
                                color: #ff8000;
                                text-shadow: 0 0 25px #ff8000;
                            }
                        }
                        
                        @keyframes yoloTextGlow {
                            0%, 100% {
                                text-shadow: 0 0 5px rgba(255, 255, 255, 0.8);
                            }
                            50% {
                                text-shadow: 0 0 20px rgba(255, 0, 128, 1);
                            }
                        }
                        
                        @keyframes yoloQuickStart {
                            0%, 100% {
                                background: rgba(255, 0, 255, 0.2);
                                border-color: rgba(255, 0, 255, 0.4);
                            }
                            50% {
                                background: rgba(0, 255, 255, 0.2);
                                border-color: rgba(0, 255, 255, 0.4);
                            }
                        }
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <div class="input-container">
                    <div class="input-group">
                        <div class="input-addon">
                            <i class="fas fa-microphone" id="voiceBtn" title="Voice Input (Coming Soon)"></i>
                        </div>
                        <textarea id="messageInput" placeholder="Ask Jarvis anything..." disabled rows="1"></textarea>
                        <div class="input-actions">
                            <button id="attachBtn" class="action-btn" title="Attach File (Coming Soon)">
                                <i class="fas fa-paperclip"></i>
                            </button>
                            <button id="sendBtn" disabled class="send-btn">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                    </div>
                    <div class="typing-indicator" id="typingIndicator">
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                        <span>Jarvis is thinking...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Floating Action Button -->
    <div class="fab-container">
        <button class="fab" id="quickActionsBtn">
            <i class="fas fa-magic"></i>
        </button>
        <div class="fab-menu" id="fabMenu">
            <button class="fab-action" data-action="status" title="System Status">
                <i class="fas fa-heartbeat"></i>
            </button>
            <button class="fab-action" data-action="code" title="Code Analysis">
                <i class="fas fa-code"></i>
            </button>
            <button class="fab-action" data-action="files" title="List Files">
                <i class="fas fa-folder"></i>
            </button>
            <button class="fab-action" data-action="help" title="Help">
                <i class="fas fa-question"></i>
            </button>
        </div>
    </div>
    
    <!-- Settings Panel -->
    <div class="settings-panel" id="settingsPanel">
        <div class="settings-content">
            <div class="settings-header">
                <h2><i class="fas fa-cog"></i> Jarvis Settings</h2>
                <button class="close-btn" id="closeSettings">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            
            <div class="settings-body">
                <div class="setting-group">
                    <h3><i class="fas fa-robot"></i> Model Configuration</h3>
                    <div class="setting-item">
                        <label for="modelSelect">Claude Model:</label>
                        <select id="modelSelect">
                            <option value="claude-opus-4-20250514">Claude 4 Opus (Most Intelligent)</option>
                            <option value="claude-sonnet-4-20250514">Claude 4 Sonnet (Balanced)</option>
                        </select>
                    </div>
                    <div class="setting-item">
                        <label for="temperatureSlider">Temperature:</label>
                        <input type="range" id="temperatureSlider" min="0" max="1" step="0.1" value="0.5">
                        <span id="tempValue">0.5</span>
                    </div>
                    <div class="setting-item">
                        <label for="maxTokensInput">Max Tokens:</label>
                        <input type="number" id="maxTokensInput" min="100" max="4000" value="1000">
                    </div>
                </div>
                
                <div class="setting-group">
                    <h3><i class="fas fa-plug"></i> MCP Servers</h3>
                    <div class="mcp-servers">
                        <div class="mcp-server">
                            <div class="mcp-info">
                                <span class="mcp-name">Filesystem Server</span>
                                <span class="mcp-status" id="fsStatus">Checking...</span>
                            </div>
                            <button class="mcp-toggle" id="fsToggle">Enable</button>
                        </div>
                        <div class="mcp-server">
                            <div class="mcp-info">
                                <span class="mcp-name">Git Server</span>
                                <span class="mcp-status" id="gitStatus">Checking...</span>
                            </div>
                            <button class="mcp-toggle" id="gitToggle">Enable</button>
                        </div>
                        <div class="mcp-server">
                            <div class="mcp-info">
                                <span class="mcp-name">Terminal Server</span>
                                <span class="mcp-status" id="terminalStatus">Checking...</span>
                            </div>
                            <button class="mcp-toggle" id="terminalToggle">Enable</button>
                        </div>
                    </div>
                </div>
                
                <div class="setting-group">
                    <h3><i class="fas fa-palette"></i> Interface</h3>
                    <div class="setting-item">
                        <label for="themeSelect">Theme:</label>
                        <select id="themeSelect">
                            <option value="auto">Auto (System)</option>
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                        </select>
                    </div>
                    <div class="setting-item">
                        <label for="animationsToggle">Animations:</label>
                        <input type="checkbox" id="animationsToggle" checked>
                    </div>
                </div>
                
                <div class="setting-group">
                    <h3><i class="fas fa-save"></i> Data</h3>
                    <div class="setting-actions">
                        <button class="btn-secondary" id="exportSettings">
                            <i class="fas fa-download"></i> Export Settings
                        </button>
                        <button class="btn-secondary" id="importSettings">
                            <i class="fas fa-upload"></i> Import Settings
                        </button>
                        <button class="btn-danger" id="clearData">
                            <i class="fas fa-trash"></i> Clear All Data
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="settings-footer">
                <button class="btn-primary" id="saveSettings">
                    <i class="fas fa-save"></i> Save Settings
                </button>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        const messages = document.getElementById('messages');
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const status = document.getElementById('status');
        const statusText = document.getElementById('statusText');
        
        // Settings elements
        const settingsBtn = document.getElementById('settingsBtn');
        const settingsPanel = document.getElementById('settingsPanel');
        const closeSettings = document.getElementById('closeSettings');
        const saveSettings = document.getElementById('saveSettings');
        
        // UI Elements
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mcpSidebar = document.getElementById('mcpSidebar');
        const mainContainer = document.getElementById('mainContainer');
        const quickActionsBtn = document.getElementById('quickActionsBtn');
        const fabMenu = document.getElementById('fabMenu');
        const typingIndicator = document.getElementById('typingIndicator');
        
        // Tool indicators
        const fsToolIndicator = document.getElementById('fsToolIndicator');
        const gitToolIndicator = document.getElementById('gitToolIndicator');
        const terminalToolIndicator = document.getElementById('terminalToolIndicator');
        
        // Sidebar status elements
        const fsIndicator = document.getElementById('fsIndicator');
        const gitIndicator = document.getElementById('gitIndicator');
        const terminalIndicator = document.getElementById('terminalIndicator');
        const sidebarFsStatus = document.getElementById('sidebarFsStatus');
        const sidebarGitStatus = document.getElementById('sidebarGitStatus');
        const sidebarTerminalStatus = document.getElementById('sidebarTerminalStatus');
        
        // System stats
        const messageCountElement = document.getElementById('messageCount');
        
        // Settings storage
        let currentSettings = {
            model: 'claude-opus-4-20250514',
            temperature: 0.5,
            max_tokens: 1000,
            theme: 'auto',
            animations: true,
            mcp_enabled: {}
        };

        let connectionAttempts = 0;
        const maxAttempts = 3;
        let messageCount = 0;
        let startTime = Date.now();
        let sidebarCollapsed = false;
        let fabMenuOpen = false;
        
        function connect() {
            connectionAttempts++;
            statusText.textContent = `Connecting... (${connectionAttempts}/${maxAttempts})`;
            
            // Test basic connectivity first
            fetch('/test')
                .then(response => response.json())
                .then(data => {
                    console.log('Server test passed:', data);
                    connectWebSocket();
                })
                .catch(error => {
                    console.error('Server test failed:', error);
                    statusText.textContent = 'Server Error';
                    addMessage('system', 'Server connection failed. Please refresh the page.');
                });
        }
        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            console.log('Attempting WebSocket connection to:', wsUrl);
            console.log('Browser:', navigator.userAgent);
            
            try {
                ws = new WebSocket(wsUrl);
                
                // Set timeout for connection
                const connectionTimeout = setTimeout(() => {
                    if (ws.readyState === WebSocket.CONNECTING) {
                        console.log('WebSocket connection timed out');
                        ws.close();
                        handleConnectionFailure();
                    }
                }, 5000);
                
                ws.onopen = function() {
                    console.log('🚀 YOLO MODE: WebSocket SUPERCHARGED!');
                    clearTimeout(connectionTimeout);
                    connectionAttempts = 0;
                    status.classList.add('connected');
                    statusText.textContent = '🔥 ONLINE 🔥';
                    input.disabled = false;
                    updateSendButton();
                    
                    // YOLO connection explosion!
                    const jarvisCore = document.querySelector('.jarvis-core');
                    if (jarvisCore) {
                        jarvisCore.style.animation = 'none';
                        jarvisCore.offsetHeight; // Trigger reflow
                        jarvisCore.style.animation = 'yoloConnectionExplosion 2s ease-out';
                    }
                    
                    // Add disco mode to entire body
                    document.body.style.animation = 'yoloDiscoMode 10s linear infinite';
                    
                    addMessage('system', '🎉 YOLO MODE ACTIVATED! 🎉 Jarvis is SUPERCHARGED and ready to DEMOLISH your tasks! 💥');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    removeTyping();
                    addMessage(data.type, data.message);
                };
                
                ws.onclose = function(event) {
                    console.log('WebSocket closed:', event.code, event.reason);
                    clearTimeout(connectionTimeout);
                    status.classList.remove('connected');
                    input.disabled = true;
                    sendBtn.disabled = true;
                    
                    if (event.code === 1006) {
                        console.log('Abnormal closure, attempting reconnect...');
                        handleConnectionFailure();
                    } else {
                        statusText.textContent = 'Reconnecting...';
                        addMessage('system', 'Connection lost. Reconnecting...');
                        setTimeout(connect, 3000);
                    }
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                    clearTimeout(connectionTimeout);
                    handleConnectionFailure();
                };
                
            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                handleConnectionFailure();
            }
        }
        
        function handleConnectionFailure() {
            if (connectionAttempts < maxAttempts) {
                statusText.textContent = 'Retrying...';
                addMessage('system', `Connection failed. Retrying... (${connectionAttempts}/${maxAttempts})`);
                setTimeout(connect, 2000);
            } else {
                statusText.textContent = 'Failed';
                addMessage('system', 'Connection failed after multiple attempts. Please refresh the page or try a different browser.');
            }
        }

        function addMessage(type, message, timestamp = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            const time = timestamp ? new Date(timestamp) : new Date();
            const timeStr = time.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'});
            
            let avatar = '';
            let content = '';
            
            if (type === 'user') {
                avatar = '<div class="avatar">You</div>';
                content = `
                    <div style="flex: 1;">
                        <div class="message-content">${escapeHtml(message)}</div>
                        <div class="timestamp">${timeStr}</div>
                    </div>
                `;
                messageCount++;
            } else if (type === 'jarvis') {
                avatar = '<div class="avatar">J</div>';
                content = `
                    <div style="flex: 1;">
                        <div class="message-content">${escapeHtml(message)}</div>
                        <div class="timestamp">${timeStr}</div>
                    </div>
                `;
                messageCount++;
            } else if (type === 'system') {
                messageDiv.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
                messages.appendChild(messageDiv);
                scrollToBottom();
                updateSystemStats();
                return;
            }
            
            messageDiv.innerHTML = avatar + content;
            messages.appendChild(messageDiv);
            scrollToBottom();
            updateSystemStats();
        }
        
        function addTyping() {
            removeTyping();
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message jarvis typing';
            typingDiv.id = 'typing-indicator';
            typingDiv.innerHTML = `
                <div class="avatar">J</div>
                <div style="flex: 1;">
                    <div class="message-content">
                        <div class="typing-dots">
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                            <div class="typing-dot"></div>
                        </div>
                        Jarvis is thinking...
                    </div>
                </div>
            `;
            messages.appendChild(typingDiv);
            scrollToBottom();
            
            // Show typing indicator in input area
            if (typingIndicator) {
                typingIndicator.classList.add('active');
            }
        }
        
        function removeTyping() {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
            
            // Hide typing indicator in input area
            if (typingIndicator) {
                typingIndicator.classList.remove('active');
            }
        }
        
        function clearMessages() {
            // Remove jarvis startup when first real message arrives
            const jarvisStartup = document.querySelector('.jarvis-startup');
            if (jarvisStartup) {
                jarvisStartup.style.opacity = '0';
                jarvisStartup.style.transform = 'translateY(-20px)';
                setTimeout(() => jarvisStartup.remove(), 300);
            }
        }
        
        function scrollToBottom() {
            messages.scrollTop = messages.scrollHeight;
        }

        function sendMessage() {
            const message = input.value.trim();
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                // Clear welcome message on first user message
                if (messageCount === 0) {
                    clearMessages();
                }
                addMessage('user', message);
                addTyping();
                ws.send(JSON.stringify({message: message}));
                input.value = '';
                autoResize();
                updateSendButton();
                
                // Close mobile sidebar if open
                if (window.innerWidth <= 1024 && mcpSidebar.classList.contains('show')) {
                    mcpSidebar.classList.remove('show');
                    if (mobileSidebarToggle) {
                        mobileSidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
                    }
                }
            }
        }
        
        function autoResize() {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        }
        
        function updateSendButton() {
            const hasText = input.value.trim().length > 0;
            const isConnected = ws && ws.readyState === WebSocket.OPEN;
            sendBtn.disabled = !hasText || !isConnected;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/\\n/g, '<br>');
        }

        // Event listeners
        sendBtn.addEventListener('click', sendMessage);
        
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        input.addEventListener('input', function() {
            autoResize();
            updateSendButton();
        });

        // Settings functions
        function initializeSettings() {
            // Load settings from localStorage
            const saved = localStorage.getItem('jarvis-settings');
            if (saved) {
                currentSettings = { ...currentSettings, ...JSON.parse(saved) };
            }
            
            // Load server settings
            loadServerSettings();
            updateSettingsUI();
            
            // Check MCP servers
            checkMCPServers();
        }
        
        async function loadServerSettings() {
            try {
                const response = await fetch('/settings');
                const serverSettings = await response.json();
                currentSettings = { ...currentSettings, ...serverSettings };
                updateSettingsUI();
            } catch (error) {
                console.error('Failed to load server settings:', error);
            }
        }
        
        async function checkMCPServers() {
            // Check all MCP servers through main server (avoids CORS issues)
            try {
                const response = await fetch('/settings');
                const settings = await response.json();
                
                // Update filesystem server status
                const fsStatus = document.getElementById('fsStatus');
                const fsToggle = document.getElementById('fsToggle');
                updateMCPStatus(fsStatus, fsToggle, settings.mcp_servers?.filesystem, 'filesystem');
                
                // Update git server status
                const gitStatus = document.getElementById('gitStatus');
                const gitToggle = document.getElementById('gitToggle');
                updateMCPStatus(gitStatus, gitToggle, settings.mcp_servers?.git, 'git');
                
                // Update terminal server status
                const terminalStatus = document.getElementById('terminalStatus');
                const terminalToggle = document.getElementById('terminalToggle');
                updateMCPStatus(terminalStatus, terminalToggle, settings.mcp_servers?.terminal, 'terminal');
                
            } catch (error) {
                console.error('Failed to check MCP servers:', error);
                // Set all to error state
                ['fsStatus', 'gitStatus', 'terminalStatus'].forEach(id => {
                    const status = document.getElementById(id);
                    if (status) {
                        status.textContent = 'Error';
                        status.style.color = 'var(--danger)';
                    }
                });
                
                // Update indicators for error state
                updateSidebarIndicators('filesystem', false);
                updateSidebarIndicators('git', false);
                updateSidebarIndicators('terminal', false);
                updateToolIndicators('filesystem', false);
                updateToolIndicators('git', false);
                updateToolIndicators('terminal', false);
            }
        }
        
        function updateMCPStatus(statusElement, toggleElement, isOnline, serverType) {
            if (isOnline) {
                statusElement.textContent = 'Online';
                statusElement.style.color = 'var(--success)';
                toggleElement.disabled = false;
                toggleElement.textContent = currentSettings.mcp_enabled[serverType] ? 'Disable' : 'Enable';
            } else {
                statusElement.textContent = 'Offline';
                statusElement.style.color = 'var(--danger)';
                toggleElement.disabled = true;
                toggleElement.textContent = 'Enable';
            }
            
            // Update sidebar indicators
            updateSidebarIndicators(serverType, isOnline);
            
            // Update header tool indicators
            updateToolIndicators(serverType, isOnline);
        }
        
        function updateSettingsUI() {
            document.getElementById('modelSelect').value = currentSettings.model;
            document.getElementById('temperatureSlider').value = currentSettings.temperature;
            document.getElementById('tempValue').textContent = currentSettings.temperature;
            document.getElementById('maxTokensInput').value = currentSettings.max_tokens;
            document.getElementById('themeSelect').value = currentSettings.theme;
            document.getElementById('animationsToggle').checked = currentSettings.animations;
        }
        
        async function saveSettingsToServer() {
            try {
                const response = await fetch('/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(currentSettings)
                });
                
                if (response.ok) {
                    addMessage('system', 'Settings saved successfully!');
                } else {
                    addMessage('system', 'Failed to save settings to server.');
                }
            } catch (error) {
                console.error('Failed to save settings:', error);
                addMessage('system', 'Error saving settings to server.');
            }
        }
        
        function exportSettings() {
            const dataStr = JSON.stringify(currentSettings, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = 'jarvis-settings.json';
            link.click();
            
            URL.revokeObjectURL(url);
            addMessage('system', 'Settings exported successfully!');
        }
        
        function importSettings() {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            
            input.onchange = function(event) {
                const file = event.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        try {
                            const imported = JSON.parse(e.target.result);
                            currentSettings = { ...currentSettings, ...imported };
                            updateSettingsUI();
                            localStorage.setItem('jarvis-settings', JSON.stringify(currentSettings));
                            addMessage('system', 'Settings imported successfully!');
                        } catch (error) {
                            addMessage('system', 'Failed to import settings. Invalid file format.');
                        }
                    };
                    reader.readAsText(file);
                }
            };
            
            input.click();
        }
        
        // Settings event listeners
        settingsBtn.addEventListener('click', () => {
            settingsPanel.classList.add('active');
            // Refresh MCP status when settings panel opens
            checkMCPServers();
        });
        
        closeSettings.addEventListener('click', () => {
            settingsPanel.classList.remove('active');
        });
        
        saveSettings.addEventListener('click', () => {
            // Update settings from UI
            currentSettings.model = document.getElementById('modelSelect').value;
            currentSettings.temperature = parseFloat(document.getElementById('temperatureSlider').value);
            currentSettings.max_tokens = parseInt(document.getElementById('maxTokensInput').value);
            currentSettings.theme = document.getElementById('themeSelect').value;
            currentSettings.animations = document.getElementById('animationsToggle').checked;
            
            // Save to localStorage
            localStorage.setItem('jarvis-settings', JSON.stringify(currentSettings));
            
            // Save to server
            saveSettingsToServer();
            
            settingsPanel.classList.remove('active');
        });
        
        document.getElementById('temperatureSlider').addEventListener('input', (e) => {
            document.getElementById('tempValue').textContent = e.target.value;
        });
        
        document.getElementById('exportSettings').addEventListener('click', exportSettings);
        document.getElementById('importSettings').addEventListener('click', importSettings);
        
        document.getElementById('clearData').addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
                localStorage.clear();
                addMessage('system', 'All data cleared successfully!');
                location.reload();
            }
        });
        
        // New UI functions
        function updateSidebarIndicators(serverType, isOnline) {
            let indicator;
            let statusElement;
            let card;
            
            switch(serverType) {
                case 'filesystem':
                    indicator = fsIndicator;
                    statusElement = sidebarFsStatus;
                    card = document.getElementById('fsCard');
                    break;
                case 'git':
                    indicator = gitIndicator;
                    statusElement = sidebarGitStatus;
                    card = document.getElementById('gitCard');
                    break;
                case 'terminal':
                    indicator = terminalIndicator;
                    statusElement = sidebarTerminalStatus;
                    card = document.getElementById('terminalCard');
                    break;
            }
            
            if (indicator && statusElement && card) {
                if (isOnline) {
                    indicator.classList.add('online');
                    statusElement.textContent = 'Online';
                    statusElement.style.color = 'var(--success)';
                    card.classList.add('online');
                    card.classList.remove('offline');
                } else {
                    indicator.classList.remove('online');
                    statusElement.textContent = 'Offline';
                    statusElement.style.color = 'var(--danger)';
                    card.classList.add('offline');
                    card.classList.remove('online');
                }
            }
        }
        
        function updateToolIndicators(serverType, isOnline) {
            let toolIndicator;
            
            switch(serverType) {
                case 'filesystem':
                    toolIndicator = fsToolIndicator;
                    break;
                case 'git':
                    toolIndicator = gitToolIndicator;
                    break;
                case 'terminal':
                    toolIndicator = terminalToolIndicator;
                    break;
            }
            
            if (toolIndicator) {
                if (isOnline) {
                    toolIndicator.classList.add('active');
                } else {
                    toolIndicator.classList.remove('active');
                }
            }
        }
        
        function updateSystemStats() {
            // Update message count
            if (messageCountElement) {
                messageCountElement.textContent = messageCount;
            }
        }
        
        function toggleSidebar() {
            sidebarCollapsed = !sidebarCollapsed;
            if (sidebarCollapsed) {
                mcpSidebar.classList.add('collapsed');
                mainContainer.classList.add('sidebar-collapsed');
                sidebarToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
            } else {
                mcpSidebar.classList.remove('collapsed');
                mainContainer.classList.remove('sidebar-collapsed');
                sidebarToggle.innerHTML = '<i class="fas fa-chevron-left"></i>';
            }
        }
        
        function toggleFabMenu() {
            fabMenuOpen = !fabMenuOpen;
            if (fabMenuOpen) {
                fabMenu.classList.add('active');
                quickActionsBtn.style.transform = 'rotate(45deg)';
            } else {
                fabMenu.classList.remove('active');
                quickActionsBtn.style.transform = 'rotate(0deg)';
            }
        }
        
        function handleFabAction(action) {
            toggleFabMenu();
            
            switch(action) {
                case 'status':
                    addMessage('user', 'Show system status');
                    sendMessage();
                    break;
                case 'code':
                    addMessage('user', 'Help me analyze my code');
                    sendMessage();
                    break;
                case 'files':
                    addMessage('user', 'List files in current directory');
                    sendMessage();
                    break;
                case 'help':
                    addMessage('user', 'What can you help me with?');
                    sendMessage();
                    break;
            }
        }
        
        // MCP toggle handlers
        document.getElementById('fsToggle').addEventListener('click', () => {
            currentSettings.mcp_enabled.filesystem = !currentSettings.mcp_enabled.filesystem;
            const toggle = document.getElementById('fsToggle');
            toggle.textContent = currentSettings.mcp_enabled.filesystem ? 'Disable' : 'Enable';
            
            if (currentSettings.mcp_enabled.filesystem) {
                addMessage('system', 'Filesystem MCP server enabled. Jarvis can now access files.');
            } else {
                addMessage('system', 'Filesystem MCP server disabled.');
            }
        });

        // UI Event Listeners
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }
        
        if (quickActionsBtn) {
            quickActionsBtn.addEventListener('click', toggleFabMenu);
        }
        
        // Handle FAB actions
        document.querySelectorAll('.fab-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.getAttribute('data-action');
                handleFabAction(action);
            });
        });
        
        // Auto-update system stats
        setInterval(updateSystemStats, 1000);
        
        // Auto-refresh MCP servers status with visual feedback
        setInterval(() => {
            // Add subtle pulse to show system is active
            const indicators = document.querySelectorAll('.server-indicator');
            indicators.forEach(indicator => {
                indicator.style.animation = 'none';
                indicator.offsetHeight; // Trigger reflow
                indicator.style.animation = null;
            });
            checkMCPServers();
        }, 30000); // Every 30 seconds
        
        // Mobile sidebar toggle
        const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
        
        function toggleMobileSidebar() {
            if (window.innerWidth <= 1024) {
                const isVisible = mcpSidebar.classList.contains('show');
                if (isVisible) {
                    mcpSidebar.classList.remove('show');
                    mobileSidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
                } else {
                    mcpSidebar.classList.add('show');
                    mobileSidebarToggle.innerHTML = '<i class="fas fa-times"></i>';
                }
            }
        }
        
        if (mobileSidebarToggle) {
            mobileSidebarToggle.addEventListener('click', toggleMobileSidebar);
        }
        
        // Handle responsive sidebar on mobile
        if (window.innerWidth <= 1024) {
            sidebarCollapsed = true;
            mcpSidebar.classList.add('collapsed');
            mainContainer.classList.add('sidebar-collapsed');
            if (sidebarToggle) {
                sidebarToggle.innerHTML = '<i class="fas fa-chevron-right"></i>';
            }
        }
        
        // Close mobile sidebar when clicking outside
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024 && 
                mcpSidebar.classList.contains('show') && 
                !mcpSidebar.contains(e.target) && 
                !mobileSidebarToggle.contains(e.target)) {
                mcpSidebar.classList.remove('show');
                mobileSidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1024) {
                mcpSidebar.classList.remove('show');
                mobileSidebarToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
        
        // Connect on load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, starting connection...');
            initializeSettings();
            connect();
            updateSystemStats();
        });
        
        // Also try to connect immediately
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initializeSettings();
                connect();
                updateSystemStats();
            });
        } else {
            initializeSettings();
            connect();
            updateSystemStats();
        }
    </script>
</body>
</html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("WebSocket connection attempt")
    try:
        await websocket.accept()
        print("WebSocket connection accepted")
        connections.append(websocket)
        print(f"Total connections: {len(connections)}")
        
        while True:
            data = await websocket.receive_text()
            print(f"Received message: {data}")
            message_data = json.loads(data)
            user_message = message_data.get("message", "").strip()
            
            if user_message:
                if claude_client:
                    try:
                        # Check which MCP servers are enabled
                        fs_enabled = await check_mcp_server("http://localhost:8001")
                        git_enabled = await check_mcp_server("http://localhost:8002")
                        terminal_enabled = await check_mcp_server("http://localhost:8003")
                        
                        # Enhanced prompt with MCP capabilities
                        mcp_info = ""
                        if fs_enabled or git_enabled or terminal_enabled:
                            mcp_info = "\n\nAVAILABLE DEVELOPMENT TOOLS:"
                            
                        if fs_enabled:
                            mcp_info += """
- 📁 FILESYSTEM: Read, write, list files and directories in BoarderframeOS project
- Example: "read the README file", "list all Python files", "create a new config file"""
                            
                        if git_enabled:
                            mcp_info += """
- 🔄 GIT: Version control operations (status, add, commit, push, pull, branches)  
- Example: "show git status", "commit these changes", "create a new branch"""
                            
                        if terminal_enabled:
                            mcp_info += """
- 💻 TERMINAL: Run Python scripts, install packages, run tests, execute commands
- Example: "run the tests", "install package X", "execute this Python script"""

                        prompt = f"""You are Jarvis, a helpful AI assistant powered by Claude 4. You're part of BoarderframeOS, an AI business operating system.

{mcp_info}

User message: "{user_message}"

Respond in a friendly, helpful, and conversational way. If the user asks about files or filesystem operations and you have filesystem access enabled, let them know you can help with that. Keep your response concise but informative. Be professional yet approachable."""

                        response = await claude_client.generate(prompt, max_tokens=1000, temperature=0.5)
                        
                        # Check if user is asking for development operations
                        hints = []
                        if fs_enabled and any(word in user_message.lower() for word in ['file', 'read', 'write', 'list', 'directory', 'folder']):
                            hints.append("📁 *I can help with file operations - reading, writing, and listing files!*")
                            
                        if git_enabled and any(word in user_message.lower() for word in ['git', 'commit', 'push', 'pull', 'branch', 'status', 'diff']):
                            hints.append("🔄 *I can help with git operations - status, commits, branches, and more!*")
                            
                        if terminal_enabled and any(word in user_message.lower() for word in ['run', 'execute', 'install', 'test', 'command', 'script']):
                            hints.append("💻 *I can run commands, install packages, and execute scripts!*")
                            
                        if hints:
                            response += "\n\n" + " ".join(hints)
                        
                        await websocket.send_text(json.dumps({
                            "type": "jarvis",
                            "message": response
                        }))
                        
                    except Exception as e:
                        await websocket.send_text(json.dumps({
                            "type": "jarvis",
                            "message": f"I'm experiencing some technical difficulties: {str(e)}"
                        }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "jarvis",
                        "message": "I'm not properly configured. Please check the API key setup."
                    }))
                    
    except WebSocketDisconnect:
        print("WebSocket disconnected")
        if websocket in connections:
            connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in connections:
            connections.remove(websocket)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "claude_available": claude_client is not None,
        "connections": len(connections),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test():
    return {"message": "Server is working", "websocket_available": True}

@app.get("/settings")
async def get_settings():
    return {
        "model": CLAUDE_OPUS_CONFIG.model,
        "temperature": CLAUDE_OPUS_CONFIG.temperature,
        "max_tokens": CLAUDE_OPUS_CONFIG.max_tokens,
        "mcp_servers": {
            "filesystem": await check_mcp_server("http://localhost:8001"),
            "git": await check_mcp_server("http://localhost:8002"),
            "terminal": await check_mcp_server("http://localhost:8003")
        }
    }

@app.post("/settings")
async def update_settings(settings: dict):
    # Update Claude configuration
    global claude_client
    if settings.get("model"):
        CLAUDE_OPUS_CONFIG.model = settings["model"]
    if settings.get("temperature") is not None:
        CLAUDE_OPUS_CONFIG.temperature = settings["temperature"]
    if settings.get("max_tokens"):
        CLAUDE_OPUS_CONFIG.max_tokens = settings["max_tokens"]
    
    # Reinitialize Claude client with new settings
    claude_client = LLMClient(CLAUDE_OPUS_CONFIG)
    
    return {"success": True, "message": "Settings updated successfully"}

async def check_mcp_server(url: str) -> bool:
    """Check if MCP server is available"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/health", timeout=2.0)
            return response.status_code == 200
    except:
        return False

@app.post("/mcp/filesystem")
async def call_filesystem_mcp(operation: dict):
    """Call filesystem MCP server"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/rpc",
                json=operation,
                timeout=10.0
            )
            return response.json()
    except Exception as e:
        return {"error": str(e)}

async def main():
    print("🚀 Starting Jarvis Web Chat")
    print("=" * 40)
    
    # Initialize Claude
    if not await init_claude():
        print("Cannot start without API key")
        return
    
    print("🌐 Starting server on http://localhost:8890")
    print("Open your browser and go to: http://localhost:8890")
    print("Press Ctrl+C to stop")
    
    config = uvicorn.Config(
        app, 
        host="127.0.0.1", 
        port=8890, 
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())