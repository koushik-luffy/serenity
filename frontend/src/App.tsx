import { useEffect, useState } from "react";
import { ArrowRightLeft, HeartHandshake, ShieldCheck } from "lucide-react";

import CounselorDashboard from "@/pages/CounselorDashboard";
import UserDashboard from "@/pages/UserDashboard";

type PageId = "user" | "counselor";

function getPageFromHash(): PageId {
  const hash = window.location.hash.replace("#", "").trim().toLowerCase();
  return hash === "counselor" ? "counselor" : "user";
}

export default function App() {
  const [page, setPage] = useState<PageId>(() => getPageFromHash());

  useEffect(() => {
    const handleHashChange = () => setPage(getPageFromHash());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  function navigate(nextPage: PageId) {
    window.location.hash = nextPage;
    setPage(nextPage);
  }

  return (
    <div className="relative">
      <div className="fixed left-1/2 top-4 z-50 flex -translate-x-1/2 items-center gap-2 rounded-full border border-white/80 bg-white/80 px-3 py-2 shadow-soft backdrop-blur-xl">
        <button
          onClick={() => navigate("user")}
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
            page === "user" ? "bg-[#14182c] text-white" : "text-slate-600"
          }`}
        >
          <HeartHandshake className="h-4 w-4" />
          User dashboard
        </button>
        <button
          onClick={() => navigate("counselor")}
          className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
            page === "counselor" ? "bg-[#14182c] text-white" : "text-slate-600"
          }`}
        >
          <ShieldCheck className="h-4 w-4" />
          Counselor dashboard
        </button>
        <div className="hidden items-center gap-2 pl-2 text-xs text-slate-400 md:flex">
          <ArrowRightLeft className="h-3.5 w-3.5" />
          Hash routes: `#user` and `#counselor`
        </div>
      </div>

      {page === "user" ? <UserDashboard /> : <CounselorDashboard />}
    </div>
  );
}
