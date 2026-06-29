export interface SearchQueryParams {
  q: string;
  limit?: number;
  offset?: number;
  intent?: string;
}

export interface SearchResultItem {
  title?: string;
  url?: string;
  snippet?: string;
  source?: string;
  score?: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResultItem[];
  total?: number;
}
