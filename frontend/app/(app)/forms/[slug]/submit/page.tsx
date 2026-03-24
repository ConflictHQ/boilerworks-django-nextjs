"use client";

import { useParams, useRouter } from "next/navigation";
import { DynamicForm } from "@/components/forms/DynamicForm";

export default function FormSubmitPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <DynamicForm
        slug={slug}
        onSuccess={() => {
          setTimeout(() => router.push(`/forms/${slug}`), 2000);
        }}
      />
    </div>
  );
}
