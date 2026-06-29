import { HttpClient } from "../core/http.js";
import { SearchQueryParams, SearchResponse } from "../types/index.js";
import { ValidationError } from "../errors.js";

export class SearchService {
  constructor(private readonly http: HttpClient) {}

  async search(params: SearchQueryParams): Promise<SearchResponse> {
    if (!params?.q?.trim()) {
      throw new ValidationError("search requires a non-empty q parameter.");
    }

    return this.http.request<SearchResponse>({
      method: "GET",
      path: "/search",
      query: {
        q: params.q,
        limit: params.limit,
        offset: params.offset,
        intent: params.intent,
      },
    });
  }
}
