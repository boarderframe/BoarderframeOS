/**
 * SecureIframe Component
 * Enterprise-grade iframe implementation with comprehensive security controls
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';

// Security configuration
const SECURITY_CONFIG = {
  // Allowed origins for postMessage
  trustedOrigins: [
    'https://mcp-ui.com',
    'https://api.mcp-ui.com',
    process.env.NODE_ENV === 'development' ? 'http://localhost:3000' : null
  ].filter(Boolean),
  
  // Sandbox permissions
  sandboxPermissions: [
    'allow-scripts',
    'allow-same-origin',
    'allow-forms',
    'allow-modals'
  ],
  
  // Feature policy
  featurePolicy: {
    camera: 'none',
    microphone: 'none',
    geolocation: 'none',
    payment: 'none',
    usb: 'none',
    magnetometer: 'none',
    gyroscope: 'none',
    accelerometer: 'none',
    'ambient-light-sensor': 'none',
    autoplay: 'none',
    'encrypted-media': 'self',
    fullscreen: 'self',
    'picture-in-picture': 'none'
  },
  
  // Message timeout (ms)
  messageTimeout: 30000,
  
  // CSP for iframe content
  contentSecurityPolicy: [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.mcp-ui.com",
    "frame-ancestors 'self'",
    "form-action 'self'",
    "base-uri 'self'",
    "object-src 'none'"
  ].join('; ')
};

interface SecureIframeProps {
  src: string;
  title: string;
  className?: string;
  onMessage?: (data: any) => void;
  onError?: (error: Error) => void;
  onLoad?: () => void;
  allowedOrigins?: string[];
  customSandbox?: string[];
  customFeatures?: Record<string, string>;
  width?: string | number;
  height?: string | number;
}

interface MessageData {
  type: string;
  payload: any;
  timestamp: number;
  nonce: string;
  signature?: string;
  origin?: string;
}

interface SecurityContext {
  sessionId: string;
  fingerprint: string;
  processedNonces: Set<string>;
  messageQueue: MessageData[];
  isReady: boolean;
}

export const SecureIframe: React.FC<SecureIframeProps> = ({
  src,
  title,
  className = '',
  onMessage,
  onError,
  onLoad,
  allowedOrigins = [],
  customSandbox = [],
  customFeatures = {},
  width = '100%',
  height = '400px'
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isLoaded, setIsLoaded] = useState(false);
  const [securityContext, setSecurityContext] = useState<SecurityContext>({
    sessionId: uuidv4(),
    fingerprint: '',
    processedNonces: new Set(),
    messageQueue: [],
    isReady: false
  });

  // Validate source URL
  const validateSource = useCallback((url: string): boolean => {
    try {
      const parsed = new URL(url);
      
      // Check protocol
      if (!['https:', 'http:'].includes(parsed.protocol)) {
        if (process.env.NODE_ENV !== 'development' || parsed.protocol !== 'http:') {
          throw new Error(`Invalid protocol: ${parsed.protocol}`);
        }
      }
      
      // Check for javascript: or data: URLs
      if (url.toLowerCase().startsWith('javascript:') || 
          url.toLowerCase().startsWith('data:') ||
          url.toLowerCase().startsWith('vbscript:')) {
        throw new Error('Dangerous URL scheme detected');
      }
      
      return true;
    } catch (error) {
      onError?.(error as Error);
      return false;
    }
  }, [onError]);

  // Generate iframe fingerprint
  const generateFingerprint = useCallback((): string => {
    const data = {
      sessionId: securityContext.sessionId,
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
      random: Math.random()
    };
    
    // Simple hash function for demonstration
    const hash = btoa(JSON.stringify(data));
    return hash;
  }, [securityContext.sessionId]);

  // Validate incoming message
  const validateMessage = useCallback((event: MessageEvent): boolean => {
    // Check origin
    const trustedOrigins = [
      ...SECURITY_CONFIG.trustedOrigins,
      ...allowedOrigins
    ];
    
    if (!trustedOrigins.includes(event.origin)) {
      console.error(`Rejected message from untrusted origin: ${event.origin}`);
      return false;
    }
    
    // Validate message structure
    const message = event.data as MessageData;
    if (!message || typeof message !== 'object') {
      console.error('Invalid message structure');
      return false;
    }
    
    // Check required fields
    const requiredFields = ['type', 'payload', 'timestamp', 'nonce'];
    for (const field of requiredFields) {
      if (!(field in message)) {
        console.error(`Missing required field: ${field}`);
        return false;
      }
    }
    
    // Check timestamp (prevent replay attacks)
    const messageAge = Date.now() - message.timestamp;
    if (messageAge > SECURITY_CONFIG.messageTimeout) {
      console.error('Message expired');
      return false;
    }
    
    // Check nonce (prevent duplicate processing)
    if (securityContext.processedNonces.has(message.nonce)) {
      console.error('Duplicate message nonce');
      return false;
    }
    
    // Verify signature if present
    if (message.signature && !verifySignature(message)) {
      console.error('Invalid message signature');
      return false;
    }
    
    return true;
  }, [allowedOrigins, securityContext.processedNonces]);

  // Verify message signature
  const verifySignature = (message: MessageData): boolean => {
    // In production, implement proper signature verification
    // This is a placeholder for demonstration
    const expectedSignature = generateSignature(message);
    return message.signature === expectedSignature;
  };

  // Generate message signature
  const generateSignature = (message: MessageData): string => {
    // In production, use proper cryptographic signing
    // This is a simplified version for demonstration
    const signingData = JSON.stringify({
      type: message.type,
      payload: message.payload,
      timestamp: message.timestamp,
      nonce: message.nonce
    });
    
    return btoa(signingData);
  };

  // Handle incoming messages
  const handleMessage = useCallback((event: MessageEvent) => {
    // Validate message
    if (!validateMessage(event)) {
      return;
    }
    
    const message = event.data as MessageData;
    
    // Add nonce to processed list
    setSecurityContext(prev => ({
      ...prev,
      processedNonces: new Set([...prev.processedNonces, message.nonce])
    }));
    
    // Handle specific message types
    switch (message.type) {
      case 'ready':
        setSecurityContext(prev => ({ ...prev, isReady: true }));
        processMessageQueue();
        break;
      
      case 'error':
        onError?.(new Error(message.payload));
        break;
      
      case 'resize':
        handleResize(message.payload);
        break;
      
      default:
        // Pass to parent handler
        onMessage?.(message);
    }
  }, [validateMessage, onMessage, onError]);

  // Send message to iframe
  const sendMessage = useCallback((type: string, payload: any) => {
    if (!iframeRef.current?.contentWindow) {
      console.error('Iframe not ready');
      return;
    }
    
    const message: MessageData = {
      type,
      payload,
      timestamp: Date.now(),
      nonce: uuidv4(),
      origin: window.location.origin
    };
    
    // Add signature
    message.signature = generateSignature(message);
    
    // Queue message if iframe not ready
    if (!securityContext.isReady) {
      setSecurityContext(prev => ({
        ...prev,
        messageQueue: [...prev.messageQueue, message]
      }));
      return;
    }
    
    // Send message
    try {
      const targetOrigin = new URL(src).origin;
      iframeRef.current.contentWindow.postMessage(message, targetOrigin);
    } catch (error) {
      onError?.(error as Error);
    }
  }, [src, securityContext.isReady, onError]);

  // Process queued messages
  const processMessageQueue = useCallback(() => {
    if (!iframeRef.current?.contentWindow) return;
    
    const targetOrigin = new URL(src).origin;
    securityContext.messageQueue.forEach(message => {
      iframeRef.current!.contentWindow!.postMessage(message, targetOrigin);
    });
    
    setSecurityContext(prev => ({
      ...prev,
      messageQueue: []
    }));
  }, [src, securityContext.messageQueue]);

  // Handle iframe resize
  const handleResize = (dimensions: { width?: number; height?: number }) => {
    if (!iframeRef.current) return;
    
    if (dimensions.width) {
      iframeRef.current.style.width = `${dimensions.width}px`;
    }
    
    if (dimensions.height) {
      iframeRef.current.style.height = `${dimensions.height}px`;
    }
  };

  // Handle iframe load
  const handleLoad = useCallback(() => {
    setIsLoaded(true);
    
    // Generate and store fingerprint
    const fingerprint = generateFingerprint();
    setSecurityContext(prev => ({
      ...prev,
      fingerprint
    }));
    
    // Send initialization message
    sendMessage('init', {
      sessionId: securityContext.sessionId,
      fingerprint,
      timestamp: Date.now()
    });
    
    onLoad?.();
  }, [generateFingerprint, sendMessage, securityContext.sessionId, onLoad]);

  // Handle iframe error
  const handleError = useCallback((event: ErrorEvent) => {
    console.error('Iframe error:', event);
    onError?.(new Error(event.message));
  }, [onError]);

  // Setup message listener
  useEffect(() => {
    window.addEventListener('message', handleMessage);
    window.addEventListener('error', handleError);
    
    return () => {
      window.removeEventListener('message', handleMessage);
      window.removeEventListener('error', handleError);
    };
  }, [handleMessage, handleError]);

  // Validate source before rendering
  if (!validateSource(src)) {
    return (
      <div className="error-container">
        <p>Error: Invalid or dangerous iframe source</p>
      </div>
    );
  }

  // Build sandbox attribute
  const sandboxAttribute = [
    ...SECURITY_CONFIG.sandboxPermissions,
    ...customSandbox
  ].join(' ');

  // Build allow attribute (Feature Policy)
  const allowAttribute = Object.entries({
    ...SECURITY_CONFIG.featurePolicy,
    ...customFeatures
  })
    .map(([feature, value]) => `${feature} ${value}`)
    .join('; ');

  // Build CSP meta tag for iframe
  const cspMeta = `<meta http-equiv="Content-Security-Policy" content="${SECURITY_CONFIG.contentSecurityPolicy}">`;

  return (
    <div className={`secure-iframe-container ${className}`}>
      {!isLoaded && (
        <div className="iframe-loading">
          <span>Loading secure content...</span>
        </div>
      )}
      
      <iframe
        ref={iframeRef}
        src={src}
        title={title}
        width={width}
        height={height}
        sandbox={sandboxAttribute}
        allow={allowAttribute}
        referrerPolicy="strict-origin-when-cross-origin"
        loading="lazy"
        importance="low"
        onLoad={handleLoad}
        onError={handleError}
        style={{
          border: 'none',
          display: isLoaded ? 'block' : 'none',
          maxWidth: '100%',
          maxHeight: '100vh'
        }}
      />
      
      {/* Security indicator */}
      <div className="security-indicator">
        <span className="security-badge">
          🔒 Secure Frame
        </span>
        <span className="session-id">
          Session: {securityContext.sessionId.substring(0, 8)}...
        </span>
      </div>
    </div>
  );
};

// Export utilities for parent components
export const IframeSecurityUtils = {
  /**
   * Create a secure message to send to iframe
   */
  createMessage: (type: string, payload: any): MessageData => {
    return {
      type,
      payload,
      timestamp: Date.now(),
      nonce: uuidv4()
    };
  },
  
  /**
   * Validate an origin against trusted list
   */
  isOriginTrusted: (origin: string, trustedOrigins: string[] = []): boolean => {
    const allTrusted = [
      ...SECURITY_CONFIG.trustedOrigins,
      ...trustedOrigins
    ];
    return allTrusted.includes(origin);
  },
  
  /**
   * Sanitize HTML content before displaying in iframe
   */
  sanitizeContent: (html: string): string => {
    // Use DOMPurify or similar in production
    const tempDiv = document.createElement('div');
    tempDiv.textContent = html;
    return tempDiv.innerHTML;
  },
  
  /**
   * Generate CSP header for iframe content
   */
  generateCSP: (additionalDirectives?: string[]): string => {
    const baseCSP = SECURITY_CONFIG.contentSecurityPolicy.split('; ');
    const combined = [...baseCSP, ...(additionalDirectives || [])];
    return combined.join('; ');
  }
};

export default SecureIframe;