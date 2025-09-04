/**
 * PostMessage Bridge for MCP-UI Protocol
 * Handles secure communication between MCP servers and UI components
 */

export interface MCPMessage {
  type: string;
  id?: string;
  payload?: any;
  timestamp?: number;
  origin?: string;
}

export interface MCPResponse {
  type: string;
  id: string;
  success: boolean;
  data?: any;
  error?: string;
  timestamp: number;
}

type MessageHandler = (message: MCPMessage) => void | Promise<void>;
type ResponseHandler = (response: MCPResponse) => void;

class PostMessageBridge {
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private responseHandlers: Map<string, ResponseHandler> = new Map();
  private messageQueue: MCPMessage[] = [];
  private isReady = false;
  private targetOrigin = '*';
  private allowedOrigins: Set<string> = new Set();

  constructor() {
    this.initialize();
  }

  private initialize() {
    if (typeof window === 'undefined') return;

    window.addEventListener('message', this.handleMessage.bind(this));
    
    // Send ready signal
    this.sendMessage({
      type: 'MCP_UI_READY',
      timestamp: Date.now(),
    });

    this.isReady = true;
    this.flushQueue();
  }

  private handleMessage(event: MessageEvent) {
    // Security: Check origin if allowed origins are configured
    if (this.allowedOrigins.size > 0 && !this.allowedOrigins.has(event.origin)) {
      console.warn(`Blocked message from unauthorized origin: ${event.origin}`);
      return;
    }

    const message = event.data as MCPMessage;
    
    // Ignore non-MCP messages
    if (!message.type || !message.type.startsWith('MCP_')) {
      return;
    }

    message.origin = event.origin;
    message.timestamp = message.timestamp || Date.now();

    // Handle response messages
    if (message.type === 'MCP_RESPONSE' && message.id) {
      const handler = this.responseHandlers.get(message.id);
      if (handler) {
        handler(message as MCPResponse);
        this.responseHandlers.delete(message.id);
        return;
      }
    }

    // Handle regular messages
    const handlers = this.handlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          const result = handler(message);
          if (result instanceof Promise) {
            result.catch(error => {
              console.error(`Error handling message ${message.type}:`, error);
              this.sendError(message.id || '', error.message);
            });
          }
        } catch (error) {
          console.error(`Error handling message ${message.type}:`, error);
          this.sendError(message.id || '', error.message);
        }
      });
    }
  }

  /**
   * Set allowed origins for security
   */
  setAllowedOrigins(origins: string[]) {
    this.allowedOrigins = new Set(origins);
  }

  /**
   * Set target origin for postMessage
   */
  setTargetOrigin(origin: string) {
    this.targetOrigin = origin;
  }

  /**
   * Register a message handler
   */
  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);

    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.handlers.delete(type);
        }
      }
    };
  }

  /**
   * Remove a message handler
   */
  off(type: string, handler?: MessageHandler) {
    if (!handler) {
      this.handlers.delete(type);
    } else {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler);
      }
    }
  }

  /**
   * Send a message
   */
  sendMessage(message: MCPMessage) {
    if (!this.isReady) {
      this.messageQueue.push(message);
      return;
    }

    const fullMessage: MCPMessage = {
      ...message,
      timestamp: Date.now(),
    };

    if (window.parent && window.parent !== window) {
      window.parent.postMessage(fullMessage, this.targetOrigin);
    }

    // Also send to opener if exists (for popup scenarios)
    if (window.opener) {
      window.opener.postMessage(fullMessage, this.targetOrigin);
    }
  }

  /**
   * Send a request and wait for response
   */
  async sendRequest<T = any>(type: string, payload?: any, timeout = 5000): Promise<T> {
    const id = this.generateId();
    
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.responseHandlers.delete(id);
        reject(new Error(`Request ${type} timed out after ${timeout}ms`));
      }, timeout);

      this.responseHandlers.set(id, (response: MCPResponse) => {
        clearTimeout(timeoutId);
        if (response.success) {
          resolve(response.data as T);
        } else {
          reject(new Error(response.error || 'Unknown error'));
        }
      });

      this.sendMessage({
        type,
        id,
        payload,
      });
    });
  }

  /**
   * Send a response to a request
   */
  sendResponse(requestId: string, data: any, success = true) {
    this.sendMessage({
      type: 'MCP_RESPONSE',
      id: requestId,
      payload: {
        success,
        data,
        timestamp: Date.now(),
      },
    });
  }

  /**
   * Send an error response
   */
  sendError(requestId: string, error: string) {
    this.sendMessage({
      type: 'MCP_RESPONSE',
      id: requestId,
      payload: {
        success: false,
        error,
        timestamp: Date.now(),
      },
    });
  }

  /**
   * Flush queued messages
   */
  private flushQueue() {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.sendMessage(message);
      }
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Clean up
   */
  destroy() {
    window.removeEventListener('message', this.handleMessage.bind(this));
    this.handlers.clear();
    this.responseHandlers.clear();
    this.messageQueue = [];
  }
}

// Singleton instance
export const mcpBridge = new PostMessageBridge();

// React Hook for using the bridge
import { useEffect, useCallback } from 'react';

export function useMCPBridge() {
  const sendMessage = useCallback((type: string, payload?: any) => {
    mcpBridge.sendMessage({ type, payload });
  }, []);

  const sendRequest = useCallback(async <T = any>(type: string, payload?: any, timeout?: number) => {
    return mcpBridge.sendRequest<T>(type, payload, timeout);
  }, []);

  const onMessage = useCallback((type: string, handler: MessageHandler) => {
    return mcpBridge.on(type, handler);
  }, []);

  useEffect(() => {
    return () => {
      // Cleanup if needed
    };
  }, []);

  return {
    sendMessage,
    sendRequest,
    onMessage,
    bridge: mcpBridge,
  };
}

// Common MCP-UI Protocol Messages
export const MCPMessages = {
  // UI Events
  UI_READY: 'MCP_UI_READY',
  UI_RESIZE: 'MCP_UI_RESIZE',
  UI_THEME_CHANGE: 'MCP_UI_THEME_CHANGE',
  
  // Data Events
  DATA_REQUEST: 'MCP_DATA_REQUEST',
  DATA_UPDATE: 'MCP_DATA_UPDATE',
  DATA_SYNC: 'MCP_DATA_SYNC',
  
  // Action Events
  ACTION_EXECUTE: 'MCP_ACTION_EXECUTE',
  ACTION_RESULT: 'MCP_ACTION_RESULT',
  
  // Navigation Events
  NAVIGATE_TO: 'MCP_NAVIGATE_TO',
  ROUTE_CHANGE: 'MCP_ROUTE_CHANGE',
  
  // Authentication Events
  AUTH_REQUEST: 'MCP_AUTH_REQUEST',
  AUTH_SUCCESS: 'MCP_AUTH_SUCCESS',
  AUTH_FAILURE: 'MCP_AUTH_FAILURE',
  AUTH_LOGOUT: 'MCP_AUTH_LOGOUT',
  
  // Cart Events (Kroger specific)
  CART_ADD: 'MCP_CART_ADD',
  CART_REMOVE: 'MCP_CART_REMOVE',
  CART_UPDATE: 'MCP_CART_UPDATE',
  CART_CLEAR: 'MCP_CART_CLEAR',
  CART_CHECKOUT: 'MCP_CART_CHECKOUT',
  
  // Product Events (Kroger specific)
  PRODUCT_SEARCH: 'MCP_PRODUCT_SEARCH',
  PRODUCT_DETAILS: 'MCP_PRODUCT_DETAILS',
  PRODUCT_FAVORITE: 'MCP_PRODUCT_FAVORITE',
  
  // Location Events (Kroger specific)
  LOCATION_SEARCH: 'MCP_LOCATION_SEARCH',
  LOCATION_SELECT: 'MCP_LOCATION_SELECT',
  LOCATION_UPDATE: 'MCP_LOCATION_UPDATE',
} as const;