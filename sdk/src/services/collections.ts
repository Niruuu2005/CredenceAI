import { HttpClient } from "../core/http.js";
import { CollectionRecord, CreateCollectionRequest } from "../types/collections.js";

export class CollectionsService {
  constructor(private readonly http: HttpClient) {}

  async list(): Promise<CollectionRecord[]> {
    return this.http.request<CollectionRecord[]>({
      method: "GET",
      path: "/collections",
    });
  }

  async create(request: CreateCollectionRequest): Promise<CollectionRecord> {
    return this.http.request<CollectionRecord>({
      method: "POST",
      path: "/collections",
      body: request,
    });
  }

  async delete(collectionId: string): Promise<{ message: string }> {
    return this.http.request<{ message: string }>({
      method: "DELETE",
      path: `/collections/${encodeURIComponent(collectionId)}`,
    });
  }
}
