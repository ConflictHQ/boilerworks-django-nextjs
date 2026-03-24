"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SendIcon, BotIcon, UserIcon } from "lucide-react";

const MODELS = ["Genesis", "Explorer", "Quantum"];

type Message = { role: "user" | "assistant"; content: string };

const initialMessages: Message[] = [
  { role: "user", content: "Explain the concept of zero-shot prompting." },
  {
    role: "assistant",
    content:
      "Zero-shot prompting means asking a model to perform a task without giving it any examples. The model relies solely on its pre-trained knowledge to generate a response. This is useful when you need quick answers and don't have labeled examples ready.",
  },
  { role: "user", content: "Can you give me a practical example?" },
  {
    role: "assistant",
    content:
      "Sure! A zero-shot prompt might look like: \"Translate the following English text to French: 'Hello, how are you?'\" — no French examples provided, yet the model handles it correctly.",
  },
];

export default function PlaygroundPage() {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("Genesis");
  const [loading, setLoading] = useState(false);

  const handleSend = () => {
    if (!prompt.trim()) return;
    const userMsg: Message = { role: "user", content: prompt };
    setMessages((prev) => [...prev, userMsg]);
    setPrompt("");
    setLoading(true);
    setTimeout(() => {
      const assistantMsg: Message = {
        role: "assistant",
        content: `[${model}] This is a simulated response to: "${userMsg.content}"`,
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="flex flex-1 gap-4 p-6">
      {/* Left: conversation history list */}
      <div className="hidden w-56 shrink-0 flex-col gap-2 lg:flex">
        <h2 className="text-muted-foreground px-1 text-sm font-semibold">Recent sessions</h2>
        {["Zero-shot prompting", "Code review", "Data analysis", "Creative writing"].map((s) => (
          <button
            key={s}
            className="hover:bg-accent truncate rounded-md px-3 py-2 text-left text-sm"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Right: editor panel */}
      <div className="flex flex-1 flex-col gap-4">
        {/* Model selector */}
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground text-sm">Model</span>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MODELS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Message thread */}
        <Card className="flex-1 overflow-auto">
          <CardContent className="flex flex-col gap-4 p-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
              >
                <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
                  {msg.role === "user" ? (
                    <UserIcon className="h-4 w-4" />
                  ) : (
                    <BotIcon className="h-4 w-4" />
                  )}
                </div>
                <div
                  className={`max-w-prose rounded-lg px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
                  <BotIcon className="h-4 w-4" />
                </div>
                <div className="bg-muted text-muted-foreground animate-pulse rounded-lg px-4 py-2 text-sm">
                  Thinking…
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Input */}
        <div className="flex gap-2">
          <Textarea
            placeholder="Enter your prompt…"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            className="resize-none"
            rows={3}
          />
          <Button onClick={handleSend} disabled={loading || !prompt.trim()} className="self-end">
            <SendIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
