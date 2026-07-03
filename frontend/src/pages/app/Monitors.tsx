import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck, ShieldAlert, PlusCircle, Trash2, RefreshCw, Loader2 } from "lucide-react";
import { api, Monitor } from "@/lib/api";

export function Monitors() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [createTopic, setCreateTopic] = useState("");

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

  const openDeleteConfirm = (id: string) => {
    setDeleteTargetId(id);
    setIsDeleteOpen(true);
  };

  const submitDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await api.deleteMonitor(deleteTargetId);
      setMonitors(prev => prev.filter(mon => mon.id !== deleteTargetId));
    } catch (err) {
      console.error("Failed to delete monitor:", err);
    } finally {
      setIsDeleteOpen(false);
      setDeleteTargetId(null);
    }
  };

  const submitCreate = async () => {
    if (!createTopic || !createTopic.trim()) return;
    try {
      const newMon = await api.createMonitor(createTopic);
      setMonitors(prev => [newMon, ...prev]);
    } catch (err) {
      console.error("Failed to create monitor:", err);
    } finally {
      setIsCreateOpen(false);
      setCreateTopic("");
    }
  };

  return (
    <div className="space-y-8 bg-bg-deep text-text-body select-none">
      {/* Create Modal Overlay */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-bg-deep rounded-2xl p-6 w-full max-w-md neu-outset space-y-6 border-none">
            <h3 className="text-xl font-serif italic text-text-title font-medium">Create New Monitor</h3>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle ml-1">Search Topic to Monitor</label>
                <Input 
                  value={createTopic} 
                  onChange={(e) => setCreateTopic(e.target.value)} 
                  placeholder="e.g. Artificial Intelligence standards updates" 
                  required 
                />
              </div>
            </div>
            <div className="flex gap-4 justify-end">
              <Button variant="outline" onClick={() => { setIsCreateOpen(false); setCreateTopic(""); }}>Cancel</Button>
              <Button onClick={submitCreate}>Create</Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal Overlay */}
      {isDeleteOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-bg-deep rounded-2xl p-6 w-full max-w-sm neu-outset space-y-6 text-center border-none">
            <h3 className="text-xl font-serif italic text-text-title font-medium">Delete Monitor</h3>
            <p className="text-xs text-text-subtle leading-relaxed">
              Are you sure you want to delete this monitor? This action is permanent and cannot be undone.
            </p>
            <div className="flex gap-4 justify-center">
              <Button variant="outline" onClick={() => { setIsDeleteOpen(false); setDeleteTargetId(null); }}>Cancel</Button>
              <Button variant="destructive" onClick={submitDelete}>Delete</Button>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif italic text-text-title">Monitors</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-wider font-bold">Manual topic checks — Scheduled updates require a Pro or Enterprise plan.</p>
        </div>
        <Button className="shrink-0" onClick={() => setIsCreateOpen(true)}>
          <PlusCircle className="h-4 w-4 mr-2" /> Create Monitor
        </Button>
      </div>

      <div className="grid gap-6">
        {loading ? (
          <div className="text-center py-12 p-6 rounded-2xl bg-bg-panel/20 neu-inset-sm flex flex-col items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-xs text-text-subtle uppercase tracking-widest font-bold">Loading search monitors...</p>
          </div>
        ) : monitors.length === 0 ? (
          <div className="text-center py-12 p-6 rounded-2xl bg-bg-panel/20 neu-inset-sm">
            <p className="text-xs text-text-subtle uppercase tracking-widest font-bold">No active monitors. Click "Create Monitor" to add one.</p>
          </div>
        ) : (
          monitors.map((mon) => (
            <div key={mon.id} className="p-6 rounded-2xl bg-bg-deep neu-outset border-none flex flex-col md:flex-row md:items-center md:justify-between gap-6 transition-all duration-300">
              <div className="space-y-3 flex-1">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${mon.status === 'Active' ? 'bg-highlight-color animate-[pulse_2s_infinite]' : 'bg-text-subtle'}`}></span>
                  <h4 className="text-lg font-serif italic text-text-title">{mon.topic}</h4>
                </div>
                <div className="flex flex-wrap items-center gap-6 text-[10px] uppercase tracking-wider font-bold text-text-subtle">
                  <span className="border border-border-subtle/20 bg-bg-panel/40 px-2 py-0.5 text-text-body font-sans rounded-md">{mon.scope}</span>
                  <span>Interval: {mon.topic.length > 30 ? "4 Hours" : mon.interval}</span>
                  <span>Last checked: {mon.lastCheck}</span>
                </div>
              </div>

              <div className="flex items-center gap-8 justify-between md:justify-end border-t border-border-subtle/10 md:border-0 pt-4 md:pt-0">
                <div className="flex flex-col items-start md:items-end">
                  <span className="text-[9px] uppercase tracking-widest text-text-subtle font-extrabold mb-1.5 font-sans">Health State</span>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1.5 flex items-center gap-1.5 border rounded-xl ${
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
                    className="h-10"
                  >
                    <RefreshCw className={`h-3 w-3 mr-2 ${syncingId === mon.id ? "animate-spin" : ""}`} /> Manual Check
                  </Button>
                  <button 
                    onClick={() => openDeleteConfirm(mon.id)}
                    className="h-10 w-10 rounded-xl flex items-center justify-center border-none text-text-subtle hover:text-red-500 bg-bg-deep hover:bg-bg-panel cursor-pointer active:scale-95 transition-all neu-outset-sm"
                    title="Delete Monitor"
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
