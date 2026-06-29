export interface MonitorRecord {
  id: string;
  topic: string;
  scope: string;
  status: string;
  interval: string;
  last_check: string;
  health: string;
}

export interface CreateMonitorRequest {
  topic: string;
  scope?: string;
  interval?: string;
}
