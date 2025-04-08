<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext, createEventDispatcher } from 'svelte';
	const i18n = getContext('i18n');
	const dispatch = createEventDispatcher();

	import { chatId, showArtifacts, showControls } from '$lib/stores';
	import XMark from '../icons/XMark.svelte';
	import { copyToClipboard, createMessagesList } from '$lib/utils';
	import ArrowsPointingOut from '../icons/ArrowsPointingOut.svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import SvgPanZoom from '../common/SVGPanZoom.svelte';
	import ArrowLeft from '../icons/ArrowLeft.svelte';
	import { generateImportMap } from '$lib/utils/artifacts_helper';

	export let overlay = false;
	export let history;
	let messages = [];

	let contents: Array<{ type: string; content: string }> = [];
	let selectedContentIdx = 0;

	let copied = false;
	let iframeElement: HTMLIFrameElement;

	$: if (history) {
		messages = createMessagesList(history, history.currentId);
		getContents();
	} else {
		messages = [];
		getContents();
	}

	const getContents = () => {
		contents = [];
		messages.forEach((message) => {
			if (message?.role !== 'user' && message?.content) {
				const codeBlockContents = message.content.match(/```[\s\S]*?```/g);
				let codeBlocks = [];

				if (codeBlockContents) {
					codeBlockContents.forEach((block) => {
						const lang = block.split('\n')[0].replace('```', '').trim().toLowerCase();
						const code = block.replace(/```[\s\S]*?\n/, '').replace(/```$/, '');
						codeBlocks.push({ lang, code });
					});
				}

				let htmlContent = '';
				let cssContent = '';
				let jsContent = '';
				let jsxContent = '';

				codeBlocks.forEach((block) => {
					const { lang, code } = block;

					if (lang === 'html') {
						htmlContent += code + '\n';
					} else if (lang === 'css') {
						cssContent += code + '\n';
					} else if (lang === 'javascript' || lang === 'js') {
						jsContent += code + '\n';
					} else if (lang === 'jsx') {
						jsxContent += code + '\n';
					}
				});

				const inlineHtml = message.content.match(/<html>[\s\S]*?<\/html>/gi);
				const inlineCss = message.content.match(/<style>[\s\S]*?<\/style>/gi);
				const inlineJs = message.content.match(/<script>[\s\S]*?<\/script>/gi);

				if (inlineHtml) {
					inlineHtml.forEach((block) => {
						const content = block.replace(/<\/?html>/gi, ''); // Remove <html> tags
						htmlContent += content + '\n';
					});
				}
				if (inlineCss) {
					inlineCss.forEach((block) => {
						const content = block.replace(/<\/?style>/gi, ''); // Remove <style> tags
						cssContent += content + '\n';
					});
				}
				if (inlineJs) {
					inlineJs.forEach((block) => {
						const content = block.replace(/<\/?script>/gi, ''); // Remove <script> tags
						jsContent += content + '\n';
					});
				}
				if (jsxContent) {
					// 匹配export default 后的组件名称
					const match = jsxContent.match(/export\s+(default\s+)?(\w+)/);
					const componentName = match ? match[2] : 'App'; // 如果没有匹配到组件名称，则默认为 'App'
					const appComponent = `<${componentName} />`;
					const importMap = generateImportMap(jsxContent);

					const renderContent = `
						<!DOCTYPE html>
							<html lang="en">
								<head>
									<meta charset="UTF-8">
									<meta name="viewport" content="width=device-width, initial-scale=1.0">
									<${''}style>
										body {
											background-color: white; /* Ensure the iframe has a white background */
										}
										
										/* 加载提示样式 */
										#loading-container {
											position: absolute;
											top: 50%;
											left: 50%;
											transform: translate(-50%, -50%);
											text-align: center;
											font-family: system-ui, -apple-system, sans-serif;
											color: #666;
											max-width: 80%;
										}

										#error-message {
											display: none;
											width: 100%;
											border: 2px solid #ff1212;
											background-color: #ff121203;
											padding: 8px;
											margin-top: 8px;
										}

										#error-message > pre {
											color: red;
											overflow: hidden;
											white-space: pre-wrap;
											word-wrap: break-word;
										}
										
										${cssContent}
									</${''}style>

									<${''}script src="https://cdn.tailwindcss.com"></${''}script>

									<${''}script>
										// 保存原始 fetch 方法
										const originalFetch = window.fetch;

										// 覆写 fetch 方法以捕获错误
										window.fetch = async function (...args) {
											try {
													const response = await originalFetch.apply(this, args);
													if (!response.ok) {
															if (response.url === 'https://esm.sh/transform' && response.status >= 400) {
																const msg = await response.json();
																const loadingContainer = document.getElementById('loading-message');
																if (loadingContainer) {
																	loadingContainer.style.display = 'none';
																}
																const errorContainer = document.getElementById('error-message');
																if (errorContainer) {
																	errorContainer.style.display = 'block';
																	errorContainer.innerHTML = '<pre>' + msg.message + '</pre>';
																}
															}
													}
													return response;
											} catch (error) {
													console.error('Fetch error captured:', error);
													throw error; // 继续抛出错误
											}
										};
									</${''}script>

									<${''}script type="importmap">
										${JSON.stringify(importMap)}
									</${''}script>
									<${''}script type="module" src="https://esm.sh/tsx"></${''}script>
								</head>
								<body>
									<div id="root">
										<div id="loading-container">
											<div id="loading-message">
												<p>正在加载依赖库和编译代码，这可能需要一些时间...</p>
												<p style="font-size: 0.9em; margin-top: 8px;">如果加载时间过长，可能是程序有 bug 或不通外网没加载出来依赖。</p>
												<p style="font-size: 0.9em; margin-top: 8px;">可以前往 playground 进一步调试：<a class="text-blue-500" href="https://artifacts-preview.ai-native.glm.ai/playground?type=react" target="_blank">https://artifacts-preview.ai-native.glm.ai/playground?type=react</a></p>
											</div>
											<div id="error-message"></div>
										</div>
									</div>
									${htmlContent}

									<${''}script>
										${jsContent}
									</${''}script>

									<${''}script type="text/babel">
										import { createRoot } from 'react-dom/client';
										import { ErrorBoundary } from 'react-error-boundary';

										function fallbackRender({ error, resetErrorBoundary }) {
											return (
												<div role="alert">
													<p>Something went wrong:</p>
													<pre style={{ color: "red" }}>{error.message}</pre>
												</div>
											);
										}

										${jsxContent}
										const rootElement = document.getElementById('root');
										createRoot(rootElement).render(
											<ErrorBoundary fallbackRender={fallbackRender}>
												${appComponent}
											</ErrorBoundary>
										);
									</${''}script>
								</body>
							</html>
					`;
					console.log(renderContent);
					contents = [...contents, { type: 'iframe', content: renderContent }];
				} else if (htmlContent || cssContent || jsContent) {
					const renderedContent = `
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
							<${''}style>
								body {
									background-color: white; /* Ensure the iframe has a white background */
								}

								${cssContent}
							</${''}style>
                        </head>
                        <body>
                            ${htmlContent}

							<${''}script>
                            	${jsContent}
							</${''}script>
                        </body>
                        </html>
                    `;
					contents = [...contents, { type: 'iframe', content: renderedContent }];
				} else {
					// Check for SVG content
					for (const block of codeBlocks) {
						if (block.lang === 'svg' || (block.lang === 'xml' && block.code.includes('<svg'))) {
							contents = [...contents, { type: 'svg', content: block.code }];
						}
					}
				}
			}
		});

		// 通过功能块开启，没有咱们也不关闭好吧。
		// if (contents.length === 0) {
		// 	showControls.set(false);
		// 	showArtifacts.set(false);
		// }

		selectedContentIdx = contents ? contents.length - 1 : 0;
	};

	function navigateContent(direction: 'prev' | 'next') {
		console.log(selectedContentIdx);

		selectedContentIdx =
			direction === 'prev'
				? Math.max(selectedContentIdx - 1, 0)
				: Math.min(selectedContentIdx + 1, contents.length - 1);

		console.log(selectedContentIdx);
	}

	const iframeLoadHandler = (e) => {
		iframeElement.contentWindow.addEventListener(
			'error',
			function (event) {
				console.error('inner error:', event);
			},
			true
		);
		iframeElement.contentWindow.addEventListener(
			'unhandledrejection',
			function (event) {
				console.error('inner unhandledrejection:', event);
			},
			true
		);

		iframeElement.contentWindow.addEventListener(
			'click',
			function (e) {
				const target = e.target.closest('a');
				if (target && target.href) {
					e.preventDefault();
					const url = new URL(target.href, iframeElement.baseURI);
					if (url.origin === window.location.origin) {
						iframeElement.contentWindow.history.pushState(
							null,
							'',
							url.pathname + url.search + url.hash
						);
					} else {
						window.open(url.href, '_blank');
						// console.log('External navigation blocked:', url.href);
					}
				}
			},
			true
		);

		// Cancel drag when hovering over iframe
		iframeElement.contentWindow.addEventListener('mouseenter', function (e) {
			e.preventDefault();
			iframeElement.contentWindow.addEventListener('dragstart', (event) => {
				event.preventDefault();
			});
		});
	};

	const showFullScreen = () => {
		if (iframeElement.requestFullscreen) {
			iframeElement.requestFullscreen();
		} else if (iframeElement.webkitRequestFullscreen) {
			iframeElement.webkitRequestFullscreen();
		} else if (iframeElement.msRequestFullscreen) {
			iframeElement.msRequestFullscreen();
		}
	};

	onMount(() => {});
</script>

<div class=" w-full h-full relative flex flex-col bg-gray-50 dark:bg-gray-850">
	<div class="w-full h-full flex-1 relative">
		{#if overlay}
			<div class=" absolute top-0 left-0 right-0 bottom-0 z-10"></div>
		{/if}

		<div class="absolute pointer-events-none z-50 w-full flex items-center justify-start p-4">
			{$i18n.t('PreviewMode')}
		</div>

		<div class=" absolute pointer-events-none z-50 w-full flex items-center justify-end p-4">
			<button
				class="self-center pointer-events-auto p-1 rounded-full bg-white dark:bg-gray-850"
				on:click={() => {
					dispatch('close');
					showControls.set(false);
					showArtifacts.set(false);
				}}
			>
				<XMark className="size-3.5 text-gray-900 dark:text-white" />
			</button>
		</div>

		<div class="flex-1 w-full h-full">
			<div class=" h-full flex flex-col">
				{#if contents.length > 0}
					<div class="max-w-full w-full h-full">
						{#if contents[selectedContentIdx].type === 'iframe'}
							<iframe
								bind:this={iframeElement}
								title="Content"
								srcdoc={contents[selectedContentIdx].content}
								class="w-full border-0 h-full rounded-none"
								sandbox="allow-scripts allow-forms allow-same-origin"
								on:load={iframeLoadHandler}
							></iframe>
						{:else if contents[selectedContentIdx].type === 'svg'}
							<SvgPanZoom
								className=" w-full h-full max-h-full overflow-hidden"
								svg={contents[selectedContentIdx].content}
							/>
						{/if}
					</div>
				{:else}
					<div class="m-auto font-medium text-xs text-gray-900 dark:text-white">
						{$i18n.t('No HTML, CSS, or JavaScript content found.')}
					</div>
				{/if}
			</div>
		</div>
	</div>

	{#if contents.length > 0}
		<div class="flex justify-between items-center p-2.5 font-primar text-gray-900 dark:text-white">
			<div class="flex items-center space-x-2">
				<div class="flex items-center gap-0.5 self-center min-w-fit" dir="ltr">
					<button
						class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
						on:click={() => navigateContent('prev')}
						disabled={contents.length <= 1}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
							class="size-3.5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M15.75 19.5 8.25 12l7.5-7.5"
							/>
						</svg>
					</button>

					<div class="text-xs self-center dark:text-gray-100 min-w-fit">
						{$i18n.t('Version {{selectedVersion}} of {{totalVersions}}', {
							selectedVersion: selectedContentIdx + 1,
							totalVersions: contents.length
						})}
					</div>

					<button
						class="self-center p-1 hover:bg-black/5 dark:hover:bg-white/5 dark:hover:text-white hover:text-black rounded-md transition disabled:cursor-not-allowed"
						on:click={() => navigateContent('next')}
						disabled={contents.length <= 1}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
							class="size-3.5"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
						</svg>
					</button>
				</div>
			</div>

			<div class="flex items-center gap-1">
				<button
					class="copy-code-button bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md px-1.5 py-0.5"
					on:click={() => {
						copyToClipboard(contents[selectedContentIdx].content);
						copied = true;

						setTimeout(() => {
							copied = false;
						}, 2000);
					}}>{copied ? $i18n.t('Copied') : $i18n.t('Copy')}</button
				>

				{#if contents[selectedContentIdx].type === 'iframe'}
					<Tooltip content={$i18n.t('Open in full screen')}>
						<button
							class=" bg-none border-none text-xs bg-gray-50 hover:bg-gray-100 dark:bg-gray-850 dark:hover:bg-gray-800 transition rounded-md p-0.5"
							on:click={showFullScreen}
						>
							<ArrowsPointingOut className="size-3.5" />
						</button>
					</Tooltip>
				{/if}
			</div>
		</div>
	{/if}
</div>
