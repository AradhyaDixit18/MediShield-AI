import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { ShieldPlus, Code2 } from "lucide-react";
import { useEffect } from "react";

function Navbar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${isActive ? "text-brand-400" : "text-slate-300 hover:text-white"}`;
  return (
    <header className="sticky top-0 z-50 border-b border-white/5 bg-ink-950/70 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="grid h-9 w-9 place-items-center rounded-xl bg-brand-500/15 text-brand-400 ring-1 ring-brand-500/30">
            <ShieldPlus size={20} />
          </div>
          <span className="font-display text-lg font-bold tracking-tight text-white">
            MediShield<span className="text-brand-400"> AI</span>
          </span>
        </Link>
        <div className="flex items-center gap-6">
          <NavLink to="/" end className={linkClass}>Home</NavLink>
          <NavLink to="/report" className={linkClass}>Report</NavLink>
          <NavLink to="/dashboard" className={linkClass}>Dashboard</NavLink>
          <NavLink to="/about" className={linkClass}>About</NavLink>
          <a
            href="https://github.com/AradhyaDixit18/MediShield-AI"
            target="_blank" rel="noreferrer"
            className="hidden items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-sm text-slate-300 transition hover:border-white/25 hover:text-white sm:flex"
          >
            <Code2 size={15} /> Repo
          </a>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/5 py-8">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-5 text-sm text-slate-500 sm:flex-row">
        <p>© {new Date().getFullYear()} MediShield AI · Built by Aradhya Dixit</p>
        <p className="text-xs">For educational use only. Not a medical device.</p>
      </div>
    </footer>
  );
}

export default function App() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
