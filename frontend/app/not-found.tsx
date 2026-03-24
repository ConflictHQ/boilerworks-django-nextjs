import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

export default function NotFound() {
  return (
    <div className="bg-background flex min-h-screen items-center justify-center">
      <div className="flex max-w-md flex-col items-center gap-6 px-4 text-center">
        <div className="flex items-center gap-4">
          <span className="text-4xl font-bold tracking-tight">404</span>
          <Separator
            orientation="vertical"
            className="h-10 data-vertical:h-10 data-vertical:self-auto"
          />
          <span className="text-muted-foreground text-lg">Page not found</span>
        </div>

        <p className="text-muted-foreground text-sm">
          The page you are looking for does not exist or has been moved.
        </p>

        <Button asChild>
          <Link href="/">Go home</Link>
        </Button>
      </div>
    </div>
  );
}
