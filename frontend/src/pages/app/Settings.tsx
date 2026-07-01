import { useState, useEffect, type FormEvent } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Key, Sliders, Copy, Trash2, Check, Plus, Loader2 } from "lucide-react";
import { api, ApiKey } from "@/lib/api";

export function Settings() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [labelInput, setLabelInput] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  useEffect(() => {
    fetchKeys();
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
    <div className="h-full overflow-y-auto pr-2 max-w-4xl space-y-10 pb-12 bg-bg-deep text-text-body">
      <div>
        <h2 className="text-3xl font-serif italic text-text-title mb-2">Workspace Settings</h2>
        <p className="text-[10px] uppercase tracking-widest font-medium text-text-subtle">Configure parameters, access credentials, and security defaults.</p>
      </div>

      <div className="space-y-8">
        {/* Intelligence Preferences */}
        <Card className="bg-bg-surface border-border-subtle">
          <CardHeader className="border-b border-border-subtle pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
              <Sliders className="h-5 w-5 text-text-subtle" />
              Intelligence Preferences
            </CardTitle>
            <CardDescription className="text-[10px] text-text-subtle tracking-wider">Tweak reasoning filters and citation thresholds.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h5 className="text-sm font-medium text-text-title">Minimum Citation Count</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Require a minimum number of self-corroborating sources before asserting high-confidence convergence.</p>
              </div>
              <select className="bg-bg-deep border border-border-subtle text-text-body px-4 py-2 text-xs focus:outline-none focus:border-border-accent uppercase tracking-widest min-w-[150px]">
                <option>2 Sources</option>
                <option>3 Sources</option>
                <option>5 Sources (Strict)</option>
              </select>
            </div>

            <div className="h-px bg-border-subtle"></div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h5 className="text-sm font-medium text-text-title">Scholarly Focus Biasing</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Prioritize peer-reviewed scientific journals and patent offices above mainstream journalism indexes.</p>
              </div>
              <select className="bg-bg-deep border border-border-subtle text-text-body px-4 py-2 text-xs focus:outline-none focus:border-border-accent uppercase tracking-widest min-w-[150px]">
                <option>None (Balanced)</option>
                <option>Academic High</option>
                <option>Exclusive Patents</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* API Credentials */}
        <Card className="bg-bg-surface border-border-subtle">
          <CardHeader className="border-b border-border-subtle pb-6 mb-6">
            <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
              <Key className="h-5 w-5 text-text-subtle" />
              API Credentials
            </CardTitle>
            <CardDescription className="text-[10px] text-text-subtle tracking-wider">Access the raw Credence intelligence graph programmatically.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            
            {/* Generate Key Panel */}
            <form onSubmit={handleCreateKey} className="space-y-4">
              <span className="text-[10px] uppercase tracking-widest font-bold text-text-subtle block">Generate API Key</span>
              <div className="space-y-1">
                <label className="text-[10px] text-text-subtle uppercase">Key Label (Optional)</label>
                <input
                  type="text"
                  value={labelInput}
                  onChange={(e) => setLabelInput(e.target.value)}
                  placeholder="e.g. Production server key"
                  className="w-full bg-bg-deep border border-border-subtle text-text-body px-3 py-1.5 text-xs focus:outline-none focus:border-border-accent"
                />
              </div>
              <Button type="submit" size="sm" className="bg-highlight-color text-highlight-foreground px-4 py-2 hover:bg-highlight-color/90 text-xs">
                <Plus className="h-3.5 w-3.5 mr-1" /> Generate New Key
              </Button>
            </form>

            {/* Display newly created key */}
            {newKey && (
              <div className="p-4 border border-amber-900/30 bg-amber-950/10 space-y-3">
                <h6 className="text-xs font-semibold text-amber-500 uppercase tracking-wider">Save Your Key</h6>
                <p className="text-xs text-text-subtle leading-normal">
                  Make sure to copy your API key now. You won't be able to see it again!
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newKey}
                    readOnly
                    className="flex-1 bg-bg-deep border border-border-subtle text-text-body px-3 py-1 text-xs font-mono select-all focus:outline-none"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(newKey)}
                    className="border-border-subtle bg-bg-deep px-3 hover:bg-bg-panel hover:text-text-title text-text-body text-xs"
                  >
                    {copiedKey ? <Check className="h-3.5 w-3.5 text-highlight-color" /> : <Copy className="h-3.5 w-3.5" />}
                  </Button>
                </div>
              </div>
            )}

            <div className="h-px bg-border-subtle"></div>

            {/* Keys List */}
            <div className="space-y-3">
              <span className="text-[10px] uppercase tracking-widest font-bold text-text-subtle block">Active API Keys</span>
              
              {loading ? (
                <div className="flex items-center gap-2 text-xs text-text-subtle py-4">
                  <Loader2 className="h-4 w-4 animate-spin text-highlight-color" />
                  <span>Loading workspace keys...</span>
                </div>
              ) : keys.length === 0 ? (
                <div className="text-center py-6 border border-dashed border-border-subtle text-xs text-text-subtle">
                  No active keys found. Generate a key above to get started.
                </div>
              ) : (
                <div className="border border-border-subtle divide-y divide-border-subtle bg-bg-deep">
                  {keys.map((k) => (
                    <div key={k.id} className="flex items-center justify-between p-3 text-xs gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-text-title">{k.label || "No Label"}</span>
                          <span className="text-[10px] text-text-subtle border border-border-subtle px-1.5 py-0.2 bg-bg-surface font-mono">
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
                          className="p-1.5 border border-border-subtle hover:border-red-900 hover:text-red-500 text-text-subtle transition-colors cursor-pointer"
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

            <div className="h-px bg-border-subtle"></div>

            <div className="flex items-center justify-between gap-4 pt-2">
              <div>
                <h5 className="text-sm font-medium text-text-title">API Access Logging</h5>
                <p className="text-xs text-text-subtle mt-1 leading-normal">Require signed keys and register structural audit records on all outbound IP data streams.</p>
              </div>
              <div className="w-12 h-6 bg-accent border border-border-subtle relative cursor-pointer flex items-center p-0.5">
                <div className="w-4.5 h-4.5 bg-accent-foreground transform translate-x-6 transition-transform"></div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

