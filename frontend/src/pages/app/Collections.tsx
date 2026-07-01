import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FolderPlus, Folder, FileText, Trash2, Loader2 } from "lucide-react";
import { api, Collection } from "@/lib/api";

export function Collections() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);

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

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this collection?")) return;
    try {
      await api.deleteCollection(id);
      setCollections(prev => prev.filter(col => col.id !== id));
    } catch (err) {
      console.error("Failed to delete collection:", err);
    }
  };

  const handleCreate = async () => {
    const name = prompt("Enter the name of the new collection:");
    if (!name || !name.trim()) return;
    const desc = prompt("Enter a description for this collection:");

    try {
      const newCol = await api.createCollection(name, desc || undefined);
      setCollections(prev => [newCol, ...prev]);
    } catch (err) {
      console.error("Failed to create collection:", err);
    }
  };

  return (
    <div className="h-full overflow-y-auto pr-2 space-y-8 bg-bg-deep text-text-body">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-3xl font-serif italic text-text-title">Collections</h2>
          <p className="text-text-subtle mt-2 text-xs uppercase tracking-widest font-medium">Coordinate and package verified evidence domains.</p>
        </div>
        <Button className="shrink-0" onClick={handleCreate}>
          <FolderPlus className="h-4 w-4 mr-2" /> New Collection
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-12 p-6 border border-dashed border-border-subtle bg-bg-surface flex flex-col items-center gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-highlight-color" />
            <p className="text-xs text-text-subtle uppercase tracking-wider">Loading collections...</p>
          </div>
        ) : collections.length === 0 ? (

          <div className="col-span-full text-center py-12 p-6 border border-dashed border-border-subtle bg-bg-surface">
            <p className="text-xs text-text-subtle uppercase tracking-wider">No collections found. Click "New Collection" to add one.</p>
          </div>
        ) : (
          collections.map((col) => (
            <Card key={col.id} className="bg-bg-surface border-border-subtle flex flex-col justify-between">
              <div>
                <CardHeader className="border-b border-border-subtle pb-5 mb-5 flex flex-row items-start justify-between">
                  <div>
                    <CardTitle className="text-xl font-serif italic text-text-title flex items-center gap-2">
                      <Folder className="h-4 w-4 text-text-subtle shrink-0" />
                      {col.name}
                    </CardTitle>
                    <CardDescription className="text-text-subtle text-[10px] mt-2 tracking-widest uppercase">
                      ID: {col.id}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-xs text-text-body leading-relaxed border-l-2 border-border-subtle pl-3">
                    {col.description}
                  </p>
                  <div className="flex items-center gap-6 mt-4 text-[10px] uppercase tracking-widest font-bold text-text-subtle">
                    <span className="flex items-center gap-1.5"><FileText className="h-3 w-3" /> {col.itemsCount} Sources</span>
                    <span>Updated {col.updatedAt}</span>
                  </div>
                </CardContent>
              </div>
              <div className="flex items-center justify-between p-6 border-t border-border-subtle mt-4">
                <Button size="sm" variant="outline" disabled title="Coming soon" className="border-border-subtle bg-bg-deep text-xs text-text-subtle opacity-60 cursor-not-allowed">
                  Open Workspace
                </Button>
                <div className="flex gap-2">
                  <button disabled title="Coming soon" className="p-2 border border-border-subtle text-text-subtle opacity-60 cursor-not-allowed">
                    <Download className="h-3.5 w-3.5" />
                  </button>
                  <button 
                    onClick={() => handleDelete(col.id)}
                    className="p-2 border border-border-subtle hover:border-red-900 hover:text-red-500 text-text-subtle transition-colors cursor-pointer"
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

