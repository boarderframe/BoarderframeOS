<script lang="ts">
  import { onMount } from 'svelte';
  import { serverStore } from '$lib/stores/serverStore';
  
  let storeData: any = {};
  let apiResponse: any = null;
  let apiError: string | null = null;
  
  onMount(async () => {
    // Subscribe to store
    const unsubscribe = serverStore.subscribe(value => {
      storeData = value;
    });
    
    // Fetch servers
    await serverStore.fetchServers();
    
    // Also try direct API call
    try {
      const response = await fetch('http://localhost:8001/api/v1/servers/');
      apiResponse = await response.json();
    } catch (err) {
      apiError = err instanceof Error ? err.message : String(err);
    }
    
    return unsubscribe;
  });
</script>

<div class="p-8">
  <h1 class="text-2xl font-bold mb-4">Debug Page</h1>
  
  <div class="mb-8">
    <h2 class="text-xl font-semibold mb-2">Store Data:</h2>
    <pre class="bg-gray-100 p-4 rounded overflow-auto">{JSON.stringify(storeData, null, 2)}</pre>
  </div>
  
  <div class="mb-8">
    <h2 class="text-xl font-semibold mb-2">Direct API Response:</h2>
    {#if apiError}
      <p class="text-red-500">Error: {apiError}</p>
    {:else if apiResponse}
      <pre class="bg-gray-100 p-4 rounded overflow-auto">{JSON.stringify(apiResponse, null, 2)}</pre>
    {:else}
      <p>Loading...</p>
    {/if}
  </div>
</div>