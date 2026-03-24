export const locales = ["en", "pl", "es", "fr", "de", "it", "pt"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";
