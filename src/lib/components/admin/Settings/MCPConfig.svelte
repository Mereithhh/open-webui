<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { user } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import { getMCPConfig, updateMCPConfig } from '$lib/apis';
	import SpinnerIcon from '$lib/components/common/Spinner.svelte';
	
	const i18n = getContext('i18n');
	
	export let saveHandler = () => {};
	
	let mcpConfig = '';
	let isLoading = true;
	let isSaving = false;
	let error = null;
	
	onMount(async () => {
		await loadConfig();
	});
	
	async function loadConfig() {
		isLoading = true;
		error = null;
		
		try {
			const data = await getMCPConfig(localStorage.token);
			mcpConfig = data.yaml;
		} catch (err) {
			error = err;
			toast.error($i18n.t('Failed to load MCP configuration'));
			console.error('Error loading MCP config:', err);
		} finally {
			isLoading = false;
		}
	}
	
	async function saveConfig() {
		isSaving = true;
		error = null;
		
		try {
			await updateMCPConfig(localStorage.token, mcpConfig);
			// toast.success($i18n.t('MCP configuration updated successfully'));
			toast.info($i18n.t('Please refresh your browser for changes to take effect'));
			saveHandler();
			
			// 添加延迟后刷新页面
			setTimeout(() => {
				window.location.reload();
			}, 2000);
		} catch (err) {
			error = err;
			toast.error($i18n.t('Failed to update MCP configuration'));
			console.error('Error updating MCP config:', err);
		} finally {
			isSaving = false;
		}
	}
</script>

<div class="flex flex-col h-full overflow-hidden gap-2">
	<div class="font-semibold text-lg dark:text-white">
		{$i18n.t('MCP Server Configuration')}
	</div>
	
	<div class="text-sm text-gray-500 dark:text-gray-400 mb-4">
		{$i18n.t('Edit the MCP server configuration YAML directly. Be careful as incorrect configuration may break functionality.')}
	</div>
	
	{#if isLoading}
		<div class="flex justify-center items-center h-64">
			<SpinnerIcon />
		</div>
	{:else}
		<div class="flex-1 overflow-hidden flex flex-col">
			<textarea
				class="flex-1 font-mono text-sm p-4 rounded-lg border dark:border-gray-700 bg-gray-50 dark:bg-gray-800 resize-none h-80 focus:outline-none focus:border-gray-700 dark:focus:border-gray-700"
				bind:value={mcpConfig}
				spellcheck="false"
			></textarea>
			
			{#if error}
				<div class="text-red-500 mt-2 text-sm">
					{error.message || $i18n.t('An error occurred')}
				</div>
			{/if}
			
			<div class="flex justify-end mt-4 gap-2">
				<button
					class="text-xs px-3 py-1.5 bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-lg font-medium"
					type="button"
					on:click={loadConfig}
					disabled={isLoading || isSaving}
				>
					{$i18n.t('Reload')}
				</button>
				
				<button
					class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
					type="button"
					on:click={saveConfig}
					disabled={isLoading || isSaving}
				>
					{#if isSaving}
						<SpinnerIcon />
					{:else}
						{$i18n.t('Save Configuration')}
					{/if}
				</button>
			</div>
		</div>
	{/if}
</div> 