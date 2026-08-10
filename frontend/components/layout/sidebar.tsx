"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Upload, BarChart3, Briefcase, Circle, History, Star } from "lucide-react";
import { useEffect, useState } from "react";
import { checkHealth } from "@/lib/api";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "Dashboard", href: "/", icon: Home },
  { name: "Results", href: "/results", icon: BarChart3 },
  { name: "History", href: "/history", icon: History },
  { name: "Shortlist", href: "/shortlist", icon: Star },
];

export function Sidebar() {
  const pathname = usePathname();
  const [apiStatus, setApiStatus] = useState<"online" | "offline">("offline");
  const [scoringMode, setScoringMode] = useState<"hybrid" | "rules-only" | "unknown">(
    "unknown"
  );

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const health = await checkHealth();
        setApiStatus(health.status === "healthy" ? "online" : "offline");
        const mlLoaded = health.components?.ml_model_loaded;
        setScoringMode(
          mlLoaded === undefined ? "unknown" : mlLoaded ? "hybrid" : "rules-only"
        );
      } catch {
        setApiStatus("offline");
        setScoringMode("unknown");
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-gradient-to-b from-gray-900 to-gray-800 border-r border-white/10 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center text-2xl shadow-lg shadow-purple-500/30 group-hover:shadow-purple-500/50 transition-all">
            <Briefcase className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold bg-gradient-to-r from-purple-400 to-blue-500 bg-clip-text text-transparent">AI Resume</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 rounded-lg transition-all",
                    isActive
                      ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg shadow-purple-500/30"
                      : "text-gray-400 hover:bg-white/5 hover:text-white"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.name}</span>
                  {isActive && (
                    <Circle className="w-2 h-2 fill-current ml-auto animate-pulse" />
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* API Status */}
      <div className="p-4 border-t border-white/10 space-y-2">
        <div className="flex items-center gap-3 px-4 py-3 bg-white/5 rounded-lg">
          <Circle
            className={cn(
              "w-3 h-3 fill-current",
              apiStatus === "online" ? "text-green-500" : "text-red-500"
            )}
          />
          <div>
            <p className="text-sm font-medium text-white">API Status</p>
            <p className="text-xs text-gray-400 capitalize">{apiStatus}</p>
          </div>
        </div>

        {/* Scoring mode. Rule-based-only means the ML model failed to load and
            the hybrid scoring is not running — previously invisible in the UI. */}
        {apiStatus === "online" && scoringMode !== "unknown" && (
          <div
            className="flex items-center gap-3 px-4 py-3 bg-white/5 rounded-lg"
            title={
              scoringMode === "hybrid"
                ? "Scores combine the ML model with rule-based matching"
                : "ML model not loaded — scores come from rule-based matching only"
            }
          >
            <Circle
              className={cn(
                "w-3 h-3 fill-current",
                scoringMode === "hybrid" ? "text-green-500" : "text-amber-500"
              )}
            />
            <div>
              <p className="text-sm font-medium text-white">Scoring</p>
              <p className="text-xs text-gray-400" aria-live="polite">
                {scoringMode === "hybrid" ? "Hybrid (ML + rules)" : "Rules only"}
              </p>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
