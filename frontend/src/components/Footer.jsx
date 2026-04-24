import { Link } from "react-router-dom";

function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-6 py-8 text-sm text-slate-500 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-sm font-semibold text-slate-900">AI Intelligence Hub</span>
          <span>Daily AI news, research, and retrieval grounded chat.</span>
        </div>
        <div className="flex flex-wrap gap-5">
          <Link className="transition-colors hover:text-blue-600" to="/privacy">Privacy Policy</Link>
          <Link className="transition-colors hover:text-blue-600" to="/terms">Terms of Service</Link>
          <Link className="transition-colors hover:text-blue-600" to="/help">Help Center</Link>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
