<script lang="ts">
  import '../styles/index.css';
  import { Activity, Terminal, Settings } from 'lucide-svelte';
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <header class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <div class="flex items-center gap-3">
          <Activity class="w-8 h-8 text-primary-500" />
          <h1 class="text-xl font-bold text-gray-900">
            MCP Server Manager
          </h1>
        </div>
        <nav class="flex items-center gap-4">
          <button
            class="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="View logs"
          >
            <Terminal class="w-5 h-5" />
            <span class="hidden sm:inline">Logs</span>
          </button>
          <button
            class="flex items-center gap-2 px-3 py-2 text-gray-600 hover:text-gray-900 transition-colors"
            aria-label="Settings"
          >
            <Settings class="w-5 h-5" />
            <span class="hidden sm:inline">Settings</span>
          </button>
        </nav>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <slot />
  </main>
</div>