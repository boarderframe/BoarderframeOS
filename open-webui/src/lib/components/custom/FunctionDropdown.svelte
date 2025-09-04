<script lang="ts">
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import { getContext } from 'svelte';
	import Tooltip from '../common/Tooltip.svelte';
	import Sparkles from '../icons/Sparkles.svelte';
	
	// Get i18n context
	const i18n = getContext('i18n');
	
	// Get chat context if available
	const chatId = getContext('chatId');
	const messages = getContext('messages');
	
	// Component state
	let isOpen = false;
	let isExecuting = false;
	let dropdownElement: HTMLDivElement;
	let buttonElement: HTMLButtonElement;
	
	let actionConfig = {
		categories: [
			{
				id: 'conversation',
				name: 'Conversation',
				icon: '💬',
				actions: [
					{
						id: 'summarize',
						name: 'Summarize',
						icon: '📝',
						description: 'Create a summary of the conversation',
						action: 'pipeline:ui_functions:summarize_conversation',
						params: { style: 'brief' }
					},
					{
						id: 'export',
						name: 'Export',
						icon: '💾',
						description: 'Export conversation to different formats',
						action: 'pipeline:ui_functions:export_conversation',
						params: { format: 'markdown' }
					},
					{
						id: 'analyze',
						name: 'Analyze',
						icon: '📊',
						description: 'Analyze conversation metrics',
						action: 'pipeline:ui_functions:analyze_conversation',
						params: { analysis_type: 'statistics' }
					}
				]
			},
			{
				id: 'productivity',
				name: 'Productivity',
				icon: '⚡',
				actions: [
					{
						id: 'extract_tasks',
						name: 'Extract Tasks',
						icon: '✅',
						description: 'Extract action items from conversation',
						action: 'pipeline:ui_functions:extract_action_items',
						params: { format: 'list' }
					},
					{
						id: 'followup',
						name: 'Follow-up Questions',
						icon: '❓',
						description: 'Generate follow-up questions',
						action: 'pipeline:ui_functions:generate_followup_questions',
						params: { count: 3, style: 'exploratory' }
					}
				]
			},
			{
				id: 'system',
				name: 'System',
				icon: '⚙️',
				actions: [
					{
						id: 'clear',
						name: 'Clear Context',
						icon: '🔄',
						description: 'Clear conversation context',
						action: 'pipeline:ui_functions:clear_context',
						params: { keep_system_prompt: true },
						confirm: true,
						confirmMessage: 'Are you sure you want to clear the conversation context?'
					}
				]
			}
		]
	};
	
	// Load custom configuration if exists
	onMount(async () => {
		try {
			const response = await fetch('/function-config.json');
			if (response.ok) {
				const customConfig = await response.json();
				// Update to use 'actions' if the config still uses 'functions'
				if (customConfig.categories) {
					customConfig.categories = customConfig.categories.map(cat => ({
						...cat,
						actions: cat.functions || cat.actions || []
					}));
				}
				actionConfig = { ...actionConfig, ...customConfig };
			}
		} catch (error) {
			console.log('Using default action configuration');
		}
		
		// Position dropdown on mount
		positionDropdown();
	});
	
	// Position dropdown above input
	function positionDropdown() {
		if (!dropdownElement || !buttonElement) return;
		
		const rect = buttonElement.getBoundingClientRect();
		const dropdownHeight = 400; // Approximate height
		
		// Position above the button
		dropdownElement.style.bottom = `${window.innerHeight - rect.top + 10}px`;
		dropdownElement.style.left = `${rect.left}px`;
		
		// Adjust if it goes off screen
		const dropdownRect = dropdownElement.getBoundingClientRect();
		if (dropdownRect.right > window.innerWidth) {
			dropdownElement.style.left = 'auto';
			dropdownElement.style.right = '10px';
		}
	}
	
	// Execute an action
	async function executeAction(action: any) {
		if (action.confirm && !confirm(action.confirmMessage || 'Execute this action?')) {
			return;
		}
		
		isExecuting = true;
		isOpen = false;
		
		try {
			const [type, pipeline, actionName] = action.action.split(':');
			
			if (type === 'pipeline') {
				// Call pipeline function
				await executePipelineFunction(pipeline, actionName, action.params);
			} else if (type === 'message') {
				// Send as message
				await sendAsMessage(action.message || action.name);
			} else if (type === 'native') {
				// Call native WebUI function
				await executeNativeFunction(action.nativeAction, action.params);
			}
			
			toast.success(`${action.name} executed successfully`);
		} catch (error) {
			console.error('Action execution error:', error);
			toast.error(`Failed to execute ${action.name}`);
		} finally {
			isExecuting = false;
		}
	}
	
	// Execute pipeline function
	async function executePipelineFunction(pipeline: string, action: string, params: any) {
		// Get current messages from context or DOM
		const currentMessages = messages?.get() || extractMessagesFromDOM();
		
		// Method 1: Direct pipeline call (if pipeline server supports CORS)
		try {
			const response = await fetch(`http://localhost:9999/pipelines/${pipeline}/action`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${localStorage.getItem('token')}`
				},
				body: JSON.stringify({
					name: action,
					parameters: params,
					body: {
						messages: currentMessages
					}
				})
			});
			
			if (response.ok) {
				const result = await response.json();
				displayResult(result);
				return;
			}
		} catch (error) {
			console.log('Direct pipeline call failed, trying message injection');
		}
		
		// Method 2: Message injection (fallback)
		const triggerMessage = generateTriggerMessage(action, params);
		await injectMessage(triggerMessage);
	}
	
	// Send as message to chat
	async function sendAsMessage(message: string) {
		const chatInput = document.querySelector('textarea[placeholder*="Send a message"], textarea[placeholder*="Ask me anything"]') as HTMLTextAreaElement;
		if (chatInput) {
			chatInput.value = message;
			chatInput.dispatchEvent(new Event('input', { bubbles: true }));
			
			// Trigger send
			setTimeout(() => {
				const sendButton = document.querySelector('button[type="submit"]#send-message-button') as HTMLButtonElement;
				if (sendButton) {
					sendButton.click();
				} else {
					// Fallback: trigger Enter key
					const enterEvent = new KeyboardEvent('keydown', {
						key: 'Enter',
						code: 'Enter',
						bubbles: true
					});
					chatInput.dispatchEvent(enterEvent);
				}
			}, 100);
		}
	}
	
	// Execute native WebUI function
	async function executeNativeFunction(action: string, params: any) {
		// This would integrate with WebUI's native functions
		// For now, we'll send as a command
		await sendAsMessage(`/${action} ${JSON.stringify(params)}`);
	}
	
	// Extract messages from DOM (fallback)
	function extractMessagesFromDOM() {
		const messages = [];
		const messageElements = document.querySelectorAll('.message-content');
		messageElements.forEach((el, index) => {
			const role = el.classList.contains('user') ? 'user' : 'assistant';
			messages.push({
				role,
				content: el.textContent || ''
			});
		});
		return messages;
	}
	
	// Generate trigger message for function
	function generateTriggerMessage(action: string, params: any) {
		const paramString = Object.entries(params)
			.map(([key, value]) => `${key}=${value}`)
			.join(' ');
		return `Please ${action.replace(/_/g, ' ')} ${paramString}`.trim();
	}
	
	// Inject message into chat
	async function injectMessage(message: string) {
		const chatInput = document.querySelector('textarea[placeholder*="Send a message"], textarea[placeholder*="Ask me anything"]') as HTMLTextAreaElement;
		if (chatInput) {
			const originalValue = chatInput.value;
			chatInput.value = message;
			chatInput.dispatchEvent(new Event('input', { bubbles: true }));
			
			// Auto-send
			setTimeout(() => {
				const sendButton = document.querySelector('button[type="submit"]#send-message-button') as HTMLButtonElement;
				if (sendButton) sendButton.click();
			}, 100);
		}
	}
	
	// Display function result
	function displayResult(result: any) {
		if (result.result) {
			// Try to inject as assistant message
			const messagesContainer = document.querySelector('.messages-container');
			if (messagesContainer) {
				const messageDiv = document.createElement('div');
				messageDiv.className = 'message assistant';
				messageDiv.innerHTML = `
					<div class="message-content">
						<div class="action-result">
							${result.result}
						</div>
					</div>
				`;
				messagesContainer.appendChild(messageDiv);
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
		}
	}
	
	// Toggle dropdown
	function toggleDropdown() {
		isOpen = !isOpen;
		if (isOpen) {
			// Position on open
			setTimeout(() => positionDropdown(), 10);
		}
	}
	
	// Close on outside click
	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.action-dropdown-container')) {
			isOpen = false;
		}
	}
	
	// Handle window resize
	function handleResize() {
		if (isOpen) {
			positionDropdown();
		}
	}
</script>

<svelte:window on:click={handleClickOutside} on:resize={handleResize} />

<div class="action-dropdown-container">
	<Tooltip content={$i18n.t('Quick Actions')} placement="top">
		<button
			bind:this={buttonElement}
			class="px-2 @xl:px-2.5 py-2 flex gap-1.5 items-center text-sm rounded-full transition-colors duration-300 focus:outline-hidden max-w-full overflow-hidden hover:bg-gray-50 dark:hover:bg-gray-800 {isOpen
				? 'text-sky-500 dark:text-sky-300 bg-sky-50 dark:bg-sky-200/5'
				: 'bg-transparent text-gray-600 dark:text-gray-300'}"
			on:click|stopPropagation|preventDefault={toggleDropdown}
			type="button"
			disabled={isExecuting}
			aria-label={$i18n.t('Quick Actions')}
		>
			<Sparkles className="size-4" strokeWidth="1.75" />
			<span class="hidden @xl:block whitespace-nowrap overflow-hidden text-ellipsis leading-none pr-0.5">
				{$i18n.t('Actions')}
			</span>
		</button>
	</Tooltip>
	
	{#if isOpen}
		<div 
			bind:this={dropdownElement}
			class="dropdown-menu fixed z-50"
			on:click|stopPropagation
		>
			<!-- Single scrolling list with sections -->
			<div class="actions-list">
				{#each actionConfig.categories as category}
					<!-- Section header -->
					<div class="section-header">
						<span class="section-title">{category.name}</span>
					</div>
					
					<!-- Actions in this section -->
					{#each category.actions as action}
						<button
							class="action-item"
							on:click={() => executeAction(action)}
							disabled={isExecuting}
						>
							<span class="action-icon">{action.icon}</span>
							<span class="action-name">{action.name}</span>
						</button>
					{/each}
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.action-dropdown-container {
		position: relative;
		display: inline-block;
	}
	
	.dropdown-menu {
		min-width: 260px;
		max-width: 320px;
		background: rgb(255 255 255);
		border: 1px solid rgb(228 228 231);
		border-radius: 0.75rem;
		box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
		overflow: hidden;
	}
	
	:global(.dark) .dropdown-menu {
		background: rgb(39 39 42);
		border-color: rgb(63 63 70);
	}
	
	.actions-list {
		max-height: 400px;
		overflow-y: auto;
		padding: 0.5rem 0;
	}
	
	.actions-list::-webkit-scrollbar {
		width: 6px;
	}
	
	.actions-list::-webkit-scrollbar-track {
		background: transparent;
	}
	
	.actions-list::-webkit-scrollbar-thumb {
		background: rgb(212 212 216);
		border-radius: 3px;
	}
	
	:global(.dark) .actions-list::-webkit-scrollbar-thumb {
		background: rgb(82 82 91);
	}
	
	.section-header {
		padding: 0.5rem 1rem 0.25rem;
		margin-top: 0.25rem;
	}
	
	.section-header:first-child {
		margin-top: 0;
	}
	
	.section-title {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: rgb(113 113 122);
	}
	
	:global(.dark) .section-title {
		color: rgb(161 161 170);
	}
	
	.action-item {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		width: 100%;
		padding: 0.5rem 1rem;
		background: transparent;
		color: rgb(39 39 42);
		border: none;
		text-align: left;
		cursor: pointer;
		transition: background-color 0.15s ease;
		font-size: 0.875rem;
	}
	
	:global(.dark) .action-item {
		color: rgb(244 244 245);
	}
	
	.action-item:hover:not(:disabled) {
		background: rgb(244 244 245);
	}
	
	:global(.dark) .action-item:hover:not(:disabled) {
		background: rgb(63 63 70);
	}
	
	.action-item:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
	
	.action-icon {
		font-size: 1.125rem;
		flex-shrink: 0;
		width: 1.25rem;
		text-align: center;
	}
	
	.action-name {
		font-weight: 500;
		flex: 1;
	}
	
	/* Responsive */
	@media (max-width: 640px) {
		.dropdown-menu {
			min-width: 240px;
			max-width: calc(100vw - 2rem);
		}
	}
</style>