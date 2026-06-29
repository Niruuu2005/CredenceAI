import { sleep } from "../utils/timing.js";
import { TimeoutError } from "../errors.js";

export interface PollOptions<T> {
  fn: () => Promise<T>;
  validate: (result: T) => boolean;
  intervalMs: number;
  maxWaitMs: number;
  onTimeout?: () => void;
}

export async function poll<T>(options: PollOptions<T>): Promise<T> {
  const { fn, validate, intervalMs, maxWaitMs } = options;
  const startedAt = Date.now();

  while (Date.now() - startedAt < maxWaitMs) {
    const result = await fn();
    if (validate(result)) {
      return result;
    }
    await sleep(intervalMs);
  }

  if (options.onTimeout) {
    options.onTimeout();
  }
  throw new TimeoutError(`Polling timed out after ${maxWaitMs}ms.`);
}
