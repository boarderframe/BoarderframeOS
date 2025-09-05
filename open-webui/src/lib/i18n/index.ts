import i18next from 'i18next';
import resourcesToBackend from 'i18next-resources-to-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import type { i18n as i18nType } from 'i18next';
import { writable } from 'svelte/store';

const createI18nStore = (i18n: i18nType) => {
	const i18nWritable = writable(i18n);

	// Create a custom store that wraps the i18next instance
	const { subscribe, set } = i18nWritable;

	// Update the store when i18next events occur
	i18n.on('initialized', () => {
		set(i18n);
	});
	i18n.on('loaded', () => {
		set(i18n);
	});
	i18n.on('added', () => set(i18n));
	i18n.on('languageChanged', () => {
		set(i18n);
	});

	// Return a store object that includes all i18next methods
	return {
		subscribe,
		// Expose i18next methods directly on the store
		t: i18n.t.bind(i18n),
		changeLanguage: i18n.changeLanguage.bind(i18n),
		getLanguage: () => i18n.language,
		// Add other commonly used i18next methods as needed
		exists: i18n.exists.bind(i18n),
		getResource: i18n.getResource.bind(i18n),
		addResource: i18n.addResource.bind(i18n),
		addResources: i18n.addResources.bind(i18n),
		addResourceBundle: i18n.addResourceBundle.bind(i18n),
		hasResourceBundle: i18n.hasResourceBundle.bind(i18n),
		getResourceBundle: i18n.getResourceBundle.bind(i18n),
		removeResourceBundle: i18n.removeResourceBundle.bind(i18n)
	};
};

const createIsLoadingStore = (i18n: i18nType) => {
	const isLoading = writable(false);

	// if loaded resources are empty || {}, set loading to true
	i18n.on('loaded', (resources) => {
		// console.log('loaded:', resources);
		isLoading.set(Object.keys(resources).length === 0);
	});

	// if resources failed loading, set loading to true
	i18n.on('failedLoading', () => {
		isLoading.set(true);
	});

	return isLoading;
};

export const initI18n = (defaultLocale?: string | undefined) => {
	const detectionOrder = defaultLocale
		? ['querystring', 'localStorage']
		: ['querystring', 'localStorage', 'navigator'];
	const fallbackDefaultLocale = defaultLocale ? [defaultLocale] : ['en-US'];

	const loadResource = (language: string, namespace: string) =>
		import(`./locales/${language}/${namespace}.json`);

	i18next
		.use(resourcesToBackend(loadResource))
		.use(LanguageDetector)
		.init({
			debug: false,
			detection: {
				order: detectionOrder,
				caches: ['localStorage'],
				lookupQuerystring: 'lang',
				lookupLocalStorage: 'locale'
			},
			fallbackLng: {
				default: fallbackDefaultLocale
			},
			ns: 'translation',
			returnEmptyString: false,
			interpolation: {
				escapeValue: false // not needed for svelte as it escapes by default
			}
		});

	const lang = i18next?.language || defaultLocale || 'en-US';
	document.documentElement.setAttribute('lang', lang);
};

const i18n = createI18nStore(i18next);
const isLoadingStore = createIsLoadingStore(i18next);

export const getLanguages = async () => {
	const languages = (await import(`./locales/languages.json`)).default;
	return languages;
};

// Enhanced changeLanguage that updates DOM lang attribute
export const changeLanguage = (lang: string) => {
	document.documentElement.setAttribute('lang', lang);
	i18next.changeLanguage(lang);
};

export default i18n;
export const isLoading = isLoadingStore;
