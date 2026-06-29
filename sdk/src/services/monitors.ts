import { HttpClient } from "../core/http.js";
import { CreateMonitorRequest, MonitorRecord } from "../types/monitors.js";

export class MonitorsService {
  constructor(private readonly http: HttpClient) {}

  async list(): Promise<MonitorRecord[]> {
    return this.http.request<MonitorRecord[]>({
      method: "GET",
      path: "/monitors",
    });
  }

  async create(request: CreateMonitorRequest): Promise<MonitorRecord> {
    return this.http.request<MonitorRecord>({
      method: "POST",
      path: "/monitors",
      body: request,
    });
  }

  async sync(monitorId: string): Promise<MonitorRecord> {
    return this.http.request<MonitorRecord>({
      method: "POST",
      path: `/monitors/${encodeURIComponent(monitorId)}/sync`,
    });
  }

  async delete(monitorId: string): Promise<{ message: string }> {
    return this.http.request<{ message: string }>({
      method: "DELETE",
      path: `/monitors/${encodeURIComponent(monitorId)}`,
    });
  }
}
