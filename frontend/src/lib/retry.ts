const WAKEUP_RETRIES = 3;
const WAKEUP_BACKOFF_MS = 1500;

function isWakeupError(err: unknown): boolean {
  if (!err || typeof err !== "object") return false;
  const name = (err as { name?: string }).name ?? "";
  const message = String((err as { message?: string }).message ?? "");
  return (
    name === "NetworkError" ||
    message.includes("Network connection failed") ||
    message.includes("Failed to fetch") ||
    message.includes("Load failed")
  );
}

export async function withWakeupRetry<T>(fn: () => Promise<T>): Promise<T> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= WAKEUP_RETRIES; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (!isWakeupError(err) || attempt === WAKEUP_RETRIES) {
        throw err;
      }
      await new Promise((resolve) =>
        setTimeout(resolve, WAKEUP_BACKOFF_MS * (attempt + 1))
      );
    }
  }
  throw lastError;
}
