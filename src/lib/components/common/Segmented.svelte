<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	const dispatch = createEventDispatcher();
	// 定义组件属性
	export let value: string;
	export let options: Array<{ label: string; value: string }>;
	export let size: 'small' | 'normal' | 'large' = 'normal';

	// 处理选项点击事件
	function handleClick(selectedValue: string) {
		value = selectedValue;
		dispatch('change', selectedValue);
	}
</script>

<div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 gap-1">
	{#each options as option}
		<button
			class="flex-1 rounded transition-all duration-200 cursor-pointer {size === 'small'
				? 'px-1 py-0.5 text-xs'
				: size === 'large'
					? 'px-5 py-3 text-base'
					: 'px-4 py-2 text-sm'} {value === option.value
				? 'bg-white dark:bg-gray-700 shadow-sm'
				: 'bg-transparent hover:bg-black/5 dark:hover:bg-white/5'}"
			on:click={() => handleClick(option.value)}
		>
			{option.label}
		</button>
	{/each}
</div>
