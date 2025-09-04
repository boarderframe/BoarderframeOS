#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';
import { glob } from 'glob';
import mime from 'mime-types';

// Home directory with full access
const HOME_DIR = '/Users/cosburn';

class FileSystemServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'filesystem-server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.getTools(),
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (!args) {
        throw new Error('No arguments provided');
      }

      try {
        switch (name) {
          case 'read_file':
            return await this.readFile(args.path as string);
          
          case 'write_file':
            return await this.writeFile(args.path as string, args.content as string);
          
          case 'list_directory':
            return await this.listDirectory(args.path as string | undefined);
          
          case 'create_directory':
            return await this.createDirectory(args.path as string);
          
          case 'delete_file':
            return await this.deleteFile(args.path as string);
          
          case 'move_file':
            return await this.moveFile(args.source as string, args.destination as string);
          
          case 'copy_file':
            return await this.copyFile(args.source as string, args.destination as string);
          
          case 'search_files':
            return await this.searchFiles(args.pattern as string, args.path as string);
          
          case 'get_file_info':
            return await this.getFileInfo(args.path as string);
          
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  private getTools(): Tool[] {
    return [
      {
        name: 'read_file',
        description: 'Read the contents of a file',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path to the file (absolute or relative to home directory)',
            },
          },
          required: ['path'],
        },
      },
      {
        name: 'write_file',
        description: 'Write content to a file',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path to the file',
            },
            content: {
              type: 'string',
              description: 'Content to write',
            },
          },
          required: ['path', 'content'],
        },
      },
      {
        name: 'list_directory',
        description: 'List contents of a directory (defaults to /Users/cosburn)',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path to the directory (optional, defaults to /Users/cosburn)',
              default: '',
            },
          },
          required: [],
        },
      },
      {
        name: 'create_directory',
        description: 'Create a new directory',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path for the new directory',
            },
          },
          required: ['path'],
        },
      },
      {
        name: 'delete_file',
        description: 'Delete a file or empty directory',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path to the file or directory to delete',
            },
          },
          required: ['path'],
        },
      },
      {
        name: 'move_file',
        description: 'Move or rename a file or directory',
        inputSchema: {
          type: 'object',
          properties: {
            source: {
              type: 'string',
              description: 'Source path',
            },
            destination: {
              type: 'string',
              description: 'Destination path',
            },
          },
          required: ['source', 'destination'],
        },
      },
      {
        name: 'copy_file',
        description: 'Copy a file or directory',
        inputSchema: {
          type: 'object',
          properties: {
            source: {
              type: 'string',
              description: 'Source path',
            },
            destination: {
              type: 'string',
              description: 'Destination path',
            },
          },
          required: ['source', 'destination'],
        },
      },
      {
        name: 'search_files',
        description: 'Search for files using glob patterns',
        inputSchema: {
          type: 'object',
          properties: {
            pattern: {
              type: 'string',
              description: 'Glob pattern to search for',
            },
            path: {
              type: 'string',
              description: 'Base path to search from (defaults to home)',
            },
          },
          required: ['pattern'],
        },
      },
      {
        name: 'get_file_info',
        description: 'Get detailed information about a file',
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: 'Path to the file',
            },
          },
          required: ['path'],
        },
      },
    ];
  }

  private resolvePath(filePath?: string): string {
    // Default to HOME_DIR if no path provided
    if (!filePath || filePath === '') {
      return HOME_DIR;
    }
    // If path is absolute, use it; otherwise, resolve relative to home
    if (path.isAbsolute(filePath)) {
      return filePath;
    }
    return path.join(HOME_DIR, filePath);
  }

  private async readFile(filePath: string) {
    const resolvedPath = this.resolvePath(filePath);
    const content = await fs.readFile(resolvedPath, 'utf-8');
    const mimeType = mime.lookup(resolvedPath) || 'text/plain';
    
    return {
      content: [
        {
          type: 'text',
          text: content,
          mimeType,
        },
      ],
    };
  }

  private async writeFile(filePath: string, content: string) {
    const resolvedPath = this.resolvePath(filePath);
    await fs.mkdir(path.dirname(resolvedPath), { recursive: true });
    await fs.writeFile(resolvedPath, content, 'utf-8');
    
    return {
      content: [
        {
          type: 'text',
          text: `File written successfully: ${resolvedPath}`,
        },
      ],
    };
  }

  private async listDirectory(dirPath?: string) {
    const resolvedPath = this.resolvePath(dirPath);
    const entries = await fs.readdir(resolvedPath, { withFileTypes: true });
    
    const items = await Promise.all(
      entries.map(async (entry) => {
        const fullPath = path.join(resolvedPath, entry.name);
        const stats = await fs.stat(fullPath);
        
        return {
          name: entry.name,
          type: entry.isDirectory() ? 'directory' : 'file',
          size: stats.size,
          modified: stats.mtime.toISOString(),
        };
      })
    );
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(items, null, 2),
        },
      ],
    };
  }

  private async createDirectory(dirPath: string) {
    const resolvedPath = this.resolvePath(dirPath);
    await fs.mkdir(resolvedPath, { recursive: true });
    
    return {
      content: [
        {
          type: 'text',
          text: `Directory created: ${resolvedPath}`,
        },
      ],
    };
  }

  private async deleteFile(filePath: string) {
    const resolvedPath = this.resolvePath(filePath);
    const stats = await fs.stat(resolvedPath);
    
    if (stats.isDirectory()) {
      await fs.rmdir(resolvedPath);
    } else {
      await fs.unlink(resolvedPath);
    }
    
    return {
      content: [
        {
          type: 'text',
          text: `Deleted: ${resolvedPath}`,
        },
      ],
    };
  }

  private async moveFile(source: string, destination: string) {
    const sourcePath = this.resolvePath(source);
    const destPath = this.resolvePath(destination);
    
    await fs.mkdir(path.dirname(destPath), { recursive: true });
    await fs.rename(sourcePath, destPath);
    
    return {
      content: [
        {
          type: 'text',
          text: `Moved from ${sourcePath} to ${destPath}`,
        },
      ],
    };
  }

  private async copyFile(source: string, destination: string) {
    const sourcePath = this.resolvePath(source);
    const destPath = this.resolvePath(destination);
    
    await fs.mkdir(path.dirname(destPath), { recursive: true });
    await fs.copyFile(sourcePath, destPath);
    
    return {
      content: [
        {
          type: 'text',
          text: `Copied from ${sourcePath} to ${destPath}`,
        },
      ],
    };
  }

  private async searchFiles(pattern: string, basePath?: string) {
    const searchPath = basePath ? this.resolvePath(basePath) : HOME_DIR;
    const files = await glob(pattern, {
      cwd: searchPath,
      absolute: true,
      ignore: ['**/node_modules/**', '**/.git/**'],
    });
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(files, null, 2),
        },
      ],
    };
  }

  private async getFileInfo(filePath: string) {
    const resolvedPath = this.resolvePath(filePath);
    const stats = await fs.stat(resolvedPath);
    const mimeType = mime.lookup(resolvedPath) || 'unknown';
    
    const info = {
      path: resolvedPath,
      size: stats.size,
      isDirectory: stats.isDirectory(),
      isFile: stats.isFile(),
      mimeType,
      created: stats.birthtime.toISOString(),
      modified: stats.mtime.toISOString(),
      accessed: stats.atime.toISOString(),
      permissions: stats.mode.toString(8),
    };
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(info, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Filesystem MCP server running with access to:', HOME_DIR);
  }
}

const server = new FileSystemServer();
server.run().catch(console.error);