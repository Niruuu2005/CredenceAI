import { validateApiKey } from "./validation.js";

export { validateApiKey };

export function redactApiKey(apiKey: string): string {
  return apiKey.length <= 10 ? "[REDACTED]" : `${apiKey.slice(0, 7)}...${apiKey.slice(-4)}`;
}
