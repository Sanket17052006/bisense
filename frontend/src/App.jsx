import React, { useEffect, useState, useRef, useCallback } from "react";

import {
  Routes,
  Route,
  NavLink,
  useLocation,
  useNavigate
} from "react-router-dom";

import {
  Activity,
  ArrowRight,
  Award,
  BarChart3,
  Bell,
  Bot,
  Building2,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  FileText,
  FlaskConical,
  Gem,
  Globe2,
  Grid2X2,
  History as HistoryIcon,
  Home,
  Landmark,
  Layers3,
  LogOut,
  Menu,
  Mic,
  Moon,
  PackageSearch,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  Sparkles,
  Sun,
  Scale,
  UploadCloud,
  X
} from "lucide-react";

import { AuthProvider, useAuth } from "./context/AuthContext";
import { ProtectedRoute, PublicRoute } from "./components/ProtectedRoute";
import { Login, Register } from "./pages/Auth";
import { api } from "./services/api";
import "./styles.css";

/* =========================================================
   SIDEBAR NAVIGATION
========================================================= */

const nav = [
  { to: "/", label: "Dashboard", icon: Home },
  { to: "/standards", label: "Standards", icon: Search },
  { to: "/copilot", label: "AI Copilot", icon: Bot },
  { to: "/analyzer", label: "Product Analyzer", icon: PackageSearch },
  { to: "/certification", label: "Certification", icon: ShieldCheck },
  { to: "/compliance", label: "Compliance", icon: ClipboardCheck },
  { to: "/compare", label: "Compare", icon: Scale },
  { to: "/laboratories", label: "Laboratories", icon: FlaskConical },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/history", label: "History", icon: HistoryIcon }
];

/* =========================================================
   MAIN LAYOUT
========================================================= */

function Layout({ children, dark, setDark }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobile, setMobile] = useState(false);
  const { user, logout } = useAuth();

  const location = useLocation();
  const navigate = useNavigate();

  const title =
    nav.find((item) => item.to === location.pathname)?.label || "BISense";

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className={dark ? "app dark" : "app"}>
      {/* SIDEBAR */}
      <aside
        className={
          (collapsed ? "sidebar collapsed" : "sidebar") +
          (mobile ? " mobile-open" : "")
        }
      >
        <div className="brand">
          <div className="brand-mark">B</div>
          {!collapsed && (
            <div>
              <b>BISense</b>
              <span>Standards Intelligence</span>
            </div>
          )}
          <button className="icon-btn hide-mobile" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
          </button>
        </div>

        <div className="nav-label">{!collapsed && "WORKSPACE"}</div>

        <nav>
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobile(false)}
              className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
              title={collapsed ? label : ""}
            >
              <Icon />
              <span>{!collapsed && label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="nav-bottom">
          <NavLink to="/settings" className="nav-item">
            <SettingsIcon />
            <span>{!collapsed && "Settings"}</span>
          </NavLink>

          <button className="nav-item" onClick={handleLogout}>
            <LogOut />
            <span>{!collapsed && "Sign out"}</span>
          </button>
        </div>
      </aside>

      {/* MAIN */}
      <main className="main">
        {/* TOPBAR */}
        <header className="topbar">
          <button className="icon-btn menu-btn" onClick={() => setMobile(!mobile)}>
            {mobile ? <X /> : <Menu />}
          </button>

          <div className="crumb">
            <span>Workspace</span>
            <ChevronRight size={14} />
            <b>{title}</b>
          </div>

          <div className="top-actions">
            <button className="icon-btn" onClick={() => setDark(!dark)}>
              {dark ? <Sun /> : <Moon />}
            </button>
            <button className="icon-btn"><Bell /></button>

            <div className="avatar">
              {user?.name?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="user-name">{user?.name || "User"}</div>
          </div>
        </header>

        <section className="page">{children}</section>
      </main>
    </div>
  );
}

/* =========================================================
   COMMON COMPONENTS
========================================================= */

function PageHead({ eyebrow, title, sub, action }) {
  return (
    <div className="page-head">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{sub}</p>
      </div>
      {action}
    </div>
  );
}

function Stat({ icon: Icon, label, value, delta }) {
  return (
    <div className="stat-card">
      <div className="stat-icon"><Icon /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{delta}</small>
      </div>
    </div>
  );
}

function Card({ children, className = "" }) {
  return <div className={`card ${className}`}>{children}</div>;
}

function Badge({ children, tone = "red" }) {
  return <span className={`badge ${tone}`}>{children}</span>;
}

/* =========================================================
   DASHBOARD
========================================================= */

function VoiceMic({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef(null);
  const callbackRef = useRef(onTranscript);

  useEffect(() => { callbackRef.current = onTranscript; }, [onTranscript]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { setSupported(false); return; }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN";
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (e) => { console.error("Speech error:", e.error); setListening(false); };
    recognition.onresult = (e) => {
      let finalText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) finalText += e.results[i][0].transcript;
      }
      if (finalText.trim()) callbackRef.current(finalText.trim());
    };
    recognitionRef.current = recognition;
    return () => { recognition.stop(); recognitionRef.current = null; };
  }, []);

  const toggleListening = () => {
    if (!supported) { alert("Voice recognition not supported. Use Chrome or Edge."); return; }
    const recognition = recognitionRef.current;
    if (!recognition) return;
    if (listening) { recognition.stop(); return; }
    try { recognition.start(); } catch (e) { console.error("Mic error:", e); }
  };

  return (
    <div className="dashboard-mic-wrap">
      <button type="button" className={`dashboard-mic ${listening ? "dashboard-mic-listening" : ""}`} onClick={toggleListening} title={listening ? "Stop listening" : "Speak to BISense AI"}>
        <Mic size={20} />
        {listening && <span className="dashboard-mic-pulse"></span>}
      </button>
      <span className="dashboard-mic-label">{listening ? "Listening..." : "Speak"}</span>
    </div>
  );
}

function Dashboard() {
  const [data, setData] = useState({ standards: "—", searches: "—", checks: "—" });
  const [slide, setSlide] = useState(0);
  const [dashboardQuery, setDashboardQuery] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch(() => {});
    api.health().then((h) => console.log("Backend health:", h)).catch(() => {});
  }, []);

  const slides = [
    { eyebrow: "BIS INTELLIGENCE", title: (<>Understand BIS.<br /><span>Find standards.</span><br />Stay compliant.</>), description: "Explore Indian Standards, certification pathways, testing context and compliance information from one intelligent workspace.", button: "Ask BISense AI", route: "/copilot", icon: Sparkles, badge: "AI-POWERED STANDARDS ASSISTANT" },
    { eyebrow: "STANDARDS DISCOVERY", title: (<>Find the<br />right Indian <span>Standard.</span></>), description: "Search standards using an IS number, product name or keyword and build a clearer standards trail for your product.", button: "Explore Standards", route: "/standards", icon: Search, badge: "KNOW YOUR STANDARD" },
    { eyebrow: "PRODUCT CERTIFICATION", title: (<>From product<br />to <span>certification.</span></>), description: "Understand the certification journey, relevant standards, manufacturing requirements, testing context and application steps.", button: "Explore Certification", route: "/certification", icon: ShieldCheck, badge: "CONFORMITY ASSESSMENT" },
    { eyebrow: "HALLMARKING", title: (<>Understand<br /><span>purity & HUID.</span></>), description: "Explore BIS hallmarking information for precious-metal articles, including purity, fineness and HUID-related information.", button: "Explore Hallmarking", route: "/certification", icon: Gem, badge: "GOLD • SILVER • HUID" },
    { eyebrow: "LABORATORY SERVICES", title: (<>Connect standards<br />with <span>testing.</span></>), description: "Discover testing facilities, BIS laboratories and recognized or empanelled laboratories relevant to Indian Standards.", button: "Find Laboratories", route: "/laboratories", icon: FlaskConical, badge: "TESTING & RECOGNITION" },
    { eyebrow: "COMPLIANCE INTELLIGENCE", title: (<>Turn requirements<br />into a <span>checklist.</span></>), description: "Organize declarations, testing requirements, evidence and compliance actions into a structured workflow.", button: "Open Compliance", route: "/compliance", icon: ClipboardCheck, badge: "COMPLIANCE WORKSPACE" }
  ];

  const current = slides[slide];
  const CurrentIcon = current.icon;

  function nextSlide() { setSlide(p => (p + 1) % slides.length); }
  function previousSlide() { setSlide(p => (p - 1 + slides.length) % slides.length); }

  useEffect(() => {
    const timer = setInterval(nextSlide, 7000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="bis-dashboard">
      <section className="bis-hero">
        <div className="bis-hero-left">
          <div className="bis-pill"><span></span>{current.badge}</div>
          <div key={slide} className="bis-slide-content">
            <div className="bis-eyebrow">{current.eyebrow}</div>
            <h1>{current.title}</h1>
            <p>{current.description}</p>
            <div className="bis-hero-actions">
              <button className="bis-primary" onClick={() => window.location.href = current.route}>
                {current.button} <ArrowRight size={18} />
              </button>
              <button className="bis-secondary" onClick={() => window.location.href = "/standards"}>
                Explore BIS <ChevronRight size={17} />
              </button>
            </div>

            <style>{`
              .dashboard-ai-search { width: 100%; max-width: 720px; margin-top: 24px; display: flex; align-items: center; gap: 10px; padding: 8px 9px 8px 16px; background: rgba(255,255,255,.97); border: 1px solid rgba(181,18,27,.15); border-radius: 18px; box-shadow: 0 15px 40px rgba(23,23,23,.10); transition: .25s ease; }
              .dashboard-ai-search:focus-within { border-color: rgba(181,18,27,.45); box-shadow: 0 18px 45px rgba(181,18,27,.14), 0 0 0 4px rgba(181,18,27,.06); }
              .dashboard-ai-search-icon { display:flex; align-items:center; justify-content:center; color:#b5121b; flex-shrink:0; }
              .dashboard-ai-search input { flex:1; min-width:0; border:0; outline:0; background:transparent; color:#171717; font-size:14px; font-weight:500; }
              .dashboard-ai-search input::placeholder { color:#8a8a8a; }
              .dashboard-ai-search .bisense-mic-wrap { position:relative; flex-shrink:0; }
              .dashboard-ai-search .bisense-mic-button { width:42px; height:42px; display:flex; align-items:center; justify-content:center; border-radius:12px; border:1px solid rgba(181,18,27,.15); background:rgba(181,18,27,.07); color:#b5121b; cursor:pointer; transition:.2s ease; }
              .dashboard-ai-search .bisense-mic-button:hover { background:#b5121b; color:white; transform:translateY(-2px); box-shadow:0 8px 20px rgba(181,18,27,.25); }
              .dashboard-ai-search .bisense-mic-button.listening { background:#b5121b; color:white; animation:dashboardMicPulse 1.4s infinite; }
              .dashboard-ai-search-btn { height:42px; display:flex; align-items:center; justify-content:center; gap:6px; padding:0 15px; border:0; border-radius:12px; background:#b5121b; color:#fff; font-size:13px; font-weight:700; cursor:pointer; transition:.2s ease; flex-shrink:0; }
              .dashboard-ai-search-btn:hover { transform:translateY(-2px); box-shadow:0 8px 20px rgba(181,18,27,.25); }
              @keyframes dashboardMicPulse { 0% { box-shadow:0 0 0 0 rgba(181,18,27,.40); } 70% { box-shadow:0 0 0 12px rgba(181,18,27,0); } 100% { box-shadow:0 0 0 0 rgba(181,18,27,0); } }
              .app.dark .dashboard-ai-search { background:#1b1b1f; border-color:rgba(255,255,255,.10); }
              .app.dark .dashboard-ai-search input { color:#fff; }
              .app.dark .dashboard-ai-search input::placeholder { color:#999; }
              .app.dark .dashboard-ai-search-icon { color:#ff737b; }
              .app.dark .dashboard-ai-search .bisense-mic-button { background:rgba(181,18,27,.15); color:#ff737b; border-color:rgba(255,255,255,.08); }
            `}</style>

            <div className="dashboard-ai-search">
              <div className="dashboard-ai-search-icon"><Search size={19} /></div>
              <input type="text" value={dashboardQuery} onChange={(e) => setDashboardQuery(e.target.value)} placeholder="Ask about BIS standards, certification, testing..." onKeyDown={(e) => { if (e.key === "Enter") { const q = dashboardQuery.trim(); window.location.href = q ? `/copilot?query=${encodeURIComponent(q)}` : "/copilot"; } }} />
              <VoiceMic onTranscript={(t) => setDashboardQuery(p => p.trim() ? `${p.trim()} ${t}` : t)} />
              <button type="button" className="dashboard-ai-search-btn" onClick={() => { const q = dashboardQuery.trim(); window.location.href = q ? `/copilot?query=${encodeURIComponent(q)}` : "/copilot"; }}>Ask <ArrowRight size={16} /></button>
            </div>
          </div>

          <div className="bis-mini-stats">
            <div><strong>{data.standards}</strong><span>Standards indexed</span></div>
            <div><strong>{data.searches}</strong><span>Searches</span></div>
            <div><strong>{data.checks}</strong><span>Compliance checks</span></div>
          </div>
        </div>

        <div className="bis-hero-right">
          <div className="bis-orbit orbit-one"></div>
          <div className="bis-orbit orbit-two"></div>
          <div key={`visual-${slide}`} className="bis-visual-card">
            <div className="bis-visual-top">
              <div className="bis-visual-icon"><CurrentIcon /></div>
              <span>BISENSE</span>
              <Badge tone="green">LIVE</Badge>
            </div>
            <div className="bis-visual-title">
              {slide === 0 && "Ask Manak Mitra"}
              {slide === 1 && "Know Your Standard"}
              {slide === 2 && "Certification Journey"}
              {slide === 3 && "Hallmark Intelligence"}
              {slide === 4 && "Testing Network"}
              {slide === 5 && "Compliance Trail"}
            </div>
            <div className="bis-visual-lines">
              <div className="bis-line active"><span></span><div><b>{slide === 0 ? "Ask a BIS question" : slide === 1 ? "Search by IS number" : slide === 2 ? "Identify applicable standard" : slide === 3 ? "Check purity information" : slide === 4 ? "Find testing capability" : "Create requirements"}</b><small>BISense intelligence</small></div></div>
              <div className="bis-line"><span></span><div><b>Relevant information</b><small>Standards • Services • Evidence</small></div></div>
              <div className="bis-line"><span></span><div><b>Actionable next step</b><small>Build your workflow</small></div></div>
            </div>
            <div className="bis-visual-bottom">
              <span><CheckCircle2 size={15} /> Source-aware workspace</span>
              <span>{String(slide + 1).padStart(2, "0")}/{String(slides.length).padStart(2, "0")}</span>
            </div>
          </div>
        </div>

        <div className="bis-slider-controls">
          <button onClick={previousSlide} aria-label="Previous slide"><ChevronLeft /></button>
          <div className="bis-dots">
            {slides.map((_, i) => <button key={i} className={i === slide ? "active" : ""} onClick={() => setSlide(i)} aria-label={`Go to slide ${i + 1}`} />)}
          </div>
          <button onClick={nextSlide} aria-label="Next slide"><ChevronRight /></button>
        </div>
      </section>

      <section className="bis-section">
        <div className="bis-section-head">
          <div>
            <div className="bis-section-label">ABOUT BIS</div>
            <h2>One workspace for <span>standards intelligence.</span></h2>
          </div>
          <p>BIS works across standardization, certification, hallmarking, laboratory services and consumer-facing quality activities.</p>
        </div>
        <div className="bis-service-grid">
          <div className="bis-service-card"><div className="service-number">01</div><div className="service-icon"><Layers3 /></div><h3>Indian Standards</h3><p>Discover standards by product, IS number or keyword.</p><button onClick={() => window.location.href = "/standards"}>Explore <ArrowRight size={15} /></button></div>
          <div className="bis-service-card"><div className="service-number">02</div><div className="service-icon"><ShieldCheck /></div><h3>Certification</h3><p>Understand product certification and conformity pathways.</p><button onClick={() => window.location.href = "/certification"}>Explore <ArrowRight size={15} /></button></div>
          <div className="bis-service-card"><div className="service-number">03</div><div className="service-icon"><Gem /></div><h3>Hallmarking</h3><p>Explore precious-metal hallmarking and HUID information.</p><button onClick={() => window.location.href = "/certification"}>Explore <ArrowRight size={15} /></button></div>
          <div className="bis-service-card"><div className="service-number">04</div><div className="service-icon"><FlaskConical /></div><h3>Laboratory Services</h3><p>Connect standards with testing facilities and laboratory information.</p><button onClick={() => window.location.href = "/laboratories"}>Explore <ArrowRight size={15} /></button></div>
        </div>
      </section>

      <section className="bis-feature-panel">
        <div className="bis-feature-copy">
          <div className="bis-section-label">KNOW YOUR STANDARD</div>
          <h2>Start with a product.<br />End with a <span>standards trail.</span></h2>
          <p>Search by an Indian Standard number or keyword and bring together the information needed to understand that standard.</p>
          <button className="bis-primary" onClick={() => window.location.href = "/standards"}>Search Standards <ArrowRight size={17} /></button>
        </div>
        <div className="bis-trail-card">
          <div className="trail-head"><span>BISENSE</span><Search size={18} /></div>
          <div className="trail-search"><Search size={18} /><span>packaged drinking water</span><button>Search</button></div>
          <div className="trail-result"><Badge>IS STANDARD</Badge><h3>Relevant Indian Standard</h3><p>Standard information, amendments, testing context and related resources.</p><div className="trail-meta"><span><CheckCircle2 size={14} /> Standard context</span><span><FileText size={14} /> Documents</span><span><FlaskConical size={14} /> Laboratories</span></div></div>
        </div>
      </section>

      <section className="bis-section">
        <div className="bis-section-head">
          <div><div className="bis-section-label">CERTIFICATION</div><h2>From standard <span>to licence.</span></h2></div>
          <p>BIS guidance describes identifying the applicable Indian Standard, preparing manufacturing and quality capabilities, assessment and conformity testing as part of the certification journey.</p>
        </div>
        <div className="journey">
          <div className="journey-line"></div>
          <div className="journey-step"><span>01</span><Search /><h3>Identify</h3><p>Find the applicable Indian Standard.</p></div>
          <div className="journey-step"><span>02</span><FileText /><h3>Prepare</h3><p>Review infrastructure, process controls and testing capabilities.</p></div>
          <div className="journey-step"><span>03</span><FlaskConical /><h3>Test</h3><p>Establish conformity through applicable testing arrangements.</p></div>
          <div className="journey-step"><span>04</span><ShieldCheck /><h3>Certify</h3><p>Move through the applicable BIS process.</p></div>
        </div>
      </section>

      <section className="bis-dual-grid">
        <div className="bis-dark-card"><div className="bis-section-label">HALLMARKING</div><Gem /><h2>Purity you<br />can understand.</h2><p>BIS hallmarking information covers precious-metal articles. Current BIS information identifies gold and silver within the hallmarking framework.</p><div className="gold-points"><span><CheckCircle2 /> BIS Standard Mark</span><span><CheckCircle2 /> Purity & fineness</span><span><CheckCircle2 /> HUID</span></div><button onClick={() => window.location.href = "/certification"}>Explore Hallmarking <ArrowRight size={16} /></button></div>
        <div className="bis-light-card"><div className="bis-section-label">LABORATORY SERVICES</div><FlaskConical /><h2>Testing is part<br />of the <span>standards trail.</span></h2><p>BIS provides laboratory services and maintains information about recognized and empanelled laboratories.</p><div className="lab-stat"><strong>8</strong><span>BIS laboratories</span></div><button onClick={() => window.location.href = "/laboratories"}>Find Laboratories <ArrowRight size={16} /></button></div>
      </section>

      <section className="bis-compliance">
        <div><div className="bis-section-label">BISENSE COMPLIANCE</div><h2>Information is useful.<br /><span>Action is better.</span></h2><p>Convert standards and certification information into a structured compliance workflow.</p></div>
        <div className="compliance-actions">
          <button className="bis-primary" onClick={() => window.location.href = "/compliance"}>Open Compliance <ArrowRight size={18} /></button>
          <button className="bis-outline-white" onClick={() => window.location.href = "/copilot"}>Ask BISense AI <Sparkles size={17} /></button>
        </div>
      </section>

      <section className="bis-section">
        <div className="bis-section-label">BISENSE WORKSPACE</div>
        <h2 className="bis-final-title">Everything starts <span>with a question.</span></h2>
        <div className="bis-quick-grid">
          <QuickDashboardCard icon={Bot} title="Ask BISense" text="Ask questions about standards and BIS services." route="/copilot" />
          <QuickDashboardCard icon={PackageSearch} title="Analyze Product" text="Upload a product image for a standards-oriented review." route="/analyzer" />
          <QuickDashboardCard icon={Scale} title="Compare Standards" text="Put standards side-by-side and inspect context." route="/compare" />
          <QuickDashboardCard icon={FileText} title="Reports" text="Keep generated analysis and compliance outputs together." route="/reports" />
        </div>
      </section>
    </div>
  );
}

function QuickDashboardCard({ icon: Icon, title, text, route }) {
  return (
    <button className="bis-quick-card" onClick={() => window.location.href = route}>
      <div className="bis-quick-icon"><Icon /></div>
      <div><h3>{title}</h3><p>{text}</p></div>
      <ArrowRight className="quick-arrow" size={18} />
    </button>
  );
}

/* =========================================================
   STANDARDS
========================================================= */

function Standards() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [items, setItems] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const [selectedStandard, setSelectedStandard] = useState(null);
  const limit = 20;

  useEffect(() => {
    api.standardCategories().then(setCategories).catch(() => setCategories([]));
  }, []);

  const fetchStandards = useCallback(async () => {
    setLoading(true);
    try {
      const params = { skip: page * limit, limit };
      if (q) params.q = q;
      if (category) params.category = category;
      if (status) params.status = status;
      const data = await api.standards(params);
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (e) {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [q, category, status, page]);

  useEffect(() => { fetchStandards(); }, [fetchStandards]);

  const handleView = async (std) => {
    try {
      const detail = await api.standardDetail(std.id);
      setSelectedStandard(detail);
    } catch (e) {
      setSelectedStandard({ ...std, clauses: [], revisions: [] });
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <>
      <PageHead eyebrow="DISCOVER" title="Standards Explorer" sub="Search by IS number, product, title, category or keyword." />
      <Card className="search-card">
        <div className="search-box">
          <Search />
          <input value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === "Enter" && setPage(0)} placeholder="e.g. packaged drinking water, IS 14543..." />
          <button className="primary" onClick={() => setPage(0)}>Search</button>
        </div>
        <div className="filter-row" style={{ gap: 10, flexWrap: "wrap" }}>
          <select value={category} onChange={e => { setCategory(e.target.value); setPage(0); }} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e0ddd8", background: "#fff", fontSize: 13 }}>
            <option value="">All categories</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={status} onChange={e => { setStatus(e.target.value); setPage(0); }} style={{ padding: "8px 12px", borderRadius: 8, border: "1px solid #e0ddd8", background: "#fff", fontSize: 13 }}>
            <option value="">All statuses</option>
            <option value="active">Active</option>
            <option value="withdrawn">Withdrawn</option>
            <option value="under_revision">Under Revision</option>
          </select>
        </div>
      </Card>
      <div className="section-label">{total} result{total !== 1 ? "s" : ""}{q && ` for "${q}"`}{category && ` in ${category}`}{status && ` (${status})`}</div>
      <div className="result-list">
        {loading ? (
          <div className="loading" style={{ textAlign: "center", padding: 40, color: "#999" }}>Loading standards...</div>
        ) : items.length === 0 ? (
          <div className="empty" style={{ padding: 40, textAlign: "center" }}>
            <Search style={{ width: 48, height: 48, margin: "0 auto 16px", color: "#ddd" }} />
            <h3>No standards found</h3>
            <p>Try adjusting your search or filters.</p>
          </div>
        ) : (
          items.map(item => (
            <Card key={item.id} className="result-card" onClick={() => handleView(item)} style={{ cursor: "pointer" }}>
              <div>
                <Badge>{item.is_number}</Badge>
                <h3>{item.title}</h3>
                <p>{item.description || item.boundary || "No description available"}</p>
                <div className="meta-row">
                  <span>{item.category || "Uncategorized"}</span>
                  <span>•</span>
                  <span><Badge tone={item.status === "active" ? "green" : "neutral"}>{item.status}</Badge></span>
                  {item.year && <>• {item.year}</>}
                  {item.certification_type && <>• {item.certification_type}</>}
                  {item.ics_code && <>• ICS: {item.ics_code}</>}
                </div>
              </div>
              <div className="result-actions"><button className="secondary" onClick={e => { e.stopPropagation(); handleView(item); }}>View Details</button><button className="ghost" onClick={e => e.stopPropagation()}>Compare</button></div>
            </Card>
          ))
        )}
      </div>
      {totalPages > 1 && (
        <div className="pagination" style={{ display: "flex", justifyContent: "center", gap: 8, marginTop: 24 }}>
          <button className="secondary" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}><ChevronLeft size={16} /></button>
          {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
            let p = i;
            if (totalPages > 5) {
              if (page > 1 && page < totalPages - 2) p = page - 2 + i;
              else if (page >= totalPages - 2) p = totalPages - 5 + i;
            }
            return <button key={p} className={p === page ? "primary" : "secondary"} style={{ minWidth: 40 }} onClick={() => setPage(p)}>{p + 1}</button>;
          })}
          <button className="secondary" onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}><ChevronRight size={16} /></button>
        </div>
      )}

      {selectedStandard && (
        <div className="modal-overlay" onClick={() => setSelectedStandard(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <Badge>{selectedStandard.is_number}</Badge>
                <h2 style={{ margin: "8px 0 0" }}>{selectedStandard.title}</h2>
              </div>
              <button className="icon-btn" onClick={() => setSelectedStandard(null)}><X size={20} /></button>
            </div>
            <div className="modal-body">
              <div className="modal-meta">
                {selectedStandard.category && <span><b>Category:</b> {selectedStandard.category}</span>}
                {selectedStandard.year && <span><b>Year:</b> {selectedStandard.year}</span>}
                {selectedStandard.status && <span><b>Status:</b> <Badge tone={selectedStandard.status === "active" ? "green" : "neutral"}>{selectedStandard.status}</Badge></span>}
                {selectedStandard.certification_type && <span><b>Certification:</b> {selectedStandard.certification_type}</span>}
                {selectedStandard.ics_code && <span><b>ICS Code:</b> {selectedStandard.ics_code}</span>}
              </div>
              {selectedStandard.boundary && <div className="modal-section"><h4>Scope</h4><p>{selectedStandard.boundary}</p></div>}
              {selectedStandard.description && <div className="modal-section"><h4>Description</h4><p>{selectedStandard.description}</p></div>}
              {selectedStandard.clauses && selectedStandard.clauses.length > 0 && (
                <div className="modal-section">
                  <h4>Clauses ({selectedStandard.clauses.length})</h4>
                  <div className="clauses-list">
                    {selectedStandard.clauses.map(c => (
                      <div key={c.id} className="clause-item">
                        <div className="clause-ref">{c.clause_ref || `Clause ${c.id.slice(0,4)}`}</div>
                        <div>
                          {c.title && <b>{c.title}</b>}
                          <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>{c.content?.slice(0, 200)}...</p>
                          {c.page && <small>Page {c.page}</small>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {selectedStandard.revisions && selectedStandard.revisions.length > 0 && (
                <div className="modal-section">
                  <h4>Revisions</h4>
                  <div className="revisions-list">
                    {selectedStandard.revisions.map(r => (
                      <div key={r.id} className="revision-item">
                        <b>{r.revision_year}</b>{r.amendment && ` — Amendment: ${r.amendment}`}
                        {r.effective_from && <small>Effective: {new Date(r.effective_from).toLocaleDateString()}</small>}
                        {r.summary && <p style={{ margin: "4px 0 0", color: "#666", fontSize: 13 }}>{r.summary}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="primary" onClick={() => { setSelectedStandard(null); window.location.href = `/copilot?query=${encodeURIComponent("Tell me about " + selectedStandard.is_number)}`; }}>
                <Bot size={16} /> Ask BISense about this standard
              </button>
              <button className="secondary" onClick={() => setSelectedStandard(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* =========================================================
   AI COPILOT
========================================================= */

function Copilot() {
  const initialQuery = new URLSearchParams(window.location.search).get("query") || "";
  const [messages, setMessages] = useState([{ role: "assistant", text: "Hi! I'm BISense AI. Ask me about Indian Standards, BIS certification, testing, hallmarking, packaged commodities or related services." }]);
  const [input, setInput] = useState(initialQuery);
  const [busy, setBusy] = useState(false);

  async function send() {
    if (!input.trim() || busy) return;
    const text = input.trim();
    setInput("");
    setMessages(m => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const response = await api.chat(text);
      setMessages(m => [...m, { role: "assistant", text: response.reply || response.answer || "I received the request. Please verify the returned BIS source details." }]);
    } catch (err) {
      setMessages(m => [...m, { role: "assistant", text: `Error: ${err.message || "Failed to connect to backend"}` }]);
    } finally { setBusy(false); }
  }

  return (
    <>
      <PageHead eyebrow="AI ASSISTANT" title="BISense Copilot" sub="Ask questions about Indian Standards and BIS services." />
      <div className="copilot-layout">
        <Card className="chat-card">
          <div className="chat-head">
            <div className="ai-avatar"><Bot /></div>
            <div><b>BISense AI</b><span>Standards intelligence assistant</span></div>
            <Badge tone="green">Online</Badge>
          </div>
          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`msg ${msg.role}`}>
                <div className="msg-avatar">{msg.role === "assistant" ? "B" : "U"}</div>
                <div className="bubble"><span>{msg.text}</span>{msg.role === "assistant" && <small>Source-aware response • verify against official BIS sources</small>}</div>
              </div>
            ))}
          </div>
          <div className="suggestions">
            {["Find standards for packaged water", "What is BIS certification?", "How do I compare two standards?"].map(s => <button key={s} onClick={() => setInput(s)}>{s}</button>)}
          </div>
          <div className="composer">
            <button className="icon-btn" type="button" title="Attach a file"><UploadCloud /></button>
            <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask BISense anything..." />
            <VoiceMic onTranscript={t => setInput(p => p.trim() ? `${p.trim()} ${t}` : t)} />
            <button className="send" onClick={send} type="button">{busy ? "…" : "➤"}</button>
          </div>
        </Card>
        <Card className="source-panel">
          <div className="card-title"><span>How BISense helps</span><Sparkles size={18} /></div>
          <div className="feature"><ShieldCheck /><div><b>Evidence first</b><span>Keep source context alongside answers.</span></div></div>
          <div className="feature"><Search /><div><b>Standards discovery</b><span>Search by product, number or concept.</span></div></div>
          <div className="feature"><ClipboardCheck /><div><b>Actionable next steps</b><span>Turn information into a checklist.</span></div></div>
        </Card>
      </div>
    </>
  );
}

/* =========================================================
   PRODUCT ANALYZER
========================================================= */

function Analyzer() {
  const [file, setFile] = useState(null);
  return (
    <>
      <PageHead eyebrow="ANALYZE" title="Product Analyzer" sub="Upload a product image to start a standards and label review." />
      <div className="analyzer-grid">
        <Card className="upload-card">
          <div className="upload-icon"><PackageSearch /></div>
          <h2>Drop product image</h2>
          <p>PNG, JPG or WEBP. Use a clear photo of the label or product packaging.</p>
          <input id="file" type="file" accept="image/*" onChange={e => setFile(e.target.files?.[0])} />
          <label htmlFor="file" className="primary upload-btn"><UploadCloud />{file ? file.name : "Choose image"}</label>
          <button className="secondary full" onClick={() => alert("Connect this action to your backend product-analysis endpoint.")}>Analyze product</button>
        </Card>
        <Card>
          <div className="card-title"><span>Analysis workflow</span><Activity size={18} /></div>
          {["Image & label extraction", "Potential standard matching", "Certification considerations", "Compliance checklist"].map((item, i) => (
            <div key={item} className="step"><span>{i + 1}</span><div><b>{item}</b><small>{i === 0 ? "OCR / vision input" : i === 1 ? "Relevant IS references" : i === 2 ? "Scheme and licensing context" : "Trackable requirements"}</small></div></div>
          ))}
        </Card>
      </div>
    </>
  );
}

/* =========================================================
   SIMPLE FEATURE COMPONENT
========================================================= */

function SimpleFeature({ type, title, sub, icon: Icon, items }) {
  return (
    <>
      <PageHead eyebrow={type.toUpperCase()} title={title} sub={sub} />
      <div className="feature-grid">
        {items.map((item, i) => (
          <Card key={i} className="feature-card">
            <div className="large-icon"><Icon /></div>
            <Badge tone={i % 2 ? "neutral" : "red"}>{item.tag}</Badge>
            <h3>{item.title}</h3>
            <p>{item.desc}</p>
            <button className="text-btn">Open workflow <ArrowRight size={14} /></button>
          </Card>
        ))}
      </div>
    </>
  );
}

/* =========================================================
   COMPLIANCE
========================================================= */

function Compliance() {
  return (
    <SimpleFeature type="WORKFLOW" title="Compliance Assistant" sub="Build a structured checklist from available standard information." icon={ClipboardCheck} items={[
      { tag: "CHECKLIST", title: "Product requirements", desc: "Track declarations, tests and evidence against a selected standard." },
      { tag: "EVIDENCE", title: "Evidence vault", desc: "Keep supporting files and notes attached to each requirement." },
      { tag: "REPORT", title: "Compliance report", desc: "Prepare a clean review summary for internal verification." }
    ]} />
  );
}

/* =========================================================
   CERTIFICATION
========================================================= */

function Certification() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isNumber, setIsNumber] = useState("");

  const fetchRoadmap = async () => {
    if (!isNumber.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.certification({ is_number: isNumber.trim() });
      setData(result);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  if (!data && !error && !isNumber) {
    return (
      <>
        <PageHead eyebrow="BIS SERVICES" title="Certification Advisor" sub="Navigate certification concepts, schemes and preparation steps." />
        <div className="certification-search">
          <input
            value={isNumber}
            onChange={e => setIsNumber(e.target.value)}
            onKeyDown={e => e.key === "Enter" && fetchRoadmap()}
            placeholder="Enter IS number (e.g., IS 302, IS 14543)"
          />
          <button className="primary" onClick={fetchRoadmap} disabled={loading || !isNumber.trim()}>
            {loading ? "Loading…" : "Get Roadmap"}
          </button>
          <Badge tone="green">Live Data</Badge>
        </div>
        <div className="roadmap-empty">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <h3>Enter an IS number to get a certification roadmap</h3>
          <p>Example: IS 302, IS 14543, IS 16000</p>
        </div>
      </>
    );
  }

  return (
    <>
      <PageHead eyebrow="BIS SERVICES" title="Certification Advisor" sub="Navigate certification concepts, schemes and preparation steps." />
      <div className="certification-search">
        <input
          value={isNumber}
          onChange={e => setIsNumber(e.target.value)}
          onKeyDown={e => e.key === "Enter" && fetchRoadmap()}
          placeholder="Enter IS number (e.g., IS 302, IS 14543)"
        />
        <button className="primary" onClick={fetchRoadmap} disabled={loading || !isNumber.trim()}>
          {loading ? "Loading…" : "Get Roadmap"}
        </button>
        <Badge tone="green">Live Data</Badge>
      </div>
      {error && (
        <div className="roadmap-error">
          <strong>Error:</strong> {error.message || error}
        </div>
      )}
      {data && (
        <div className="certification-roadmap">
          <div className="roadmap-header">
            <h3>{data.title}</h3>
            <span className="scheme-badge">{data.scheme} ({data.scheme_type})</span>
            <div className="standard-ref"><b>Standard:</b> {data.is_number || "Not specified"}</div>
          </div>
          <div className="roadmap-steps">
            <h3>Certification Steps</h3>
            <ol>
              {data.steps.map((s, i) => (
                <li key={i}>
                  <span className="step-number">{i + 1}</span>
                  <div className="step-content">
                    <span className="step-title">{s.title}</span>
                    {s.detail && <span className="step-detail">{s.detail}</span>}
                  </div>
                </li>
              ))}
            </ol>
          </div>
          {data.documents_required?.length && (
            <div className="roadmap-documents">
              <h3>Documents Required</h3>
              <ul>
                {data.documents_required.map((d, i) => <li key={i}>{d}</li>)}
              </ul>
            </div>
          )}
          {data.disclaimer && (
            <div className="roadmap-disclaimer">{data.disclaimer}</div>
          )}
        </div>
      )}
    </>
  );
}

/* =========================================================
   LABORATORIES
========================================================= */

function Laboratories() {
  return (
    <SimpleFeature type="BIS SERVICES" title="Laboratory Finder" sub="Discover laboratories and testing context by standard or product." icon={FlaskConical} items={[
      { tag: "SEARCH", title: "Find a laboratory", desc: "Search by IS number, product or location when your backend is connected." },
      { tag: "CAPABILITY", title: "Testing capability", desc: "Review supported standards and available testing context." },
      { tag: "DETAILS", title: "Laboratory profile", desc: "Keep contact and service information in one place." }
    ]} />
  );
}

/* =========================================================
   COMPARE
========================================================= */

function Compare() {
  return (
    <>
      <PageHead eyebrow="ANALYZE" title="Compare Standards" sub="Put two standards side-by-side and inspect scope, requirements and testing context." />
      <Card>
        <div className="compare-select">
          <div><label>Standard A</label><input placeholder="Search IS number or title" /></div>
          <div className="vs">VS</div>
          <div><label>Standard B</label><input placeholder="Search IS number or title" /></div>
        </div>
        <div className="comparison">
          <div><b>Scope</b><span>Choose a standard to load scope.</span></div>
          <div><b>Requirements</b><span>Requirements will appear here.</span></div>
          <div><b>Testing</b><span>Testing information will appear here.</span></div>
          <div><b>Certification</b><span>Certification context will appear here.</span></div>
        </div>
      </Card>
    </>
  );
}

/* =========================================================
   REPORTS
========================================================= */

function Reports() {
  return (
    <>
      <PageHead eyebrow="OUTPUTS" title="Reports" sub="Keep generated analysis and compliance reports together." />
      <Card><div className="empty"><FileText /><h3>No reports yet</h3><p>Generate a report from a completed workflow and it will appear here.</p><button className="primary">Create report</button></div></Card>
    </>
  );
}

/* =========================================================
   HISTORY
========================================================= */

function History() {
  const [history, setHistory] = useState([]);
  useEffect(() => { api.history().then(setHistory).catch(() => setHistory([])); }, []);
  return (
    <>
      <PageHead eyebrow="ACTIVITY" title="History" sub="A timeline of your searches, analyses and generated outputs." />
      <Card>
        {history.length === 0 ? (
          <div className="empty"><Clock3 /><h3>No history yet</h3><p>Your activity will appear here once you start using BISense.</p></div>
        ) : (
          history.map((item, i) => (
            <div key={i} className="history-row"><Clock3 /><div><b>{item.title || item.query}</b><span>{item.meta || item.intent}</span></div><small>{item.time || item.created_at}</small></div>
          ))
        )}
      </Card>
    </>
  );
}

/* =========================================================
   PROFILE
========================================================= */

function Profile() {
  const { user } = useAuth();
  return (
    <Card>
      <div className="profile">
        <div className="profile-avatar">{user?.name?.[0]?.toUpperCase() || "U"}</div>
        <h2>{user?.name || "User"}</h2>
        <p>{user?.email || "BISense workspace account"}</p>
        <Badge tone="green">Active</Badge>
      </div>
    </Card>
  );
}

/* =========================================================
   SETTINGS
========================================================= */

function Settings() {
  const { user } = useAuth();
  const settings = [
    { title: "Appearance", description: "Light or dark interface" },
    { title: "Notifications", description: "Activity and report alerts" },
    { title: "AI response preferences", description: "Response detail and source display" },
    { title: "Data & privacy", description: "Workspace data controls" }
  ];
  return (
    <>
      <PageHead eyebrow="PREFERENCES" title="Settings" sub="Control your BISense workspace experience." />
      <Card>
        {settings.map(s => (
          <div key={s.title} className="setting-row">
            <div><b>{s.title}</b><span>{s.description}</span></div>
            <button className="secondary">Configure</button>
          </div>
        ))}
      </Card>
      <Card style={{ marginTop: 20 }}>
        <div className="setting-row"><div><b>Account</b><span>{user?.email}</span></div><button className="secondary">Manage</button></div>
      </Card>
    </>
  );
}

/* =========================================================
   APP ROOT
========================================================= */

function AppRoutes() {
  const { loading } = useAuth();

  if (loading) {
    return <div className="loading-screen"><div className="loader"></div></div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route path="*" element={<ProtectedRoute><LayoutApp /></ProtectedRoute>} />
    </Routes>
  );
}

function LayoutApp() {
  const [dark, setDark] = useState(localStorage.getItem("bis-dark") === "1");
  useEffect(() => { localStorage.setItem("bis-dark", dark ? "1" : "0"); document.documentElement.classList.toggle("dark", dark); }, [dark]);

  return (
    <Layout dark={dark} setDark={setDark}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/standards" element={<Standards />} />
        <Route path="/copilot" element={<Copilot />} />
        <Route path="/analyzer" element={<Analyzer />} />
        <Route path="/certification" element={<Certification />} />
        <Route path="/compliance" element={<Compliance />} />
        <Route path="/compare" element={<Compare />} />
        <Route path="/laboratories" element={<Laboratories />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/history" element={<History />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}