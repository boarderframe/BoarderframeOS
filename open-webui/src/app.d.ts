// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
	
	// Global constants defined in Vite config
	const APP_VERSION: string;
	const APP_BUILD_HASH: string;
}

export {};