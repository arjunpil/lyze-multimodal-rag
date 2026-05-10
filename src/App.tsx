// src/App.tsx
// Lyze — Intelligence Canvas
// React frontend wired to the local Python RAG backend

import { useState, useRef, useCallback } from "react";
import { Upload, Search, Zap, Github, Settings, RotateCcw } from "lucide-react";
import { ingestFiles, queryRAG, clearStore, Source } from "./api/lyzeClient";
import { useBackendStatus } from "./hooks/useBackendStatus";
import { BackendBanner } from "./components/BackendBanner";

const MODALITY_OPTIONS = ["All", "text", "image", "audio", "video_frame", "video_audio"];

export default function App() {
  const { connected, checking, totalChunks, recheck } = useBackendStatus();

  // Upload state
  const [files, setFiles] = useState<File[]>([]);
  const [ingesting, setIngesting] = useState(false);
  const [ingestLog, setIngestLog] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Query state
  const [question, setQuestion] = useState("");
  const [modality, setModality] = useState("All");
  const [topK, setTopK] = useState(5);
  const [querying, setQuerying] = useState(false);
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);

  // Settings panel
  const [settingsOpen, setSettings] = useState(false);

  const addLog = useCallback((msg: string) => {
    setIngestLog(prev => [...prev, msg]);
  }, []);

  // ── Handle file drop / select ─────────────────────────────────────────────
  const handleFiles = useCallback((newFiles: FileList | File[]) => {
    const arr = Array.from(newFiles);
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name));
      return [...prev, ...arr.filter(f => !names.has(f.name))];
    });
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  // ── Ingest ────────────────────────────────────────────────────────────────
  const handleIngest = useCallback(async () => {
    if (!files.length) return;
    setIngesting(true);
    setIngestLog([]);
    try {
      await ingestFiles(files, addLog);
      recheck();
    } finally {
      setIngesting(false);
    }
  }, [files, addLog, recheck]);

  // ── Query ─────────────────────────────────────────────────────────────────
  const handleQuery = useCallback(async () => {
    if (!question.trim() || querying) return;
    setQuerying(true);
    setAnswer("");
    setSources([]);
    try {
      const res = await queryRAG(question, {
        top_k: topK,
        modality_filter: modality === "All" ? null : modality,
      });
      setAnswer(res.answer);
      setSources(res.sources);
    } catch (e) {
      setAnswer(`Error: ${e instanceof Error ? e.message : "Query failed"}`);
    } finally {
      setQuerying(false);
    }
  }, [question, querying, topK, modality]);

  const handleClear = useCallback(async () => {
    if (!confirm("Clear all indexed documents?")) return;
    await clearStore();
    setIngestLog([]);
    setFiles([]);
    setAnswer("");
    setSources([]);
    recheck();
  }, [recheck]);

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen w-screen bg-[#0a1628] text-[#c8dff5] overflow-hidden font-sans" style={{ maxHeight: '100vh', maxWidth: '100vw' }}>

      {/* Backend offline banner */}
      {!checking && !connected && <BackendBanner onRetry={recheck} />}

      {/* ── Left sidebar ── */}
      <aside className="w-16 flex-shrink-0 bg-[#060e1e] border-r border-[#1565C0]/10
                        flex flex-col items-center py-4 gap-2 z-10">
        {/* Logo */}
        <div className="w-10 h-10 rounded-xl overflow-hidden border border-[#00B4D8]/25 mb-4 flex-shrink-0">
          <img src="/logo.png" alt="Lyze" className="w-full h-full object-cover"
            onError={e => { (e.target as HTMLImageElement).style.display = "none"; }} />
        </div>

        <SbBtn active title="Home"><Zap size={16} /></SbBtn>
        <div className="w-7 h-px bg-[#1565C0]/10 my-1" />
        <a href="https://github.com/arjunpil/lyze-multimodal-rag" target="_blank" rel="noreferrer">
          <SbBtn title="GitHub"><Github size={16} /></SbBtn>
        </a>

        <div className="mt-auto flex flex-col items-center gap-2">
          <div className="w-7 h-px bg-[#1565C0]/10" />
          <SbBtn title="Settings" onClick={() => setSettings(s => !s)}>
            <Settings size={16} />
          </SbBtn>
        </div>
      </aside>

      {/* ── Centre ── */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">

        {/* Topbar */}
        <header className="flex items-end gap-4 px-7 pt-5 pb-4
                           border-b border-[#1565C0]/10 bg-[#060e1e] flex-shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Intelligence Canvas</h1>
            <p className="text-xs text-[#1a3a6a] mt-0.5">Multimodal RAG Environment</p>
          </div>
          <div className="ml-auto flex items-center gap-2 pb-0.5">
            {/* Status dot */}
            <span className={`w-2 h-2 rounded-full ${connected ? "bg-[#00B4D8] shadow-[0_0_6px_#00B4D8]" : "bg-red-500"}`} />
            <span className={`text-xs font-semibold ${connected ? "text-[#00B4D8]" : "text-red-400"}`}>
              {checking ? "Checking..." : connected ? `System Ready · ${totalChunks} chunks` : "Backend Offline"}
            </span>
          </div>
        </header>

        {/* Two-col content */}
        <div className="flex flex-1 overflow-hidden">

          {/* Left panel */}
          <div className="w-[460px] flex-shrink-0 flex flex-col border-r border-[#1565C0]/08
                          bg-[#0a1628] overflow-hidden px-5 py-5 gap-4">

            {/* Sources */}
            <section className="flex flex-col gap-3 flex-shrink-0">
              <Label>Sources</Label>

              {/* Drop zone */}
              <div
                onDrop={onDrop}
                onDragOver={e => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-[#1565C0]/30 rounded-xl
                           bg-[#040c1c] min-h-[90px] flex flex-col items-center
                           justify-center cursor-pointer gap-2
                           hover:border-[#00B4D8]/50 transition-colors group"
              >
                <Upload size={20} className="text-[#00B4D8]/25 group-hover:text-[#00B4D8]/50 transition-colors" />
                <p className="text-xs text-[#2a4a7a]">Drop files or click to browse</p>
                <p className="text-[10px] text-[#1a3060]">PDF · PNG · JPG · MP3 · WAV · MP4 · MOV</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a,.mp4,.mov"
                  className="hidden"
                  onChange={e => e.target.files && handleFiles(e.target.files)}
                />
              </div>

              {/* File list */}
              {files.length > 0 && (
                <div className="space-y-1.5 max-h-28 overflow-y-auto">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center justify-between
                                            bg-[#040c1c] border border-[#1565C0]/15
                                            rounded-lg px-3 py-2">
                      <span className="text-xs text-[#4a8adf] truncate">{f.name}</span>
                      <button
                        onClick={() => setFiles(prev => prev.filter((_, j) => j !== i))}
                        className="text-[#1a3a6a] hover:text-red-400 ml-2 flex-shrink-0 text-xs"
                      >✕</button>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={handleIngest}
                disabled={!files.length || ingesting || !connected}
                className="w-full py-2.5 rounded-lg font-bold text-xs tracking-widest uppercase
                           bg-gradient-to-r from-[#1565C0] to-[#00B4D8] text-white
                           disabled:opacity-40 hover:opacity-85 transition-opacity"
              >
                {ingesting ? "Analyzing..." : "Analyze Dataset"}
              </button>

              {/* Log */}
              {ingestLog.length > 0 && (
                <pre className="text-[11px] text-[#00B4D8] font-mono bg-[#020810]
                                border border-[#1565C0]/12 rounded-lg p-3
                                max-h-28 overflow-y-auto leading-relaxed whitespace-pre-wrap">
                  {ingestLog.join("\n")}
                </pre>
              )}
            </section>

            <div className="h-px bg-[#1565C0]/08 flex-shrink-0" />

            {/* Query engine */}
            <section className="flex flex-col gap-3 flex-1 overflow-hidden">
              <Label>Query Engine</Label>
              <h2 className="text-lg font-bold text-[#d0e8ff] tracking-tight flex-shrink-0">
                What do you want to find?
              </h2>

              <textarea
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === "Enter" && e.ctrlKey && handleQuery()}
                placeholder="Describe your query or ask a specific question..."
                className="flex-1 min-h-[120px] bg-[#040c1c] border border-[#1565C0]/20
                           text-[#c8dff5] rounded-xl px-4 py-3 text-sm resize-none
                           placeholder-[#1a3a6a] focus:outline-none
                           focus:border-[#00B4D8]/50 transition-colors"
              />

              <div className="flex gap-2 flex-shrink-0">
                <select
                  value={modality}
                  onChange={e => setModality(e.target.value)}
                  className="flex-1 bg-[#040c1c] border border-[#1565C0]/20 text-[#c8dff5]
                             rounded-lg px-3 py-2 text-xs focus:outline-none
                             focus:border-[#00B4D8]/50"
                >
                  {MODALITY_OPTIONS.map(m => (
                    <option key={m} value={m}>{m === "All" ? "All modalities" : m}</option>
                  ))}
                </select>
                <select
                  value={topK}
                  onChange={e => setTopK(Number(e.target.value))}
                  className="w-24 bg-[#040c1c] border border-[#1565C0]/20 text-[#c8dff5]
                             rounded-lg px-3 py-2 text-xs focus:outline-none
                             focus:border-[#00B4D8]/50"
                >
                  {[3, 5, 7, 10].map(n => (
                    <option key={n} value={n}>{n} results</option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleQuery}
                disabled={!question.trim() || querying || !connected}
                className="w-full py-2.5 rounded-lg font-bold text-xs tracking-widest uppercase
                           bg-gradient-to-r from-[#1565C0] to-[#00B4D8] text-white
                           disabled:opacity-40 hover:opacity-85 transition-opacity
                           flex items-center justify-center gap-2"
              >
                <Search size={13} />
                {querying ? "Searching..." : "Search"}
              </button>

              {/* Quick prompts */}
              <div className="flex flex-wrap gap-1.5 flex-shrink-0">
                {["Summarize findings", "Key insights", "What are the main topics?"].map(p => (
                  <button
                    key={p}
                    onClick={() => setQuestion(p)}
                    className="text-[10px] text-[#1a3a6a] border border-[#1565C0]/15
                               rounded-full px-3 py-1 hover:text-[#00B4D8]
                               hover:border-[#00B4D8]/30 transition-colors"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </section>
          </div>

          {/* Right panel — output */}
          <div className="flex-1 flex flex-col overflow-hidden bg-[#0a1628] px-5 py-5 gap-4 min-w-0">
            <div className="flex items-center justify-between flex-shrink-0">
              <Label>Output Area</Label>
              {(answer || sources.length > 0) && (
                <button
                  onClick={() => { setAnswer(""); setSources([]); }}
                  className="text-[10px] text-[#1a3060] hover:text-[#00B4D8] transition-colors"
                >
                  Clear
                </button>
              )}
            </div>

            {/* Answer */}
            <div className="flex-1 min-h-0 bg-[#040c1c] border border-[#1565C0]/15
                            rounded-xl p-4 overflow-y-auto">
              {querying ? (
                <div className="flex items-center gap-3 text-[#00B4D8] text-sm">
                  <div className="w-4 h-4 border-2 border-[#00B4D8]/30 border-t-[#00B4D8]
                                  rounded-full animate-spin" />
                  Searching across your documents...
                </div>
              ) : answer ? (
                <p className="text-sm text-[#d0e8ff] leading-relaxed whitespace-pre-wrap">{answer}</p>
              ) : (
                <p className="text-sm text-[#1a3060]">Analysis results will appear here...</p>
              )}
            </div>

            {/* Supporting data */}
            {sources.length > 0 && (
              <div className="flex-shrink-0">
                <Label>Supporting Data</Label>
                <div className="space-y-2 mt-2 max-h-52 overflow-y-auto">
                  {sources.map((src, i) => (
                    <div key={i} className="flex gap-3 bg-[#040c1c] border border-[#1565C0]/15
                                            rounded-xl p-3 items-start">
                      <span className="text-[10px] font-bold text-white bg-[#1565C0]/35
                                       rounded px-1.5 py-0.5 flex-shrink-0 font-mono">
                        0{i + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-[#c8dff5] truncate">
                          {src.source.split(/[\\/]/).pop()}
                        </p>
                        <p className="text-[10px] text-[#1a3a6a] uppercase tracking-wider my-0.5">
                          {src.modality} · score {src.score}
                        </p>
                        <p className="text-[11px] text-[#2a5070] leading-relaxed line-clamp-2">
                          {src.preview}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Right settings panel ── */}
      <aside className={`flex-shrink-0 bg-[#060e1e] border-l border-[#1565C0]/10
                         flex flex-col px-4 py-5 overflow-y-auto
                         transition-all duration-200
                         ${settingsOpen ? "w-56" : "w-0 px-0 overflow-hidden"}`}>
        {settingsOpen && (
          <>
            <p className="text-sm font-bold text-[#00B4D8] mb-1">System Configuration</p>
            <p className="text-[11px] text-[#1a3a6a] mb-4">Multimodal Model Settings</p>

            <div className="h-px bg-[#1565C0]/10 mb-3" />

            <p className="text-[10px] font-bold tracking-widest uppercase text-[#1565C0]/40 mb-2">Models</p>
            {[
              { label: "Language", env: import.meta.env.VITE_LLM_MODEL || "mistral" },
              { label: "Vision", env: import.meta.env.VITE_VISION_MODEL || "llava" },
              { label: "Embed", env: import.meta.env.VITE_EMBED_MODEL || "nomic-embed-text" },
            ].map(item => (
              <div key={item.label}
                className="flex items-center gap-2 px-2 py-2 rounded-lg
                              border-l-2 border-[#00B4D8] bg-[#00B4D8]/05 mb-1.5">
                <div>
                  <p className="text-xs text-[#c8dff5] font-medium">{item.label}</p>
                  <p className="text-[10px] text-[#1a3a6a]">{item.env}</p>
                </div>
              </div>
            ))}

            <div className="h-px bg-[#1565C0]/10 my-3" />
            <p className="text-[10px] font-bold tracking-widest uppercase text-[#1565C0]/40 mb-2">Store</p>
            <div className="bg-[#040c1c] border border-[#1565C0]/15 rounded-lg px-3 py-2 mb-3">
              <p className="text-[10px] text-[#1a3a6a] uppercase tracking-wider">Chunks indexed</p>
              <p className="text-sm font-bold text-[#00B4D8]">{totalChunks}</p>
            </div>
            <button
              onClick={handleClear}
              className="w-full py-2 rounded-lg text-[10px] font-bold tracking-widest
                         uppercase text-red-400 border border-red-900/30
                         hover:bg-red-900/10 transition-colors flex items-center
                         justify-center gap-1.5 mb-3"
            >
              <RotateCcw size={11} /> Clear Store
            </button>

            <div className="h-px bg-[#1565C0]/10 my-1" />
            <p className="text-[10px] text-[#1a3060] leading-relaxed mt-2">
              Edit <code className="text-[#00B4D8] font-mono">backend/.env</code> to change providers. Restart backend after saving.
            </p>

            <a href="https://github.com/arjunpil/lyze-multimodal-rag"
              target="_blank" rel="noreferrer"
              className="mt-4 block py-2.5 rounded-xl font-bold text-[10px] tracking-widest
                          uppercase text-center text-white
                          bg-gradient-to-r from-[#1565C0] to-[#00B4D8]
                          hover:opacity-85 transition-opacity">
              View on GitHub
            </a>
          </>
        )}
      </aside>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────
function Label({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-bold tracking-[2.5px] uppercase text-[#00B4D8]/35">
      {children}
    </p>
  );
}

function SbBtn({
  children, title, active, onClick
}: {
  children: React.ReactNode;
  title?: string;
  active?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className={`w-10 h-10 rounded-9 flex items-center justify-center
                  border transition-all duration-150
                  ${active
          ? "bg-[#0d2a54] text-[#00B4D8] border-[#1565C0]/60"
          : "bg-transparent text-[#1a3a6a] border-transparent hover:bg-[#0d2040] hover:text-[#00B4D8] hover:border-[#1565C0]/25"
        }`}
    >
      {children}
    </button>
  );
}