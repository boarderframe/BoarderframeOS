/**
 * MSW request handlers for API mocking (Vitest compatible)
 */
import { http, HttpResponse } from 'msw';

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8001';

export const handlers = [
  // Health check endpoint
  http.get(`${API_BASE_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'mcp-server-manager'
    });
  }),

  // Authentication endpoints
  http.post(`${API_BASE_URL}/api/v1/auth/login`, async ({ request }) => {
    const body = await request.json();
    const { username, password } = body;
    
    if (username === 'testuser' && password === 'password123') {
      return HttpResponse.json({
        access_token: 'mock-jwt-token',
        token_type: 'bearer',
        expires_in: 3600,
        user: {
          id: 'test-user-123',
          username: 'testuser',
          email: 'test@example.com',
          isActive: true,
          isAdmin: false
        }
      });
    }
    
    return HttpResponse.json({
      detail: 'Invalid credentials'
    }, { status: 401 });
  }),

  http.post(`${API_BASE_URL}/api/v1/auth/logout`, () => {
    return HttpResponse.json({
      message: 'Successfully logged out'
    });
  }),

  http.get(`${API_BASE_URL}/api/v1/auth/me`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (authHeader && authHeader.includes('Bearer mock-jwt-token')) {
      return HttpResponse.json({
        id: 'test-user-123',
        username: 'testuser',
        email: 'test@example.com',
        isActive: true,
        isAdmin: false,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z'
      });
    }
    
    return HttpResponse.json({
      detail: 'Not authenticated'
    }, { status: 401 });
  }),

  // MCP Server management endpoints
  http.get(`${API_BASE_URL}/api/v1/servers/`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    const url = new URL(request.url);
    const skip = parseInt(url.searchParams.get('skip') || '0');
    const limit = parseInt(url.searchParams.get('limit') || '100');
    
    const mockServers = [
      {
        id: 1,
        name: 'test-server-1',
        description: 'First test MCP server',
        host: 'localhost',
        port: 8080,
        protocol: 'stdio',
        status: 'active',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        lastHealthCheck: '2024-01-01T00:00:00Z',
        errorMessage: null
      },
      {
        id: 2,
        name: 'test-server-2',
        description: 'Second test MCP server',
        host: 'localhost',
        port: 8081,
        protocol: 'http',
        status: 'inactive',
        createdAt: '2024-01-01T01:00:00Z',
        updatedAt: '2024-01-01T01:00:00Z',
        lastHealthCheck: '2024-01-01T01:00:00Z',
        errorMessage: null
      },
      {
        id: 3,
        name: 'test-server-3',
        description: 'Third test MCP server',
        host: 'localhost',
        port: 8082,
        protocol: 'stdio',
        status: 'error',
        createdAt: '2024-01-01T02:00:00Z',
        updatedAt: '2024-01-01T02:00:00Z',
        lastHealthCheck: '2024-01-01T02:00:00Z',
        errorMessage: 'Connection failed'
      }
    ];
    
    const paginatedServers = mockServers.slice(skip, skip + limit);
    
    return HttpResponse.json(paginatedServers);
  }),

  http.post(`${API_BASE_URL}/api/v1/servers/`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    return HttpResponse.json({
      detail: 'MCP server creation not yet implemented'
    }, { status: 501 });
  }),

  http.get(`${API_BASE_URL}/api/v1/servers/:id`, ({ request, params }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    const { id } = params;
    
    if (id === '1') {
      return HttpResponse.json({
        id: 1,
        name: 'test-server-1',
        description: 'First test MCP server',
        host: 'localhost',
        port: 8080,
        protocol: 'stdio',
        command: '/usr/bin/python',
        args: ['-m', 'test_server'],
        env: { TEST_MODE: 'true' },
        config: { timeout: 30, retries: 3 },
        status: 'active',
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
        lastHealthCheck: '2024-01-01T00:00:00Z',
        errorMessage: null
      });
    }
    
    return HttpResponse.json({
      detail: 'MCP server not found'
    }, { status: 404 });
  }),

  http.put(`${API_BASE_URL}/api/v1/servers/:id`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    return HttpResponse.json({
      detail: 'MCP server update not yet implemented'
    }, { status: 501 });
  }),

  http.delete(`${API_BASE_URL}/api/v1/servers/:id`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    return HttpResponse.json({
      detail: 'MCP server deletion not yet implemented'
    }, { status: 501 });
  }),

  // MCP Inspector endpoints
  http.get(`${API_BASE_URL}/api/v1/servers/:id/health`, ({ request, params }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    const { id } = params;
    
    return HttpResponse.json({
      serverId: parseInt(id),
      status: 'active',
      responseTimeMs: 150.5,
      errorMessage: null,
      lastCheck: new Date().toISOString()
    });
  }),

  http.get(`${API_BASE_URL}/api/v1/servers/:id/tools`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    return HttpResponse.json([
      {
        name: 'file_reader',
        description: 'Read files from the filesystem',
        parameters: {
          type: 'object',
          properties: {
            path: { type: 'string' }
          }
        }
      },
      {
        name: 'web_search',
        description: 'Search the web for information',
        parameters: {
          type: 'object',
          properties: {
            query: { type: 'string' },
            limit: { type: 'integer' }
          }
        }
      }
    ]);
  }),

  http.get(`${API_BASE_URL}/api/v1/servers/:id/resources`, ({ request }) => {
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.includes('Bearer')) {
      return HttpResponse.json({
        detail: 'Not authenticated'
      }, { status: 401 });
    }
    
    return HttpResponse.json([
      {
        name: 'config.json',
        type: 'text/json',
        description: 'Server configuration file',
        uri: 'file:///etc/mcp/config.json'
      },
      {
        name: 'data.csv',
        type: 'text/csv',
        description: 'Sample data file',
        uri: 'file:///data/sample.csv'
      }
    ]);
  }),

  // Error simulation endpoints for testing
  http.get(`${API_BASE_URL}/api/v1/test/error/:code`, ({ params }) => {
    const { code } = params;
    const statusCode = parseInt(code);
    
    return HttpResponse.json({
      detail: `Test error with status ${statusCode}`
    }, { status: statusCode });
  }),

  http.get(`${API_BASE_URL}/api/v1/test/timeout`, () => {
    // Simulate a timeout by delaying the response
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(HttpResponse.json({ message: 'This should timeout' }));
      }, 10000); // 10 second delay
    });
  }),

  // Catch-all handler for unmatched requests
  http.all('*', ({ request }) => {
    console.warn(`Unhandled ${request.method} request to ${request.url}`);
    return HttpResponse.json({
      error: 'Not Found',
      message: `No handler found for ${request.method} ${request.url}`
    }, { status: 404 });
  })
];