#!/usr/bin/env python3
"""
Jarvis Web Chat - Friendly and Warm Version
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
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis AI Assistant - Friendly Mode</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            /* Warm, friendly color system */
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --accent-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --warm-gradient: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            --success-gradient: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            
            /* Glass Morphism - darker for better contrast */
            --glass-bg: rgba(0, 0, 0, 0.4);
            --glass-border: rgba(255, 255, 255, 0.2);
            --glass-hover: rgba(0, 0, 0, 0.5);
            --glass-active: rgba(0, 0, 0, 0.6);
            
            /* Gentle shadows */
            --shadow-soft: 0 8px 32px rgba(31, 38, 135, 0.15);
            --shadow-medium: 0 12px 40px rgba(31, 38, 135, 0.25);
            --shadow-warm: 0 8px 25px rgba(255, 154, 158, 0.2);
            
            /* High contrast text colors */
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --text-white: rgba(255, 255, 255, 1);
            --text-white-secondary: rgba(255, 255, 255, 0.9);
            
            /* Status colors */
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --info: #3b82f6;
            
            /* Layout */
            --sidebar-width: 320px;
            --sidebar-collapsed: 60px;
            --border-radius: 16px;
            --border-radius-small: 8px;
            --border-radius-large: 24px;
            
            /* Gentle transitions */
            --transition-fast: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            --transition-medium: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
        
        /* Mobile Sidebar Toggle */
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
            display: none;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-medium);
        }
        
        .mobile-sidebar-toggle:hover {
            background: var(--glass-hover);
            transform: scale(1.05);
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
            animation: gentlePulse 2s infinite;
            flex-shrink: 0;
            margin-left: auto;
        }
        
        .server-indicator.online {
            background: var(--success);
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
        }
        
        @keyframes gentlePulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        
        .sidebar-footer {
            padding: 16px 20px;
            border-top: 1px solid var(--glass-border);
            background: rgba(0, 0, 0, 0.2);
            margin-top: auto;
            text-align: center;
        }
        
        .powered-by {
            color: var(--text-white-secondary);
            font-size: 11px;
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
        }
        
        .powered-by i {
            color: var(--info);
            font-size: 12px;
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
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 20px 32px;
            position: relative;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 80px;
            display: flex;
            align-items: center;
        }
        
        .header-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            z-index: 1;
            width: 100%;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo {
            width: 44px;
            height: 44px;
            background: var(--warm-gradient);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: var(--shadow-warm);
            animation: gentleGlow 3s ease-in-out infinite;
        }
        
        @keyframes gentleGlow {
            0%, 100% { 
                box-shadow: var(--shadow-warm);
                transform: scale(1);
            }
            50% { 
                box-shadow: 0 8px 25px rgba(255, 154, 158, 0.4);
                transform: scale(1.02);
            }
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
        
        /* Header Controls */
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
        }
        
        .tool-indicator:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-1px);
            border-color: rgba(255, 255, 255, 0.3);
        }
        
        .tool-indicator.active {
            background: var(--success);
            border-color: var(--success);
            color: white;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
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
            animation: gentlePulse 2s infinite;
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
        
        .status-text {
            font-size: 11px;
            opacity: 0.8;
            font-weight: 500;
            color: var(--text-white);
        }
        
        /* Messages Area */
        .messages {
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            background: linear-gradient(180deg, 
                rgba(0, 0, 0, 0.1) 0%, 
                rgba(0, 0, 0, 0.05) 100%);
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
        
        /* Jarvis Startup Animation */
        .jarvis-startup {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            padding: 32px;
            margin: 24px;
            height: calc(100vh - 240px);
            max-height: 600px;
            position: relative;
            overflow: hidden;
        }
        
        .startup-animation {
            margin-bottom: 24px;
            position: relative;
        }
        
        .jarvis-core {
            position: relative;
            width: 80px;
            height: 80px;
            margin: 0 auto;
        }
        
        .core-ring {
            position: absolute;
            border-radius: 50%;
            border: 2px solid;
            opacity: 0.6;
            animation: coreRing 3s ease-in-out infinite;
        }
        
        .core-ring-1 {
            width: 80px;
            height: 80px;
            border-color: #667eea;
            animation-delay: 0s;
        }
        
        .core-ring-2 {
            width: 64px;
            height: 64px;
            top: 8px;
            left: 8px;
            border-color: #764ba2;
            animation-delay: 0.3s;
        }
        
        .core-ring-3 {
            width: 48px;
            height: 48px;
            top: 16px;
            left: 16px;
            border-color: #4facfe;
            animation-delay: 0.6s;
        }
        
        @keyframes coreRing {
            0%, 100% {
                transform: scale(1);
                opacity: 0.6;
            }
            50% {
                transform: scale(1.1);
                opacity: 0.3;
            }
        }
        
        .jarvis-avatar {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            background: var(--warm-gradient);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 0 20px rgba(255, 154, 158, 0.6);
            animation: avatarGlow 2s ease-in-out infinite alternate;
        }
        
        @keyframes avatarGlow {
            0% {
                box-shadow: 0 0 20px rgba(255, 154, 158, 0.6);
            }
            100% {
                box-shadow: 0 0 40px rgba(255, 154, 158, 0.8), 0 0 60px rgba(255, 154, 158, 0.4);
            }
        }
        
        .startup-sequence {
            display: flex;
            flex-direction: column;
            gap: 8px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
        }
        
        .startup-line {
            color: var(--text-white-secondary);
            font-size: 12px;
            opacity: 0;
            transform: translateX(-20px);
            animation: startupLine 0.5s ease-out forwards;
        }
        
        .startup-line.success {
            color: var(--success);
            font-weight: 600;
        }
        
        .startup-line:nth-child(1) { animation-delay: 0s; }
        .startup-line:nth-child(2) { animation-delay: 0.5s; }
        .startup-line:nth-child(3) { animation-delay: 1s; }
        .startup-line:nth-child(4) { animation-delay: 1.5s; }
        
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
            padding: 24px;
            backdrop-filter: blur(16px);
            box-shadow: var(--shadow-soft);
            animation: fadeInUp 0.6s ease-out forwards;
            max-width: 500px;
            margin: 0 auto;
            max-height: 320px;
            overflow: hidden;
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
            font-size: 20px;
            font-weight: 700;
            color: var(--text-white);
            margin-bottom: 12px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .jarvis-intro {
            font-size: 14px;
            color: var(--text-white-secondary);
            margin-bottom: 16px;
            line-height: 1.4;
        }
        
        .capability-showcase {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }
        
        .capability-card {
            background: var(--glass-hover);
            border: 1px solid var(--glass-border);
            border-radius: var(--border-radius);
            padding: 8px 12px;
            text-align: center;
            transition: all var(--transition-medium);
            opacity: 0;
            transform: translateY(20px);
            animation: slideInUp 0.4s ease-out forwards;
            min-width: 120px;
            flex: 0 0 auto;
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
            width: 24px;
            height: 24px;
            background: var(--primary-gradient);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
            margin: 0 auto 6px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }
        
        .capability-info h4 {
            font-size: 11px;
            font-weight: 600;
            color: var(--text-white);
            margin: 0;
            text-align: center;
        }
        
        .quick-start {
            background: rgba(255, 154, 158, 0.1);
            border: 1px solid rgba(255, 154, 158, 0.2);
            border-radius: var(--border-radius);
            padding: 12px;
            color: var(--text-white-secondary);
            font-size: 12px;
            opacity: 0;
            animation: fadeIn 0.4s ease-out forwards;
        }
        
        .quick-start strong {
            color: var(--text-white);
            background: rgba(255, 154, 158, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }
        
        @keyframes fadeIn {
            to {
                opacity: 1;
            }
        }
        
        /* Message Styles */
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
            background: var(--warm-gradient);
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
            background: rgba(255, 154, 158, 0.15);
            color: #e91e63;
            border: 1px solid rgba(255, 154, 158, 0.3);
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
        
        /* Input Area */
        .input-area {
            padding: 20px 24px 24px;
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(16px);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .input-group {
            display: flex;
            gap: 8px;
            align-items: center;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 4px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(16px);
            border: 2px solid rgba(102, 126, 234, 0.3);
            transition: all var(--transition-medium);
        }
        
        .input-group:focus-within {
            border-color: rgba(102, 126, 234, 0.6);
            box-shadow: 0 4px 24px rgba(102, 126, 234, 0.25);
        }
        
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: none;
            background: transparent;
            font-size: 15px;
            outline: none;
            resize: none;
            max-height: 120px;
            min-height: 24px;
            font-family: inherit;
            color: var(--text-primary);
            font-weight: 400;
            line-height: 1.5;
        }
        
        #messageInput::placeholder {
            color: var(--text-secondary);
            font-weight: 400;
        }
        
        .input-actions {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        
        .send-btn {
            width: 44px;
            height: 44px;
            border: none;
            border-radius: 50%;
            background: var(--primary-gradient);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all var(--transition-medium);
            font-size: 16px;
            font-weight: 600;
            box-shadow: 0 2px 12px rgba(102, 126, 234, 0.4);
            position: relative;
            overflow: hidden;
            margin: 4px;
        }
        
        .send-btn:hover:not(:disabled) {
            transform: scale(1.08);
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6);
        }
        
        .send-btn:active {
            transform: scale(0.95);
        }
        
        .send-btn:disabled {
            background: var(--text-secondary);
            cursor: not-allowed;
            box-shadow: none;
            transform: scale(1);
        }
        
        /* Responsive Design */
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
            
            .mobile-sidebar-toggle {
                display: flex;
            }
        }
        
        @media (max-width: 768px) {
            .mobile-sidebar-toggle {
                display: flex;
            }
            
            .chat-container {
                margin: 10px;
                border-radius: 16px;
            }
            
            .header {
                padding: 16px 20px;
                min-height: 70px;
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
            <div class="powered-by">
                <i class="fas fa-robot"></i>
                <span>Powered by Claude 4 Opus</span>
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
                    
                    <div class="welcome-message-new" style="opacity: 0; animation-delay: 2s;">
                        <h2 class="jarvis-greeting">Hello! I'm Jarvis, your friendly AI assistant.</h2>
                        <p class="jarvis-intro">Powered by Claude 4, I'm here to help with coding, project management, and development tasks.</p>
                        
                        <div class="capability-showcase">
                            <div class="capability-card" style="animation-delay: 2.2s;">
                                <div class="capability-icon">
                                    <i class="fas fa-folder-open"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>Files</h4>
                                </div>
                            </div>
                            
                            <div class="capability-card" style="animation-delay: 2.3s;">
                                <div class="capability-icon">
                                    <i class="fas fa-code-branch"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>Git</h4>
                                </div>
                            </div>
                            
                            <div class="capability-card" style="animation-delay: 2.4s;">
                                <div class="capability-icon">
                                    <i class="fas fa-terminal"></i>
                                </div>
                                <div class="capability-info">
                                    <h4>Terminal</h4>
                                </div>
                            </div>
                        </div>
                        
                        <div class="quick-start" style="animation-delay: 2.6s;">
                            <p>Ready to help! Try: <strong>"Show me the project files"</strong></p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <div class="input-group">
                    <textarea id="messageInput" placeholder="Ask Jarvis anything..." disabled rows="1"></textarea>
                    <button id="sendBtn" disabled class="send-btn">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
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
        
        // UI Elements
        const sidebarToggle = document.getElementById('sidebarToggle');
        const mcpSidebar = document.getElementById('mcpSidebar');
        const mainContainer = document.getElementById('mainContainer');
        const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');
        
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

        let connectionAttempts = 0;
        const maxAttempts = 3;
        let messageCount = 0;
        let sidebarCollapsed = false;
        
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
                    console.log('WebSocket connected successfully');
                    clearTimeout(connectionTimeout);
                    connectionAttempts = 0;
                    status.classList.add('connected');
                    statusText.textContent = 'Online';
                    input.disabled = false;
                    updateSendButton();
                    
                    // Gentle connection animation
                    const jarvisCore = document.querySelector('.jarvis-core');
                    if (jarvisCore) {
                        jarvisCore.style.animation = 'none';
                        jarvisCore.offsetHeight; // Trigger reflow
                        jarvisCore.style.animation = 'connectionSuccess 1s ease-out';
                    }
                    
                    // Don't add connection message - welcome screen is enough
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
                addMessage('system', 'Connection failed after multiple attempts. Please refresh the page.');
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
        }
        
        function removeTyping() {
            const typing = document.getElementById('typing-indicator');
            if (typing) typing.remove();
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
        
        function updateMCPStatus(statusElement, toggleElement, isOnline, serverType) {
            if (isOnline) {
                statusElement.textContent = 'Online';
                statusElement.style.color = 'var(--success)';
                toggleElement.disabled = false;
                toggleElement.textContent = 'Disable';
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
        
        async function checkMCPServers() {
            try {
                const response = await fetch('/settings');
                const settings = await response.json();
                
                // Update all server statuses
                updateMCPStatus(document.getElementById('fsStatus') || {textContent: '', style: {}}, 
                              document.getElementById('fsToggle') || {disabled: false, textContent: ''}, 
                              settings.mcp_servers?.filesystem, 'filesystem');
                              
                updateMCPStatus(document.getElementById('gitStatus') || {textContent: '', style: {}}, 
                              document.getElementById('gitToggle') || {disabled: false, textContent: ''}, 
                              settings.mcp_servers?.git, 'git');
                              
                updateMCPStatus(document.getElementById('terminalStatus') || {textContent: '', style: {}}, 
                              document.getElementById('terminalToggle') || {disabled: false, textContent: ''}, 
                              settings.mcp_servers?.terminal, 'terminal');
                
            } catch (error) {
                console.error('Failed to check MCP servers:', error);
                // Update indicators for error state
                updateSidebarIndicators('filesystem', false);
                updateSidebarIndicators('git', false);
                updateSidebarIndicators('terminal', false);
                updateToolIndicators('filesystem', false);
                updateToolIndicators('git', false);
                updateToolIndicators('terminal', false);
            }
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

        // UI Event Listeners
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }
        
        if (mobileSidebarToggle) {
            mobileSidebarToggle.addEventListener('click', toggleMobileSidebar);
        }
        
        // Auto-update system stats
        setInterval(updateSystemStats, 1000);
        
        // Auto-refresh MCP servers status
        setInterval(checkMCPServers, 30000); // Every 30 seconds
        
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
            connect();
            updateSystemStats();
        });
        
        // Also try to connect immediately
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                connect();
                updateSystemStats();
            });
        } else {
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
    print("🌟 Starting Jarvis Web Chat - Friendly Mode")
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