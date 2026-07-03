import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Download, FolderPlus, Folder, FileText, Trash2, Loader2, Info } from "lucide-react";
import { api, Collection } from "@/lib/api";

export function Collections() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");

  useEffect(() => {
    fetchCollections();
  }, []);

  const fetchCollections = async () => {
    setLoading(true);
    try {
      const data = await api.getCollections();
      setCollections(data);
    } catch (err) {
      console.error("Failed to fetch collections:", err);
    } finally {
      setLoading(false);
    }
  };

  const openDeleteConfirm = (id: string) => {
    setDeleteTargetId(id);
    setIsDeleteOpen(true);
  };

  const submitDelete = async () => {
    if (!deleteTargetId) return;
    try {
      await api.deleteCollection(deleteTargetId);
      setCollections(prev => prev.filter(col => col.id !== deleteTargetId));
    } catch (err) {
      console.error("Failed to delete collection:", err);
    } finally {
      setIsDeleteOpen(false);
      setDeleteTargetId(null);
    }
  };

  const submitCreate = async () => {
    if (!createName || !createName.trim()) return;
    try {
      const newCol = await api.createCollection(createName, createDesc || undefined);
      setCollections(prev => [newCol, ...prev]);
    } catch (err) {
      console.error("Failed to create collection:", err);
    } finally {
      setIsCreateOpen(false);
      setCreateName("");
      setCreateDesc("");
    }
  };

  return (
    <div className="space-y-8 bg-bg-deep text-text-body select-none">
      {/* Create Modal Overlay */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-bg-deep rounded-2xl p-6 w-full max-w-md neu-outset space-y-6 border-none">
            <h3 className="text-xl font-serif italic text-text-title font-medium">Create New Collection</h3>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle ml-1">Name</label>
                <Input 
                  value={createName} 
                  onChange={(e) => setCreateName(e.target.value)} 
                  placeholder="Collection Name" 
                  required 
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase tracking-widest font-extrabold text-text-subtle ml-1">Description (Optional)</label>
                <textarea 
                  value={createDesc} 
                  onChange={(e) => setCreateDesc(e.target.value)} 
                  placeholder="Collection Description" 
                  className="w-full rounded-xl border-none bg-bg-deep neu-inset px-4 py-3 text-sm text-text-body placeholder:text-text-subtle/50 h-24 focus:outline-none focus:ring-2 focus:ring-primary/40 resize-none"
                />
              </div>
            </div>
            <div className="flex gap-4 justify-end">
              <Button variant="outline" onClick={() => { setIsCreateOpen(false); setCreateName(""); setCreateDesc(""); }}>Cancel</Button>
              <Button onClick={submitCreate}>Create</Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal Overlay */}
      {isDeleteOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-bg-deep rounded-2xl p-6 w-full max-w-sm neu-outset space-y-6 text-center border-none">
            <h3 className="text-xl font-serif italic text-text-title font-medium">Delete Collection</h3>
            <p className="text-xs text-text-subtle leading-relaxed">
              Are you sure you want to delete this collection? This action is permanent and cannot be undone.
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
          <h2 className="text-3xl font-serif italic text-text-title">Collections</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-widest font-bold">Coordinate and package verified evidence domains.</p>
        </div>
        <Button className="shrink-0" onClick={() => setIsCreateOpen(true)}>
          <FolderPlus className="h-4 w-4 mr-2" /> New Collection
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-12 p-6 rounded-2xl bg-bg-panel/20 neu-inset-sm flex flex-col items-center gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="text-xs text-text-subtle uppercase tracking-widest font-bold">Loading collections...</p>
          </div>
        ) : collections.length === 0 ? (
          <div className="col-span-full text-center py-12 p-6 rounded-2xl bg-bg-panel/20 neu-inset-sm">
            <p className="text-xs text-text-subtle uppercase tracking-widest font-bold">No collections found. Click "New Collection" to add one.</p>
          </div>
        ) : (
          collections.map((col) => (
            <Card key={col.id} className="flex flex-col justify-between">
              <div>
                <CardHeader className="border-b border-border-subtle/10 pb-5 mb-5 flex flex-row items-start justify-between">
                  <div>
                    <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
                      <Folder className="h-4 w-4 text-primary shrink-0" />
                      {col.name}
                    </CardTitle>
                    <CardDescription className="text-text-subtle text-[10px] mt-2 tracking-wider font-bold">
                      ID: {col.id}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs text-text-body leading-relaxed border-l-2 border-primary pl-3 bg-bg-panel/10 py-1 pr-1 rounded-r-lg">
                    {col.description || "No description provided."}
                  </p>
                  <div className="flex items-center gap-6 mt-4 text-[10px] uppercase tracking-wider font-bold text-text-subtle">
                    <span className="flex items-center gap-1.5"><FileText className="h-3.5 w-3.5 text-primary" /> {col.itemsCount} Sources</span>
                    <span>Updated {col.updatedAt}</span>
                  </div>
                </CardContent>
              </div>
              <div className="flex items-center justify-between p-6 border-t border-border-subtle/10 mt-4">
                <Button size="sm" variant="outline" disabled title="Coming soon" className="opacity-45 cursor-not-allowed">
                  Open Workspace
                </Button>
                <div className="flex gap-2">
                  <button 
                    disabled 
                    title="Coming soon" 
                    className="h-9 w-9 rounded-xl flex items-center justify-center border-none text-text-subtle opacity-45 cursor-not-allowed bg-bg-deep neu-outset-sm"
                  >
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  <button 
                    onClick={() => openDeleteConfirm(col.id)}
                    className="h-9 w-9 rounded-xl flex items-center justify-center border-none text-text-subtle hover:text-red-500 bg-bg-deep hover:bg-bg-panel cursor-pointer active:scale-95 transition-all neu-outset-sm"
                    title="Delete Collection"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
