"use client";
import { useState, useRef, useEffect } from "react";
import { Send, FileText, Mic, Globe, Plus } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  plan?: Array<{ id: number; description: string; status: string }>;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [enableSearch, setEnableSearch] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 50 * 1024 * 1024) {
      setMessages((prev) => [...prev, {
        id: Date.now().toString(), role: "assistant",
        content: "文件过大：" + (file.size / 1024 / 1024).toFixed(1) + "MB，限制 50MB",
      }]);
      return;
    }

    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("http://localhost:8000/api/knowledge/ingest/file", {
        method: "POST", body: form,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadedFile(data.filename);
        setMessages((prev) => [...prev,
          { id: Date.now().toString(), role: "user", content: "上传文件：" + file.name },
          { id: (Date.now() + 1).toString(), role: "assistant",
            content: "文件「" + data.filename + "」已就绪（" + (data.size / 1024).toFixed(1) + "KB）。你可以直接向我提问。\n\n预览：" + data.content_preview,
          },
        ]);
      } else {
        throw new Error(data.detail || "upload failed");
      }
    } catch {
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(), role: "assistant",
        content: "文件上传失败，请确认后端服务已启动。",
      }]);
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function sendMessage() {
    if (!input.trim() || loading) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const assistantId = (Date.now() + 1).toString();
    setMessages((prev) => [...prev, { id: assistantId, role: "assistant", content: "" }]);

    try {
      const body: Record<string, string> = { message: input };
      if (uploadedFile) body.filename = uploadedFile;
      if (conversationId) body.conversation_id = conversationId;
      if (enableSearch) body.enable_search = "true";

      const res = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const reader = res.body?.getReader();
      if (!reader) throw new Error("no reader");
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const dataStr = line.slice(6);
          if (dataStr === "[DONE]") continue;
          try {
            const data = JSON.parse(dataStr);
            if (data.type === "message" && data.content) {
              setMessages((prev) => prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + data.content } : m
              ));
            } else if (data.type === "done") {
              if (data.conversation_id) setConversationId(data.conversation_id);
              setMessages((prev) => prev.map((m) =>
                m.id === assistantId ? { ...m, plan: data.plan } : m
              ));
            }
          } catch {}
        }
      }
    } catch {
      setMessages((prev) => prev.map((m) =>
        m.id === assistantId && !m.content
          ? { ...m, content: "连接失败，请确认后端服务已启动。" }
          : m
      ));
    }
    setLoading(false);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto">
      <header className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "var(--color-border)" }}>
        <h1 className="text-lg font-semibold">智能办公Agent</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setMessages([]);
              setConversationId(null);
              setUploadedFile(null);
            }}
            className="p-1.5 rounded-md hover:bg-gray-100 text-xs flex items-center gap-1"
            title="新对话"
          >
            <Plus size={16} /> 新对话
          </button>
          <span className="text-xs px-2 py-1 rounded-full" style={{ background: "var(--color-accent)", color: "#fff" }}>Beta</span>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-20" style={{ color: "var(--color-text-muted)" }}>
            <h2 className="text-2xl font-semibold mb-2">有什么我可以帮你的？</h2>
            <p className="text-sm">上传文档提问、处理邮件、安排日程、生成报告...</p>
            <div className="flex gap-2 justify-center mt-6 flex-wrap">
              {["总结文档要点", "起草邮件回复", "安排下周会议", "分析销售数据"].map((hint) => (
                <button
                  key={hint}
                  onClick={() => setInput(hint)}
                  className="px-3 py-1.5 text-sm rounded-full border"
                  style={{ borderColor: "var(--color-border)" }}
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={"flex " + (msg.role === "user" ? "justify-end" : "justify-start")}>
            <div
              className="max-w-[80%] px-4 py-3 rounded-lg"
              style={{
                background: msg.role === "user" ? "var(--color-accent)" : "var(--color-surface-raised)",
                color: msg.role === "user" ? "#fff" : "var(--color-text)",
                border: msg.role === "assistant" ? "1px solid var(--color-border)" : "none",
              }}
            >
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
              {msg.plan && msg.plan.length > 0 && (
                <div className="mt-2 pt-2 border-t" style={{ borderColor: "var(--color-border)" }}>
                  <p className="text-xs font-medium mb-1" style={{ color: "var(--color-text-muted)" }}>执行步骤：</p>
                  {msg.plan.map((step) => (
                    <div key={step.id} className="flex items-center gap-2 text-xs py-0.5">
                      <span className={step.status === "done" ? "text-green-500" : "text-gray-400"}>
                        {step.status === "done" ? "✓" : "○"}
                      </span>
                      {step.description}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </main>

      <footer className="px-6 py-4 border-t" style={{ borderColor: "var(--color-border)" }}>
        {uploadedFile && (
          <div className="text-xs mb-2 flex items-center gap-2" style={{ color: "var(--color-accent)" }}>
            <FileText size={14} />
            <span>当前文档：{uploadedFile}</span>
            <button onClick={() => setUploadedFile(null)} className="underline" style={{ color: "var(--color-text-muted)" }}>清除</button>
          </div>
        )}
        <div className="flex items-center gap-2">
          <input
            type="file" ref={fileInputRef} onChange={handleFileUpload}
            className="hidden" accept=".txt,.md,.pdf,.docx,.xlsx,.pptx,.csv"
          />
          <button
            className="p-2 rounded-md hover:bg-gray-100 disabled:opacity-50"
            title="上传文件" disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
          >
            <FileText size={18} />
          </button>
          <button className="p-2 rounded-md hover:bg-gray-100" title="语音输入" disabled>
            <Mic size={18} />
          </button>
          <button
            className="p-2 rounded-md hover:bg-gray-100"
            title={enableSearch ? "联网搜索已开启" : "联网搜索已关闭"}
            onClick={() => setEnableSearch(!enableSearch)}
            style={enableSearch ? { color: "var(--color-accent)" } : {}}
          >
            <Globe size={18} />
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={uploading ? "正在上传文件..." : uploadedFile ? "对「" + uploadedFile + "」提问..." : "输入消息，Enter发送..."}
            rows={1}
            className="flex-1 px-4 py-2 rounded-md border text-sm resize-none outline-none"
            style={{ borderColor: "var(--color-border)", maxHeight: "120px" }}
            disabled={uploading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || uploading || !input.trim()}
            className="p-2 rounded-md text-white disabled:opacity-50"
            style={{ background: "var(--color-accent)" }}
          >
            <Send size={18} />
          </button>
        </div>
      </footer>
    </div>
  );
}
