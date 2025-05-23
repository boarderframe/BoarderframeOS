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
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis AI Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --dark-gradient: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            --glass-bg: rgba(255, 255, 255, 0.25);
            --glass-border: rgba(255, 255, 255, 0.18);
            --shadow-light: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            --shadow-heavy: 0 15px 35px rgba(0, 0, 0, 0.1);
            --text-primary: #2c3e50;
            --text-secondary: #7f8c8d;
            --success: #00d4aa;
            --danger: #ff6b6b;
            --warning: #feca57;
        }
        
        * { 
            margin: 0; 
            padding: 0; 
            box-sizing: border-box; 
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            background: var(--primary-gradient);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(circle at 25% 25%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .chat-container {
            width: 100%;
            max-width: 900px;
            height: 90vh;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-radius: 24px;
            border: 1px solid var(--glass-border);
            box-shadow: var(--shadow-light);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            z-index: 1;
        }
        
        .header {
            background: var(--dark-gradient);
            color: white;
            padding: 24px 32px;
            position: relative;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
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
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        
        .logo {
            width: 48px;
            height: 48px;
            background: var(--secondary-gradient);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            animation: pulse 2s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .title-section h1 {
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 4px;
            background: linear-gradient(45deg, #fff, #f0f0f0);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            font-size: 14px;
            opacity: 0.8;
            font-weight: 400;
        }
        
        .status-section {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .settings-btn {
            width: 36px;
            height: 36px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 16px;
        }
        
        .settings-btn:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: rotate(90deg);
        }
        
        .status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--danger);
            transition: all 0.3s ease;
            position: relative;
            box-shadow: 0 0 12px rgba(255, 107, 107, 0.6);
        }
        
        .status.connected {
            background: var(--success);
            box-shadow: 0 0 12px rgba(0, 212, 170, 0.6);
        }
        
        .status.connected::after {
            content: '';
            position: absolute;
            width: 12px;
            height: 12px;
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
            font-size: 12px;
            opacity: 0.9;
            font-weight: 500;
        }
        
        .messages {
            flex: 1;
            padding: 32px;
            overflow-y: auto;
            background: linear-gradient(180deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                rgba(255, 255, 255, 0.05) 100%);
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
            background: rgba(255, 255, 255, 0.9);
            color: var(--text-primary);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-bottom-left-radius: 6px;
            backdrop-filter: blur(8px);
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
            padding: 24px 32px 32px;
            background: rgba(255, 255, 255, 0.1);
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
            padding: 16px 20px;
            border: none;
            background: transparent;
            font-size: 16px;
            outline: none;
            resize: none;
            max-height: 120px;
            min-height: 24px;
            font-family: inherit;
            color: var(--text-primary);
            font-weight: 400;
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
            body {
                padding: 10px;
            }
            
            .chat-container {
                height: 95vh;
                border-radius: 16px;
            }
            
            .header {
                padding: 20px 24px;
            }
            
            .logo {
                width: 40px;
                height: 40px;
                font-size: 20px;
            }
            
            .title-section h1 {
                font-size: 20px;
            }
            
            .messages {
                padding: 24px 20px;
            }
            
            .message-content {
                max-width: 85%;
                padding: 14px 18px;
            }
            
            .input-area {
                padding: 20px 20px 24px;
            }
            
            .input-group {
                gap: 12px;
            }
            
            #messageInput {
                padding: 14px 18px;
                font-size: 16px;
            }
            
            #sendBtn {
                width: 48px;
                height: 48px;
                font-size: 18px;
            }
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
    <div class="chat-container">
        <div class="header">
            <div class="header-content">
                <div class="logo-section">
                    <div class="logo">🤖</div>
                    <div class="title-section">
                        <h1>Jarvis AI Assistant</h1>
                        <div class="subtitle">Powered by Claude 4 Opus • BoarderframeOS</div>
                    </div>
                </div>
                
                <div class="status-section">
                    <button id="settingsBtn" class="settings-btn">
                        <i class="fas fa-cog"></i>
                    </button>
                    <div class="status" id="status"></div>
                    <div class="status-text" id="statusText">Connecting...</div>
                </div>
            </div>
        </div>
        
        <div class="messages" id="messages">
            <div class="message system">
                <div class="message-content">
                    Initializing Jarvis AI Assistant...
                </div>
            </div>
        </div>
        
        <div class="input-area">
            <div class="input-group">
                <textarea id="messageInput" placeholder="Ask Jarvis anything..." disabled rows="1"></textarea>
                <button id="sendBtn" disabled>
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
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
                    console.log('WebSocket connected successfully');
                    clearTimeout(connectionTimeout);
                    connectionAttempts = 0;
                    status.classList.add('connected');
                    statusText.textContent = 'Online';
                    input.disabled = false;
                    updateSendButton();
                    clearMessages();
                    addMessage('system', 'Connected to Jarvis! Ready to assist you.');
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
            } else if (type === 'jarvis') {
                avatar = '<div class="avatar">J</div>';
                content = `
                    <div style="flex: 1;">
                        <div class="message-content">${escapeHtml(message)}</div>
                        <div class="timestamp">${timeStr}</div>
                    </div>
                `;
            } else if (type === 'system') {
                messageDiv.innerHTML = `<div class="message-content">${escapeHtml(message)}</div>`;
                messages.appendChild(messageDiv);
                scrollToBottom();
                return;
            }
            
            messageDiv.innerHTML = avatar + content;
            messages.appendChild(messageDiv);
            scrollToBottom();
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
            messages.innerHTML = '';
        }
        
        function scrollToBottom() {
            messages.scrollTop = messages.scrollHeight;
        }

        function sendMessage() {
            const message = input.value.trim();
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                addMessage('user', message);
                addTyping();
                ws.send(JSON.stringify({message: message}));
                input.value = '';
                autoResize();
                updateSendButton();
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

        // Connect on load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('DOM loaded, starting connection...');
            initializeSettings();
            connect();
        });
        
        // Also try to connect immediately
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initializeSettings();
                connect();
            });
        } else {
            initializeSettings();
            connect();
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