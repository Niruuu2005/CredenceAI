import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ShieldCheck, ShieldAlert, PlusCircle, Trash2, RefreshCw, Loader2 } from "lucide-react";
import { api, Monitor } from "@/lib/api";

export function Monitors() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  useEffect(() => {
    fetchMonitors();
  }, []);

  const fetchMonitors = async () => {
    setLoading(true);
    try {
      const data = await api.getMonitors();
      setMonitors(data);
    } catch (err) {
      console.error("Failed to fetch monitors:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (id: string) => {
    setSyncingId(id);
    try {
      const updated = await api.syncMonitor(id);
      setMonitors(prev => prev.map(mon => mon.id === id ? updated : mon));
    } catch (err) {
      console.error("Failed to sync monitor:", err);
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this monitor?")) return;
    try {
      await api.deleteMonitor(id);
      setMonitors(prev => prev.filter(mon => mon.id !== id));
    } catch (err) {
      console.error("Failed to delete monitor:", err);
    }
  };

  const handleCreate = async () => {
    const topic = prompt("Enter the search topic to monitor:");
    if (!topic || !topic.trim()) return;

    try {
      const newMon = await api.createMonitor(topic);
      setMonitors(prev => [newMon, ...prev]);
    } catch (err) {
      console.error("Failed to create monitor:", err);
    }
  };

  return (
    <div className="h-full overflow-y-auto pr-2 space-y-8 bg-bg-deep text-text-body">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif italic text-text-title">Monitors</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-widest font-medium">Configure continuous background assertion checkers.</p>
        </div>
        <Button className="shrink-0" onClick={handleCreate}>
          <PlusCircle className="h-4 w-4 mr-2" /> Create Monitor
        </Button>
      </div>

      <div className="grid gap-6">
        {loading ? (
          <div className="text-center py-12 p-6 border border-dashed border-border-subtle bg-bg-surface flex flex-col items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-highlight-color" />
            <p className="text-xs text-text-subtle uppercase tracking-wider">Loading search monitors...</p>
          </div>
        ) : monitors.length === 0 ? (

          <div className="text-center py-12 p-6 border border-dashed border-border-subtle bg-bg-surface">
            <p className="text-xs text-text-subtle uppercase tracking-wider">No active monitors. Click "Create Monitor" to add one.</p>
          </div>
        ) : (
          monitors.map((mon) => (
            <div key={mon.id} className="p-6 bg-bg-surface border border-border-subtle flex flex-col md:flex-row md:items-center md:justify-between gap-6 hover:border-border-accent transition-colors">
              <div className="space-y-3 flex-1">
                <div className="flex items-center gap-3">
                  <span className={`w-1.5 h-1.5 ${mon.status === 'Active' ? 'bg-highlight-color animate-pulse' : 'bg-text-subtle'}`}></span>
                  <h4 className="text-lg font-serif italic text-text-title">{mon.topic}</h4>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-[10px] uppercase tracking-widest font-bold text-text-subtle">
                  <span className="border border-border-subtle bg-bg-panel px-2 py-0.5 text-text-body font-sans">{mon.scope}</span>
                  <span>Interval: {mon.interval}</span>
                  <span>Last checked: {mon.lastCheck}</span>
                </div>
              </div>

              <div className="flex items-center gap-8 justify-between md:justify-end border-t border-border-subtle md:border-0 pt-4 md:pt-0">
                <div className="flex flex-col items-start md:items-end">
                  <span className="text-[9px] uppercase tracking-widest text-text-subtle font-medium mb-1.5 font-sans">Health State</span>
                  <span className={`text-[10px] font-semibold uppercase tracking-widest px-2.5 py-1 flex items-center gap-1.5 border ${
                    mon.health === "Green" 
                      ? "text-highlight-color bg-highlight-color/10 border-highlight-color/20" 
                      : "text-amber-500 bg-amber-500/10 border-amber-500/20"
                  }`}>
                    {mon.health === "Green" ? <ShieldCheck className="h-3.5 w-3.5" /> : <ShieldAlert className="h-3.5 w-3.5" />}
                    {mon.health} State
                  </span>
                </div>
                
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleSync(mon.id)}
                    disabled={syncingId === mon.id}
                    className="border-border-subtle bg-bg-deep text-xs h-9 px-4 py-2 hover:bg-bg-panel hover:text-text-title text-text-body"
                  >
                    <RefreshCw className={`h-3 w-3 mr-2 ${syncingId === mon.id ? "animate-spin" : "animate-spin-slow"}`} /> Sync
                  </Button>
                  <button 
                    onClick={() => handleDelete(mon.id)}
                    className="p-2 border border-border-subtle hover:border-red-900 hover:text-red-500 text-text-subtle transition-colors cursor-pointer"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

