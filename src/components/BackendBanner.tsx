// src/components/BackendBanner.tsx
// Shows a clear banner when the Python backend isn't running

interface Props {
  onRetry: () => void;
}

export function BackendBanner({ onRetry }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#060e1e]/95 backdrop-blur-sm">
      <div className="max-w-md w-full mx-4 bg-[#0d1f3c] border border-[#1565C0]/30 rounded-2xl p-8 text-center">
        {/* Icon */}
        <div className="w-16 h-16 mx-auto mb-5 rounded-full bg-[#1565C0]/15 flex items-center justify-center">
          <svg className="w-8 h-8 text-[#00B4D8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.14 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
          </svg>
        </div>

        <h2 className="text-xl font-bold text-white mb-2">Backend not running</h2>
        <p className="text-[#3a6090] text-sm leading-relaxed mb-6">
          Lyze needs its local backend to process files and run AI queries.
          Start it in a terminal before using the app.
        </p>

        {/* Instructions */}
        <div className="bg-[#020810] rounded-xl p-4 text-left mb-6 border border-[#1565C0]/15">
          <p className="text-[#00B4D8] text-xs font-semibold uppercase tracking-widest mb-3">
            How to start
          </p>
          <div className="space-y-2">
            <div className="flex gap-3 items-start">
              <span className="text-[#1565C0] font-mono text-xs mt-0.5">1</span>
              <p className="text-[#5a8abf] text-xs">
                Open a terminal in the project folder
              </p>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-[#1565C0] font-mono text-xs mt-0.5">2</span>
              <div>
                <p className="text-[#5a8abf] text-xs mb-1">Windows:</p>
                <code className="text-[#00B4D8] text-xs font-mono bg-[#040c1c] px-2 py-1 rounded">
                  start_backend.bat
                </code>
              </div>
            </div>
            <div className="flex gap-3 items-start">
              <span className="text-[#1565C0] font-mono text-xs mt-0.5"></span>
              <div>
                <p className="text-[#5a8abf] text-xs mb-1">Mac / Linux:</p>
                <code className="text-[#00B4D8] text-xs font-mono bg-[#040c1c] px-2 py-1 rounded">
                  ./start_backend.sh
                </code>
              </div>
            </div>
          </div>
        </div>

        <button
          onClick={onRetry}
          className="w-full py-3 rounded-xl font-bold text-sm tracking-widest uppercase
                     bg-gradient-to-r from-[#1565C0] to-[#00B4D8] text-white
                     hover:opacity-85 transition-opacity"
        >
          Retry Connection
        </button>
      </div>
    </div>
  );
}
