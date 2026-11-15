import type { Metadata } from "next";
import { AppearanceScript } from "@calliopelabs/ui";
import { ApolloWrapper } from "@/lib/apollo";
import { TooltipProvider } from "@/ui-app/primitives/tooltip";
import { ConfirmProvider } from "@/hooks/use-confirm";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { Toaster } from "@/components/Toaster";
import { AppearanceRoot } from "@/ui-app/providers/AppearanceRoot";
import { UiEnvironment } from "@/ui-app/providers/UiEnvironment";
import { product } from "@/ui-app/product";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans/700.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource-variable/dm-sans/index.css";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: product.name,
    template: `%s · ${product.name}`,
  },
  description: `${product.name} application`,
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    // AppearanceScript stamps the ground, accent and mode on <html> before
    // React hydrates, hence suppressHydrationWarning.
    <html lang={locale} suppressHydrationWarning>
      <head>
        <AppearanceScript product={product} />
      </head>
      <body className="antialiased">
        <AppearanceRoot>
          <Toaster />
          <NextIntlClientProvider locale={locale} messages={messages}>
            <UiEnvironment>
              <ApolloWrapper>
                <TooltipProvider>
                  <ConfirmProvider>{children}</ConfirmProvider>
                </TooltipProvider>
              </ApolloWrapper>
            </UiEnvironment>
          </NextIntlClientProvider>
        </AppearanceRoot>
      </body>
    </html>
  );
}
