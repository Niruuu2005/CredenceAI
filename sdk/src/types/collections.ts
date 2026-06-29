export interface CollectionRecord {
  id: string;
  name: string;
  description: string;
  items_count: number;
  updated_at: string;
}

export interface CreateCollectionRequest {
  name: string;
  description?: string;
}
