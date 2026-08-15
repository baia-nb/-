import React, { useEffect, useRef, useState } from 'react'

const API = '/api'

const FEATURES = [
  { icon: 'blocks', title: '建筑格式互转', desc: 'BDX / Litematic / MCStructure / Schematic / Schem 自由转换' },
  { icon: 'music', title: '音乐转指令', desc: 'MIDI / NBS 乐谱转换为红石音乐指令' },
  { icon: 'lock', title: '加密服务', desc: '.baia 加密格式与授权码体系，保护你的作品' },
  { icon: 'layers', title: '批量处理', desc: '一次导入多个文件，批量完成转换与优化' },
  { icon: 'grid', title: '像素画转换', desc: '图片一键转为 Minecraft 像素画建筑' },
  { icon: 'wand', title: '结构优化', desc: 'fill 合并 / 区块化 / 掉落保护 / 生成保护' },
]

function Icon({ name, className = 'w-7 h-7' }) {
  const c = {
    className,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 2,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    viewBox: '0 0 24 24',
  }
  switch (name) {
    case 'blocks':
      return (
        <svg {...c}>
          <rect x="3" y="3" width="7" height="7" />
          <rect x="14" y="3" width="7" height="7" />
          <rect x="3" y="14" width="7" height="7" />
          <rect x="14" y="14" width="7" height="7" />
        </svg>
      )
    case 'music':
      return (
        <svg {...c}>
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
      )
    case 'lock':
      return (
        <svg {...c}>
          <rect x="4" y="11" width="16" height="9" rx="2" />
          <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </svg>
      )
    case 'layers':
      return (
        <svg {...c}>
          <path d="M12 2 2 7l10 5 10-5-10-5Z" />
          <path d="m2 17 10 5 10-5" />
          <path d="m2 12 10 5 10-5" />
        </svg>
      )
    case 'grid':
      return (
        <svg {...c}>
          <rect x="3" y="3" width="18" height="18" rx="2" />
          <path d="M9 3v18M15 3v18M3 9h18M3 15h18" />
        </svg>
      )
    case 'wand':
      return (
        <svg {...c}>
          <path d="m15 4 5 5L9 20H4v-5L15 4Z" />
          <path d="M14 7l3 3" />
        </svg>
      )
    case 'upload':
      return (
        <svg {...c}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <path d="M17 8l-5-5-5 5" />
          <path d="M12 3v12" />
        </svg>
      )
    case 'download':
      return (
        <svg {...c}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <path d="M7 10l5 5 5-5" />
          <path d="M12 15V3" />
        </svg>
      )
    case 'arrow':
      return (
        <svg {...c}>
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      )
    default:
      return null
  }
}

function fmtSize(n) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(2)} MB`
}

/* ----------------------------- 全功能工具箱 ----------------------------- */
function Toolbox({ plugins }) {
  const cats = Object.keys(plugins)
  const [cat, setCat] = useState(cats[0])
  const [tool, setTool] = useState(plugins[cats[0]]?.[0]?.name || '')
  const [files, setFiles] = useState([])
  const [params, setParams] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileRef = useRef(null)
  const isBatch = tool.includes('批量')

  function selectTool(name) {
    setTool(name)
    setFiles([])
    setParams('')
    setResult(null)
    setError(null)
  }

  async function run() {
    if (!files.length && !params.trim()) {
      setError('请先上传文件，或在“额外参数”中填写所需内容')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('plugin', tool)
      for (const f of files) fd.append('files', f)
      fd.append('params', params)
      const res = await fetch(`${API}/plugin/run`, { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '运行失败')
      setResult(data)
    } catch (e) {
      setError(e.message || '运行失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mc-panel p-6 sm:p-8">
      <h2 className="text-xl font-bold mb-1">全功能工具箱</h2>
      <p className="text-stone-400 text-sm mb-5">
        以下全部功能均来自你本机的核心引擎，按分类点击即可使用。
      </p>

      {/* 分类标签 */}
      <div className="flex flex-wrap gap-2 mb-4">
        {cats.map((c) => (
          <button
            key={c}
            onClick={() => { setCat(c); selectTool(plugins[c]?.[0]?.name || '') }}
            className={`px-3 py-1.5 rounded-lg text-sm font-semibold border-2 transition
              ${cat === c ? 'border-grass bg-grass/10 text-grass' : 'border-panel-border text-stone-300 hover:border-grass/50'}`}
          >
            {c} <span className="opacity-50">({plugins[c].length})</span>
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-[260px_1fr] gap-6">
        {/* 工具列表 */}
        <div className="flex flex-col gap-2 max-h-[420px] overflow-auto pr-1">
          {(plugins[cat] || []).map((p) => (
            <button
              key={p.name}
              onClick={() => selectTool(p.name)}
              className={`text-left rounded-lg border-2 px-3 py-2.5 transition
                ${tool === p.name ? 'border-grass bg-grass/10' : 'border-panel-border hover:border-grass/50'}`}
            >
              <div className="font-semibold text-sm">{p.name}</div>
              <div className="text-xs text-stone-400 mt-0.5">{p.desc}</div>
            </button>
          ))}
        </div>

        {/* 运行面板 */}
        <div className="rounded-xl border-2 border-panel-border p-5">
          <div className="font-bold text-lg mb-1">{tool}</div>
          <div className="text-stone-400 text-sm mb-4">
            {plugins[cat]?.find((p) => p.name === tool)?.desc}
          </div>

          {/* 上传 */}
          <div
            onClick={() => fileRef.current?.click()}
            className="cursor-pointer rounded-xl border-2 border-dashed px-5 py-7 text-center transition
              border-panel-border hover:border-grass/60"
          >
            <input
              ref={fileRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
            <div className="flex flex-col items-center gap-2 text-stone-300">
              <Icon name="upload" className="w-8 h-8 text-grass" />
              <div className="font-semibold">
                {isBatch ? '选择多个文件（将作为文件夹处理）' : '点击选择文件'}
              </div>
              <div className="text-xs text-stone-400">
                {isBatch ? '批量工具：上传的多个文件会被当作一个文件夹处理' : '单文件工具：按顺序上传即可'}
              </div>
            </div>
          </div>

          {files.length > 0 && (
            <div className="mt-3 text-sm text-stone-300">
              已选 {files.length} 个文件：
              <div className="mt-1 flex flex-wrap gap-1.5">
                {files.map((f, i) => (
                  <span key={i} className="mc-chip">{f.name}</span>
                ))}
              </div>
            </div>
          )}

          {/* 额外参数 */}
          <div className="mt-4">
            <div className="text-sm text-stone-400 mb-1">
              额外参数（可选，每行一个，按插件要求顺序填写，如授权码）
            </div>
            <textarea
              value={params}
              onChange={(e) => setParams(e.target.value)}
              rows={3}
              placeholder={'例如：\n授权码123456\n或者留空'}
              className="w-full rounded-lg bg-[#0e1116] border-2 border-panel-border p-3 text-sm
                text-stone-100 outline-none focus:border-grass/60 resize-none"
            />
          </div>

          <button
            onClick={run}
            disabled={loading}
            className="mc-btn mc-btn-primary w-full mt-4"
          >
            {loading ? '处理中…' : '运行'}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm px-4 py-3">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-5 rounded-lg border border-grass/40 bg-grass/10 px-4 py-4">
              {result.message && (
                <pre className="text-sm text-stone-200 whitespace-pre-wrap break-words mb-3 font-mono leading-relaxed">
{result.message}
                </pre>
              )}
              {result.files && result.files.length > 0 && (
                <>
                  <div className="text-sm text-stone-300 mb-3">
                    生成完成，共 {result.files.length} 个文件：
                  </div>
                  <div className="flex flex-col gap-2">
                    {result.files.map((name) => (
                      <a
                        key={name}
                        href={`${API}/download/${result.id}/${encodeURIComponent(name)}`}
                        className="mc-btn mc-btn-primary"
                      >
                        <Icon name="download" className="w-5 h-5" />
                        下载 {name}
                      </a>
                    ))}
                  </div>
                </>
              )}
              {(!result.files || result.files.length === 0) && !result.message && (
                <div className="text-sm text-stone-300">未产生输出文件，请检查输入与参数。</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

/* ------------------------------- 主应用 ------------------------------- */
export default function App() {
  const [formats, setFormats] = useState({ source: [], target: [] })
  const [file, setFile] = useState(null)
  const [sourceFmt, setSourceFmt] = useState(null)
  const [target, setTarget] = useState('txt')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [drag, setDrag] = useState(false)
  const [plugins, setPlugins] = useState({})
  const fileRef = useRef(null)

  useEffect(() => {
    fetch(`${API}/formats`)
      .then((r) => r.json())
      .then((d) => setFormats(d))
      .catch(() => {})
    fetch(`${API}/plugins`)
      .then((r) => r.json())
      .then((d) => setPlugins(d))
      .catch(() => {})
  }, [])

  function detectExt(name) {
    const m = name.toLowerCase().match(/\.([a-z0-9]+)$/)
    if (!m) return null
    const map = {
      bdx: 'bdx',
      litematic: 'litematic',
      mcstructure: 'mcstructure',
      schematic: 'schematic',
      schem: 'schem',
    }
    return map[m[1]] || null
  }

  function onSelectFile(f) {
    if (!f) return
    setFile(f)
    setSourceFmt(detectExt(f.name))
    setResult(null)
    setError(null)
  }

  async function onConvert() {
    if (!file) {
      setError('请先选择一个建筑文件')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('target', target)
      const res = await fetch(`${API}/convert`, { method: 'POST', body: fd })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '转换失败')
      setResult(data)
    } catch (e) {
      setError(e.message || '转换失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  function scrollToConvert() {
    document.getElementById('convert')?.scrollIntoView({ behavior: 'smooth' })
  }
  function scrollToToolbox() {
    document.getElementById('toolbox')?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen font-sans">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-30 backdrop-blur bg-[#0e1116]/80 border-b border-panel-border">
        <div className="max-w-6xl mx-auto px-5 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-md bg-grass grid place-items-center shadow-block">
              <span className="w-3.5 h-3.5 bg-[#0e1116]" />
            </div>
            <span className="font-bold tracking-wide">
              我的世界格式转换器<span className="text-grass"> · 在线版</span>
            </span>
          </div>
          <nav className="hidden sm:flex items-center gap-7 text-sm text-stone-300">
            <a href="#features" className="hover:text-grass transition">功能</a>
            <a href="#formats" className="hover:text-grass transition">支持的格式</a>
            <button onClick={scrollToConvert} className="hover:text-grass transition">结构转换</button>
            <button onClick={scrollToToolbox} className="hover:text-grass transition">全功能</button>
          </nav>
          <button onClick={scrollToToolbox} className="mc-btn mc-btn-primary text-sm py-2 px-4">
            全功能
          </button>
        </div>
      </header>

      {/* 英雄区 */}
      <section className="relative overflow-hidden">
        <div className="max-w-6xl mx-auto px-5 pt-20 pb-16 text-center">
          <div className="inline-block font-pixel text-[10px] sm:text-xs text-grass mb-5 px-3 py-1.5 rounded border border-grass/40 bg-grass/10">
            MINECRAFT FORMAT CONVERTER
          </div>
          <h1 className="text-4xl sm:text-6xl font-black leading-tight mb-6">
            把建筑文件<span className="text-grass"> 一键转换</span>
            <br className="hidden sm:block" />成你想要的格式
          </h1>
          <p className="text-stone-300 text-base sm:text-lg max-w-2xl mx-auto mb-9">
            支持 BDX / Litematic / MCStructure / Schematic / Schem 互转，
            直接生成 setblock 指令、IBI 加密包、DSB 与基岩版结构文件。
            本地浏览器上传，真实引擎解析。
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button onClick={scrollToConvert} className="mc-btn mc-btn-primary">
              立即转换
              <Icon name="arrow" className="w-5 h-5" />
            </button>
            <button onClick={scrollToToolbox} className="mc-btn mc-btn-ghost">浏览全部功能</button>
          </div>
        </div>
      </section>

      {/* 在线转换卡片（结构快捷转换） */}
      <section id="convert" className="max-w-3xl mx-auto px-5 pb-20 scroll-mt-20">
        <div className="mc-panel p-6 sm:p-8">
          <h2 className="text-xl font-bold mb-1">结构格式转换</h2>
          <p className="text-stone-400 text-sm mb-6">上传建筑文件，选择目标格式，开始转换。</p>

          <div
            onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault()
              setDrag(false)
              onSelectFile(e.dataTransfer.files?.[0])
            }}
            onClick={() => fileRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-10 text-center transition
              ${drag ? 'border-grass bg-grass/10' : 'border-panel-border hover:border-grass/60'}`}
          >
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept=".bdx,.litematic,.mcstructure,.schematic,.schem"
              onChange={(e) => onSelectFile(e.target.files?.[0])}
            />
            <div className="flex flex-col items-center gap-3 text-stone-300">
              <Icon name="upload" className="w-9 h-9 text-grass" />
              {file ? (
                <div>
                  <div className="font-semibold text-stone-100">{file.name}</div>
                  <div className="text-xs mt-1 text-stone-400">已选择 · 点击可重新选择</div>
                </div>
              ) : (
                <div>
                  <div className="font-semibold">拖拽文件到此处，或点击选择</div>
                  <div className="text-xs mt-1 text-stone-400">
                    支持 .bdx / .litematic / .mcstructure / .schematic / .schem
                  </div>
                </div>
              )}
            </div>
          </div>

          {file && (
            <div className="mt-4 flex items-center gap-2 text-sm">
              <span className="text-stone-400">识别源格式：</span>
              {sourceFmt ? (
                <span className="mc-chip text-grass border-grass/40">{sourceFmt}</span>
              ) : (
                <span className="mc-chip text-amber-300 border-amber-400/40">未能识别 (仍会尝试解析)</span>
              )}
            </div>
          )}

          <div className="mt-6">
            <div className="text-sm text-stone-400 mb-2">转换为</div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {formats.target.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTarget(t.id)}
                  className={`rounded-lg border-2 px-3 py-3 text-left transition
                    ${target === t.id ? 'border-grass bg-grass/10' : 'border-panel-border hover:border-grass/50'}`}
                >
                  <div className="font-semibold text-sm">{t.label}</div>
                  <div className="text-xs text-stone-400 mt-0.5">{t.ext}</div>
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={onConvert}
            disabled={loading || !file}
            className="mc-btn mc-btn-primary w-full mt-6"
          >
            {loading ? '转换中…' : '开始转换'}
          </button>

          {error && (
            <div className="mt-4 rounded-lg border border-red-500/40 bg-red-500/10 text-red-300 text-sm px-4 py-3">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-5 rounded-lg border border-grass/40 bg-grass/10 px-4 py-4">
              <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm mb-3">
                <div>
                  <span className="text-stone-400">方块数：</span>
                  <span className="font-bold text-grass">{result.blocks.toLocaleString()}</span>
                </div>
                <div>
                  <span className="text-stone-400">输出体积：</span>
                  <span className="font-semibold">{fmtSize(result.size)}</span>
                </div>
                <div>
                  <span className="text-stone-400">格式：</span>
                  <span className="mc-chip">{result.source_format} → {result.target}</span>
                </div>
              </div>
              <a
                href={`${API}/download/${result.id}/${encodeURIComponent(result.filename)}`}
                className="mc-btn mc-btn-primary w-full"
              >
                <Icon name="download" className="w-5 h-5" />
                下载 {result.filename}
              </a>
            </div>
          )}
        </div>
      </section>

      {/* 全功能工具箱 */}
      <section id="toolbox" className="max-w-6xl mx-auto px-5 pb-20 scroll-mt-20">
        <h2 className="text-2xl sm:text-3xl font-bold text-center mb-3">全功能工具箱</h2>
        <p className="text-stone-400 text-center mb-10 max-w-2xl mx-auto">
          除结构转换外，音乐、优化、批量、像素画、加密服务等所有核心功能均已接入，
          点选分类与工具即可在浏览器中使用。
        </p>
        {Object.keys(plugins).length ? (
          <Toolbox plugins={plugins} />
        ) : (
          <div className="mc-panel p-8 text-center text-stone-400">功能列表加载中…</div>
        )}
      </section>

      {/* 支持的格式 */}
      <section id="formats" className="max-w-6xl mx-auto px-5 pb-20 scroll-mt-20">
        <div className="mc-panel p-6 sm:p-8">
          <h2 className="text-2xl font-bold mb-6">支持的格式</h2>
          <div className="grid sm:grid-cols-2 gap-8">
            <div>
              <h3 className="text-stone-400 text-sm mb-3">源格式（上传）</h3>
              <div className="flex flex-wrap gap-2">
                {formats.source.length ? (
                  formats.source.map((s) => (
                    <span key={s.id} className="mc-chip text-grass border-grass/40">{s.id}</span>
                  ))
                ) : (
                  <span className="mc-chip">bdx</span>
                )}
              </div>
            </div>
            <div>
              <h3 className="text-stone-400 text-sm mb-3">目标格式（导出）</h3>
              <div className="flex flex-wrap gap-2">
                {formats.target.length ? (
                  formats.target.map((t) => (
                    <span key={t.id} className="mc-chip">{t.id} <span className="text-stone-500">{t.ext}</span></span>
                  ))
                ) : (
                  <span className="mc-chip">txt</span>
                )}
              </div>
            </div>
          </div>
          <p className="text-stone-500 text-xs mt-6">
            解析使用项目内置的真实转换引擎（BDXConverter / nbtlib），与桌面版一致。
          </p>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="border-t border-panel-border">
        <div className="max-w-6xl mx-auto px-5 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-sm text-stone-400">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-grass grid place-items-center">
              <span className="w-2.5 h-2.5 bg-[#0e1116]" />
            </div>
            我的世界格式转换器 · 在线版
          </div>
          <div>基于 React + FastAPI · 复用核心转换引擎</div>
        </div>
      </footer>
    </div>
  )
}
