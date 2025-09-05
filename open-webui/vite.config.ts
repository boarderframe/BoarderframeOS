import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import path from 'path';

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
			'$lib/apis/audio': path.resolve(__dirname, './src/lib/apis/audio/index.ts'),
			'$lib/apis/auths': path.resolve(__dirname, './src/lib/apis/auths/index.ts'),
			'$lib/apis/channels': path.resolve(__dirname, './src/lib/apis/channels/index.ts'),
			'$lib/apis/chats': path.resolve(__dirname, './src/lib/apis/chats/index.ts'),
			'$lib/apis/configs': path.resolve(__dirname, './src/lib/apis/configs/index.ts'),
			'$lib/apis/evaluations': path.resolve(__dirname, './src/lib/apis/evaluations/index.ts'),
			'$lib/apis/files': path.resolve(__dirname, './src/lib/apis/files/index.ts'),
			'$lib/apis/folders': path.resolve(__dirname, './src/lib/apis/folders/index.ts'),
			'$lib/apis/functions': path.resolve(__dirname, './src/lib/apis/functions/index.ts'),
			'$lib/apis/groups': path.resolve(__dirname, './src/lib/apis/groups/index.ts'),
			'$lib/apis/images': path.resolve(__dirname, './src/lib/apis/images/index.ts'),
			'$lib/apis/knowledge': path.resolve(__dirname, './src/lib/apis/knowledge/index.ts'),
			'$lib/apis/memories': path.resolve(__dirname, './src/lib/apis/memories/index.ts'),
			'$lib/apis/models': path.resolve(__dirname, './src/lib/apis/models/index.ts'),
			'$lib/apis/notes': path.resolve(__dirname, './src/lib/apis/notes/index.ts'),
			'$lib/apis/ollama': path.resolve(__dirname, './src/lib/apis/ollama/index.ts'),
			'$lib/apis/openai': path.resolve(__dirname, './src/lib/apis/openai/index.ts'),
			'$lib/apis/prompts': path.resolve(__dirname, './src/lib/apis/prompts/index.ts'),
			'$lib/apis/retrieval': path.resolve(__dirname, './src/lib/apis/retrieval/index.ts'),
			'$lib/apis/streaming': path.resolve(__dirname, './src/lib/apis/streaming/index.ts'),
			'$lib/apis/tools': path.resolve(__dirname, './src/lib/apis/tools/index.ts'),
			'$lib/apis/users': path.resolve(__dirname, './src/lib/apis/users/index.ts'),
			'$lib/apis/utils': path.resolve(__dirname, './src/lib/apis/utils/index.ts')
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
