import type { Metadata } from "next";
import { ApolloWrapper } from "@/lib/apollo";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ConfirmProvider } from "@/hooks/use-confirm";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { ThemeProvider } from "next-themes";
import { Toaster } from "@/components/Toaster";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Boilerworks",
    template: "%s · Boilerworks",
  },
  description: "Boilerworks application",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className="antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <Toaster />
          <NextIntlClientProvider locale={locale} messages={messages}>
            <ApolloWrapper>
              <TooltipProvider>
                <ConfirmProvider>{children}</ConfirmProvider>
              </TooltipProvider>
            </ApolloWrapper>
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
