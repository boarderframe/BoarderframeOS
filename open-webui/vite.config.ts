import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
	plugins: [
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/onnxruntime-web/dist/*.jsep.*',

					dest: 'wasm'
				}
			]
		})
	],
	resolve: {
		extensions: ['.js', '.ts', '.svelte', '.json'],
		alias: {
			// Ensure directory imports resolve to index.ts files for all API modules
			'$lib/apis/audio': new URL('./src/lib/apis/audio/index.ts', import.meta.url).pathname,
			'$lib/apis/auths': new URL('./src/lib/apis/auths/index.ts', import.meta.url).pathname,
			'$lib/apis/channels': new URL('./src/lib/apis/channels/index.ts', import.meta.url).pathname,
			'$lib/apis/chats': new URL('./src/lib/apis/chats/index.ts', import.meta.url).pathname,
			'$lib/apis/configs': new URL('./src/lib/apis/configs/index.ts', import.meta.url).pathname,
			'$lib/apis/evaluations': new URL('./src/lib/apis/evaluations/index.ts', import.meta.url).pathname,
			'$lib/apis/files': new URL('./src/lib/apis/files/index.ts', import.meta.url).pathname,
			'$lib/apis/folders': new URL('./src/lib/apis/folders/index.ts', import.meta.url).pathname,
			'$lib/apis/functions': new URL('./src/lib/apis/functions/index.ts', import.meta.url).pathname,
			'$lib/apis/groups': new URL('./src/lib/apis/groups/index.ts', import.meta.url).pathname,
			'$lib/apis/images': new URL('./src/lib/apis/images/index.ts', import.meta.url).pathname,
			'$lib/apis/knowledge': new URL('./src/lib/apis/knowledge/index.ts', import.meta.url).pathname,
			'$lib/apis/memories': new URL('./src/lib/apis/memories/index.ts', import.meta.url).pathname,
			'$lib/apis/models': new URL('./src/lib/apis/models/index.ts', import.meta.url).pathname,
			'$lib/apis/notes': new URL('./src/lib/apis/notes/index.ts', import.meta.url).pathname,
			'$lib/apis/ollama': new URL('./src/lib/apis/ollama/index.ts', import.meta.url).pathname,
			'$lib/apis/openai': new URL('./src/lib/apis/openai/index.ts', import.meta.url).pathname,
			'$lib/apis/prompts': new URL('./src/lib/apis/prompts/index.ts', import.meta.url).pathname,
			'$lib/apis/retrieval': new URL('./src/lib/apis/retrieval/index.ts', import.meta.url).pathname,
			'$lib/apis/streaming': new URL('./src/lib/apis/streaming/index.ts', import.meta.url).pathname,
			'$lib/apis/tools': new URL('./src/lib/apis/tools/index.ts', import.meta.url).pathname,
			'$lib/apis/users': new URL('./src/lib/apis/users/index.ts', import.meta.url).pathname,
			'$lib/apis/utils': new URL('./src/lib/apis/utils/index.ts', import.meta.url).pathname
		}
	},
	define: {
		APP_VERSION: JSON.stringify(process.env.npm_package_version || '0.1.0'),
		APP_BUILD_HASH: JSON.stringify(process.env.APP_BUILD_HASH || 'dev-build')
	},
	build: {
		sourcemap: true,
		rollupOptions: {
			output: {
				manualChunks: undefined
			},
			external: (id) => {
				// Don't externalize local modules
				return false;
			},
			onwarn: (warning, warn) => {
				// Suppress circular dependency warnings for common patterns
				if (warning.code === 'CIRCULAR_DEPENDENCY') {
					return;
				}
				// Suppress eval warnings for development builds
				if (warning.code === 'EVAL' && process.env.NODE_ENV !== 'production') {
					return;
				}
				warn(warning);
			}
		},
		// Ensure TypeScript resolution works properly
		target: 'es2020',
		minify: 'esbuild'
	},
	worker: {
		format: 'es'
	},
	esbuild: {
		pure: process.env.ENV === 'dev' ? [] : ['console.log', 'console.debug']
	},
	server: {
		proxy: {
			'/static': {
				target: 'http://localhost:8080',
				changeOrigin: true
			},
			'/api': {
				target: 'http://localhost:8080',
				changeOrigin: true
			},
			'/ollama': {
				target: 'http://localhost:8080',
				changeOrigin: true
			},
			'/openai': {
				target: 'http://localhost:8080',
				changeOrigin: true
			}
		}
	}
});
