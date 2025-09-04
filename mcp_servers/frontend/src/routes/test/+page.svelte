<script lang="ts">
  import { onMount } from 'svelte';
  
  let status = 'Loading...';
  let servers: any[] = [];
  let error: string | null = null;
  
  onMount(async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/servers/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      status = `Response status: ${response.status}`;
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Data received:', data);
      
      servers = data.servers || [];
      status = `Success! Found ${servers.length} servers`;
    } catch (err) {
      console.error('Error:', err);
      error = err instanceof Error ? err.message : String(err);
      status = 'Error occurred';
    }
  });
</script>

<div class="p-8">
  <h1 class="text-2xl font-bold mb-4">API Test Page</h1>
  
  <div class="mb-4">
    <p class="text-lg">Status: {status}</p>
    {#if error}
      <p class="text-red-500">Error: {error}</p>
    {/if}
  </div>
  
  {#if servers.length > 0}
    <div class="space-y-4">
      <h2 class="text-xl font-semibold">Servers:</h2>
      {#each servers as server}
        <div class="border p-4 rounded">
          <h3 class="font-bold">{server.name}</h3>
          <p>ID: {server.id}</p>
          <p>Status: {server.status}</p>
          <p>Type: {server.type}</p>
        </div>
      {/each}
    </div>
  {/if}
</div>