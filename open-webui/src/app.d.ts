// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces

// Global declarations for build environment variables
declare const APP_VERSION: string;
declare const APP_BUILD_HASH: string;

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface Platform {}
	}
}

export {};
