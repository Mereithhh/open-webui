<script>
  import { config } from '$lib/stores';
  import { fade, scale } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  import { getContext } from 'svelte';
  import XMark from '../../icons/XMark.svelte';
  import Server from '../../icons/Server.svelte';
  import Modal from '../../common/Modal.svelte';
  
  const i18n = getContext('i18n');
  const dispatch = createEventDispatcher();
  
  export let show = false;
  export let selectedServers = [];
  
  let searchTerm = '';
  
  $: filteredServers = $config?.mcp_servers?.filter(server => 
    server.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (server.description && server.description.toLowerCase().includes(searchTerm.toLowerCase()))
  ) || [];
  
  function closeModal() {
    show = false;
    dispatch('close');
  }
  
  function toggleServer(serverName) {
    if (selectedServers.includes(serverName)) {
      selectedServers = selectedServers.filter(name => name !== serverName);
    } else {
      selectedServers = [...selectedServers, serverName];
    }
  }
</script>

<Modal size="md" bind:show>
  <div class="text-gray-700 dark:text-gray-100">
    <div class="flex justify-between dark:text-gray-300 px-5 pt-4 pb-1">
      <h2 class="text-lg font-medium self-center flex items-center gap-2">
        <Server className="size-5" strokeWidth={1.5} />
        <span>{$i18n.t('选择 MCP 服务器')}</span>
      </h2>
      <button 
        class="self-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
        on:click={closeModal}
      >
        <XMark />
      </button>
    </div>
    
    <!-- 搜索框 -->
    <div class="px-5 py-3 border-b border-gray-200 dark:border-gray-700">
      <input
        type="text"
        bind:value={searchTerm}
        placeholder={$i18n.t('搜索 MCP 服务器...')}
        class="w-full px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg border-none focus:ring-2 focus:ring-purple-500 dark:text-white"
      />
    </div>
    
    <!-- 服务器列表 -->
    <div class="flex-1 overflow-y-auto p-4 max-h-[50vh]">
      {#if filteredServers.length === 0}
        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
          {$i18n.t('没有找到匹配的 MCP 服务器')}
        </div>
      {:else}
        <div class="grid gap-2">
          {#each filteredServers as server (server.name)}
            <button
              class="flex items-center p-3 rounded-lg transition-colors text-left {selectedServers.includes(server.name) ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200'}"
              on:click={() => toggleServer(server.name)}
            >
              <div class="flex-1">
                <div class="font-medium">{server.name}</div>
                {#if server.description}
                  <div class="text-sm text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">{server.description}</div>
                {/if}
              </div>
              
              {#if selectedServers.includes(server.name)}
                <div class="ml-2 text-purple-600 dark:text-purple-400">
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clip-rule="evenodd" />
                  </svg>
                </div>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </div>
    
    <!-- 操作按钮 -->
    <div class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
      <button
        class="px-4 py-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        on:click={closeModal}
      >
        {$i18n.t('取消')}
      </button>
      <button
        class="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        on:click={closeModal}
      >
        {$i18n.t('确认')}
      </button>
    </div>
  </div>
</Modal> 