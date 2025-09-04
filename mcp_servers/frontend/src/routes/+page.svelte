<script lang="ts">
  import { onMount } from 'svelte';
  import ExternalServerCard from '$lib/components/ExternalServerCard.svelte';
  import ConnectionStatus from '$lib/components/ConnectionStatus.svelte';
  import KrogerServerDetails from '$lib/components/KrogerServerDetails.svelte';
  import { ExternalLink } from 'lucide-svelte';
  
  let showKrogerDetails = false;

  // Open WebUI compatible MCP servers
  const externalServers = [
    {
      id: 'filesystem-tools',
      name: 'Simple Filesystem Tools',
      description: 'Basic file operations: read, write, list directories, and search files with built-in security restrictions',
      port: 9001,
      status: 'running' as const,
      tools: ['list_directory', 'read_file', 'write_file', 'search_files'],
      openapi_url: 'http://localhost:9001/openapi.json',
      docs_url: 'http://localhost:9001/docs',
      integration_url: 'http://localhost:9001',
      features: ['Basic File Access', 'Simple Operations', 'LLM Compatible', 'Lightweight']
    },
    {
      id: 'playwright-web-tools',
      name: 'Playwright Web Tools',
      description: 'Advanced web automation with real browser capabilities: navigation, search, extraction, interaction, and enhanced news search',
      port: 9002,
      status: 'running' as const,
      tools: ['navigate', 'extract_text', 'click', 'fill', 'screenshot', 'search_news'],
      openapi_url: 'http://localhost:9002/openapi.json',
      docs_url: 'http://localhost:9002/docs',
      integration_url: 'http://localhost:9002',
      features: ['Real Browser Automation', 'Enhanced News Search', 'LLM Compatible', 'No Enum Issues']
    },
    {
      id: 'advanced-filesystem-tools',
      name: 'Advanced Filesystem Tools',
      description: 'Comprehensive file operations with enhanced features: line-based reading, content search, file operations, metadata access, and advanced directory management',
      port: 9003,
      status: 'running' as const,
      tools: ['list_directory', 'read_file', 'read_file_lines', 'write_file', 'move_file', 'copy_file', 'delete_file', 'search_files', 'create_directory', 'get_file_info'],
      openapi_url: 'http://localhost:9003/openapi.json',
      docs_url: 'http://localhost:9003/docs',
      integration_url: 'http://localhost:9003',
      features: ['Enhanced Directory Listings', 'Line-based Reading', 'Content Search', 'File Operations', 'Metadata Access']
    },
    {
      id: 'kroger-api-tools',
      name: 'Kroger API Tools',
      description: 'Complete Kroger grocery platform integration: OAuth2 authentication, product search, cart management, store locations, and order fulfillment with real-time inventory',
      port: 9004,
      status: 'running' as const,
      tools: ['authenticate', 'search_products', 'get_product_details', 'add_to_cart', 'view_cart', 'checkout', 'find_stores', 'check_inventory', 'get_promotions', 'manage_lists'],
      openapi_url: 'http://localhost:9004/openapi.json',
      docs_url: 'http://localhost:9004/docs',
      integration_url: 'http://localhost:9004',
      features: ['OAuth2 Authentication', 'Product Search & Details', 'Shopping Cart Management', 'Store Locator', 'Real-time Inventory', 'Digital Coupons', 'Order Fulfillment', 'Shopping Lists']
    }
  ];

  // Check external server status
  const checkExternalServerStatus = async (server: typeof externalServers[0]) => {
    try {
      const response = await fetch(`http://localhost:${server.port}/health`);
      return response.ok ? 'running' : 'stopped';
    } catch {
      return 'stopped';
    }
  };

  // Update external server statuses
  const updateExternalStatuses = async () => {
    for (const server of externalServers) {
      server.status = await checkExternalServerStatus(server);
    }
  };

  onMount(() => {
    // Update external server statuses
    updateExternalStatuses();
  });
</script>

<div class="space-y-6">
  <!-- Open WebUI Tool Servers Section -->
  <div class="space-y-4">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-900">Open WebUI Tool Servers</h2>
      <button
        on:click={updateExternalStatuses}
        class="flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
      >
        <ExternalLink class="w-4 h-4" />
        <span>Refresh Status</span>
      </button>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {#each externalServers as server (server.id)}
        <ExternalServerCard 
          {server} 
          on:showDetails={() => {
            if (server.id === 'kroger-api-tools') {
              showKrogerDetails = true;
            }
          }}
        />
      {/each}
    </div>

    <!-- Integration Instructions -->
    <div class="bg-gradient-to-r from-blue-50 to-green-50 border border-blue-200 rounded-lg p-6">
      <h3 class="font-semibold text-blue-900 mb-3">🚀 Open WebUI Integration Ready</h3>
      
      <!-- Quick Setup Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <!-- Playwright Setup -->
        <div class="bg-white rounded-lg p-4 border border-blue-100">
          <h4 class="font-medium text-blue-800 mb-2">🌐 Web Automation Setup</h4>
          <div class="bg-gray-100 p-2 rounded font-mono text-sm mb-2">
            <code class="text-blue-800">http://localhost:9002</code>
          </div>
          <ul class="text-blue-700 text-xs space-y-1">
            <li>• Browser automation & search</li>
            <li>• News extraction & analysis</li>
            <li>• Form interaction & screenshots</li>
          </ul>
        </div>
        
        <!-- Kroger Setup -->
        <div class="bg-white rounded-lg p-4 border border-green-100">
          <h4 class="font-medium text-green-800 mb-2">🛒 Kroger API Setup</h4>
          <div class="bg-gray-100 p-2 rounded font-mono text-sm mb-2">
            <code class="text-green-800">http://localhost:9004</code>
          </div>
          <ul class="text-green-700 text-xs space-y-1">
            <li>• OAuth2 authentication required</li>
            <li>• Product search & inventory</li>
            <li>• Cart management & checkout</li>
          </ul>
        </div>
      </div>
      
      <!-- Features Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <h4 class="font-medium text-blue-800 mb-2">📁 File Operations</h4>
          <ul class="text-blue-700 text-sm space-y-1">
            <li>• Basic & advanced file access</li>
            <li>• Directory management</li>
            <li>• Content search & metadata</li>
          </ul>
        </div>
        <div>
          <h4 class="font-medium text-blue-800 mb-2">🌐 Web Tools</h4>
          <ul class="text-blue-700 text-sm space-y-1">
            <li>• Real browser automation</li>
            <li>• Enhanced news search</li>
            <li>• Screenshots & extraction</li>
          </ul>
        </div>
        <div>
          <h4 class="font-medium text-green-800 mb-2">🛒 Grocery Services</h4>
          <ul class="text-green-700 text-sm space-y-1">
            <li>• Product search & details</li>
            <li>• Shopping cart & lists</li>
            <li>• Store locator & inventory</li>
          </ul>
        </div>
      </div>
      
      <!-- Status -->
      <div class="mt-4 bg-green-100 border border-green-200 rounded p-3">
        <p class="text-green-800 text-sm">
          ✅ <strong>Status:</strong> All servers compatible with Gemini, GPT, Claude, and major LLM providers
        </p>
      </div>
      
      <!-- Kroger OAuth Notice -->
      <div class="mt-3 bg-yellow-50 border border-yellow-200 rounded p-3">
        <p class="text-yellow-800 text-sm">
          🔑 <strong>Note:</strong> Kroger API requires OAuth2 credentials. Set KROGER_CLIENT_ID and KROGER_CLIENT_SECRET environment variables before use.
        </p>
      </div>
    </div>
  </div>
</div>

<!-- Connection Status -->
<ConnectionStatus />

<!-- Kroger Server Details Modal -->
<KrogerServerDetails bind:isOpen={showKrogerDetails} />

<!-- Notification Toasts -->
<!-- <NotificationToast /> -->