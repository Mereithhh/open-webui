<script lang="ts">
	export let primary = false;
	export let size = 'md';
	export let disabled = false;
	export let loading = false;
	export let fullWidth = false;
	export let type = 'button';
	
	const sizeClasses = {
		sm: 'px-2.5 py-1.5 text-xs',
		md: 'px-4 py-2 text-sm',
		lg: 'px-6 py-3 text-base'
	};
	
	$: buttonClasses = `
		inline-flex items-center justify-center font-medium rounded-lg shadow-sm transition-colors
		${sizeClasses[size]}
		${fullWidth ? 'w-full' : ''}
		${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
		${primary 
			? 'bg-primary-600 text-white hover:bg-primary-700 dark:bg-primary-700 dark:hover:bg-primary-800' 
			: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-100 dark:border-gray-600 dark:hover:bg-gray-800'}
	`;
</script>

<button 
	on:click 
	{type} 
	class={buttonClasses}
	{disabled}
	{...$$restProps}
>
	{#if loading}
		<span class="animate-spin mr-2">
			<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
			</svg>
		</span>
	{/if}
	<slot></slot>
</button> 