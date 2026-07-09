import { useState, useEffect, type FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Key, Sliders, Copy, Trash2, Check, Plus, Loader2 } from "lucide-react";
import { api, ApiKey } from "@/lib/api";
import { cn } from "@/lib/utils";

export function Settings() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [labelInput, setLabelInput] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  // Stateful preferences synced with backend
  const [minCitations, setMinCitations] = useState(2);
  const [scholarlyFocus, setScholarlyFocus] = useState("balanced");
  const [apiLogging, setApiLogging] = useState(true);

  const handleMinCitationsChange = async (val: string) => {
    const num = parseInt(val, 10) || 2;
    setMinCitations(num);
    try {
      await api.updatePreferences({ min_citations: num });
    } catch (err) {
      console.error("Failed to save min citations:", err);
    }
  };

  const handleScholarlyFocusChange = async (val: string) => {
    setScholarlyFocus(val);
    try {
      await api.updatePreferences({ scholarly_focus: val });
    } catch (err) {
      console.error("Failed to save scholarly focus:", err);
    }
  };

  const toggleApiLogging = async () => {
    const newVal = !apiLogging;
    setApiLogging(newVal);
    try {
      await api.updatePreferences({ api_logging_enabled: newVal });
    } catch (err) {
      console.error("Failed to save API logging pref:", err);
    }
  };

  useEffect(() => {
    fetchKeys();
    api.getPreferences().then((prefs) => {
      setMinCitations(prefs.min_citations);
      setScholarlyFocus(prefs.scholarly_focus);
      setApiLogging(prefs.api_logging_enabled);
    }).catch(() => {
      // Fallback to localStorage for offline dev
      const stored = localStorage.getItem("setting_min_citations");
      if (stored) setMinCitations(parseInt(stored, 10) || 2);
    });
  }, []);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const activeKeys = await api.getApiKeys();
      setKeys(activeKeys);
    } catch (err) {
      console.error("Failed to fetch API keys:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e: FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createApiKey(labelInput || undefined);
      setNewKey(res.key);
      setLabelInput("");
      fetchKeys();
    } catch (err) {
      console.error("Failed to create API key:", err);
    }
  };

  const handleRevokeKey = async (id: number) => {
    if (!confirm("Are you sure you want to revoke this API key? This cannot be undone.")) return;
    try {
      await api.revokeApiKey(id);
      fetchKeys();
    } catch (err) {
      console.error("Failed to revoke API key:", err);
    }
  };

  const copyToClipboard = (text: string, id: number | null = null) => {
    navigator.clipboard.writeText(text);
    if (id !== null) {
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } else {
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  return (
    <div className="max-w-4xl space-y-10 pb-12 bg-bg-deep text-text-body select-none">
      <div>
        <h2 className="text-3xl font-serif italic text-text-title mb-2">Workspace Settings</h2>
        <p className="text-[10px] uppercase tracking-widest font-bold text-text-subtle">Configure parameters, access credentials, and security defaults.</p>
      </div>

      <div className="space-y-8">
        {/* Intelligence Preferences */}
        <Card>
          <CardHeader className="border-b border-border-subtle/10 pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
              <Sliders className="h-5 w-5 text-primary" />
              Intelligence Preferences
            </CardTitle>
            <CardDescription className="text-[10px] text-text-subtle tracking-wider">Adjust intelligence criteria and source constraints.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h5 className="text-sm font-semibold text-text-title">Minimum Citation Count</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Require a minimum number of self-corroborating sources before asserting high-confidence convergence.</p>
              </div>
              <select 
                value={String(minCitations)}
                onChange={(e) => handleMinCitationsChange(e.target.value)}
                className="bg-bg-deep text-text-body px-4 py-2.5 text-xs rounded-xl neu-inset-sm focus:outline-none focus:ring-2 focus:ring-primary/40 uppercase tracking-wider font-semibold min-w-[170px] border-none"
              >
                <option value="2">2 Sources</option>
                <option value="3">3 Sources</option>
                <option value="5">5 Sources (Strict)</option>
              </select>
            </div>

            <div className="h-px bg-border-subtle/10"></div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h5 className="text-sm font-semibold text-text-title">Scholarly Focus Biasing</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Prioritize peer-reviewed scientific journals and patent offices above mainstream journalism indexes.</p>
              </div>
              <select 
                value={scholarlyFocus}
                onChange={(e) => handleScholarlyFocusChange(e.target.value)}
                className="bg-bg-deep text-text-body px-4 py-2.5 text-xs rounded-xl neu-inset-sm focus:outline-none focus:ring-2 focus:ring-primary/40 uppercase tracking-wider font-semibold min-w-[170px] border-none"
              >
                <option value="balanced">None (Balanced)</option>
                <option value="academic">Academic High</option>
                <option value="patents">Exclusive Patents</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* API Credentials */}
        <Card>
          <CardHeader className="border-b border-border-subtle/10 pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
              <Key className="h-5 w-5 text-primary" />
              API Credentials
            </CardTitle>
            <CardDescription className="text-[10px] text-text-subtle tracking-wider">Access the raw Credence intelligence graph programmatically.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* Generate Key Panel */}
            <form onSubmit={handleCreateKey} className="space-y-4">
              <span className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle block">Generate API Key</span>
              <div className="space-y-1">
                <label className="text-[10px] text-text-subtle uppercase font-semibold">Key Label (Optional)</label>
                <Input
                  type="text"
                  value={labelInput}
                  onChange={(e) => setLabelInput(e.target.value)}
                  placeholder="e.g. Production server key"
                  className="w-full"
                />
              </div>
              <Button type="submit" size="sm" className="bg-primary text-primary-foreground">
                <Plus className="h-3.5 w-3.5 mr-1" /> Generate New Key
              </Button>
            </form>

            {/* Display newly created key */}
            {newKey && (
              <div className="p-4 rounded-2xl bg-bg-panel/20 neu-inset-sm space-y-3">
                <h6 className="text-xs font-semibold text-amber-500 uppercase tracking-wider">Save Your Key</h6>
                <p className="text-xs text-text-subtle leading-normal">
                  Make sure to copy your API key now. You won't be able to see it again!
                </p>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    value={newKey}
                    readOnly
                    className="flex-1 font-mono text-xs select-all focus:outline-none"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(newKey)}
                  >
                    {copiedKey ? <Check className="h-3.5 w-3.5 text-highlight-color" /> : <Copy className="h-3.5 w-3.5" />}
                  </Button>
                </div>
              </div>
            )}

            <div className="h-px bg-border-subtle/10"></div>

            {/* Keys List */}
            <div className="space-y-3">
              <span className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle block">Active API Keys</span>
              
              {loading ? (
                <div className="flex items-center gap-2 text-xs text-text-subtle py-4">
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                  <span>Loading workspace keys...</span>
                </div>
              ) : keys.length === 0 ? (
                <div className="text-center py-6 border border-dashed border-border-subtle/20 rounded-2xl text-xs text-text-subtle bg-bg-deep/40">
                  No active keys found. Generate a key above to get started.
                </div>
              ) : (
                <div className="rounded-2xl overflow-hidden bg-bg-panel/20 neu-inset-sm divide-y divide-border-subtle/10">
                  {keys.map((k) => (
                    <div key={k.id} className="flex items-center justify-between p-4 text-xs gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-text-title">{k.label || "No Label"}</span>
                          <span className="text-[10px] text-text-subtle border border-border-subtle/20 rounded-lg px-2 py-0.5 bg-bg-deep font-mono">
                            ID: {k.id}
                          </span>
                        </div>
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[10px] text-text-subtle">
                          <span>Owner: {k.owner}</span>
                          <span>Created: {new Date(k.created_at).toLocaleDateString()}</span>
                          <span>Last Used: {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString() : "Never"}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleRevokeKey(k.id)}
                          className="h-8 w-8 rounded-xl flex items-center justify-center border-none text-text-subtle hover:text-red-500 bg-bg-deep hover:bg-bg-panel cursor-pointer active:scale-95 transition-all neu-outset-sm"
                          title="Revoke Key"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="h-px bg-border-subtle/10"></div>

            <div className="flex items-center justify-between gap-4 pt-2">
              <div>
                <h5 className="text-sm font-semibold text-text-title">API Access Logging</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Require signed keys and register structural audit records on all outbound IP data streams.</p>
              </div>
              <button 
                type="button"
                onClick={toggleApiLogging}
                className={cn(
                  "w-12 h-6 rounded-full relative transition-all duration-300 p-0.5 cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary/40",
                  apiLogging ? "bg-primary neu-inset-sm" : "bg-bg-panel/40 neu-inset-sm"
                )}
                role="switch"
                aria-checked={apiLogging}
              >
                <div className={cn(
                  "w-5 h-5 rounded-full bg-white shadow-md transform transition-transform duration-300",
                  apiLogging ? "translate-x-6" : "translate-x-0"
                )} />
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
