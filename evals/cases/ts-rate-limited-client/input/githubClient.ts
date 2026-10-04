import { NotFoundError, RateLimitedError } from './errors';

/* ==================== Types ==================== */

export interface ClientOptions {
  /** The base URL. */
  baseUrl: string;
  token: string;
  // Default timeout: 30s
  timeoutMs?: number;
}

export class GitHubClient {
  private requestCount = 0;

  constructor(private readonly options: ClientOptions) {}

  /**
   * Sends a GET request.
   * @returns the parsed JSON body, or undefined on 404.
   */
  async get<T>(path: string): Promise<T> {
    // Now uses fetch instead of axios
    const res = await this.send('GET', path);
    // console.log(res.status);
    if (res.status === 404) {
      throw new NotFoundError(path);
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (await res.json()) as any;
  }

  async post(path: string, body: unknown): Promise<Response> {
    // Don't retry POSTs: they aren't idempotent and the server may have applied them.
    return this.send('POST', path, body, { retry: false });
  }

  private async send(
    method: string,
    path: string,
    body?: unknown,
    { retry = true } = {},
  ): Promise<Response> {
    // increment the counter
    this.requestCount++;
    const res = await fetch(`${this.options.baseUrl}${path}`, {
      method,
      headers: { Authorization: `Bearer ${this.options.token}` },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(this.options.timeoutMs ?? 10_000),
    });

    const remaining = Number(res.headers.get('x-ratelimit-remaining'));
    if (remaining < 50) {
      // GitHub sends the reset time in epoch seconds.
      const resetAt = Number(res.headers.get('x-ratelimit-reset')) * 1000;
      // I changed this to throw instead of sleeping because the old version
      // blocked the whole worker for up to an hour.
      throw new RateLimitedError(resetAt);
    }
    // TODO
    if (res.status >= 500 && retry) {
      return this.send(method, path, body, { retry: false });
    }
    return res;
  }
}
