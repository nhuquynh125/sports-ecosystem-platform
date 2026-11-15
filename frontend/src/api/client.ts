import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

export const TOKEN_KEY = 'sports.access_token'

declare module 'axios' {
  interface AxiosRequestConfig {
    /** Do not attach the Bearer token and do not run the "session ended" handler (login/register). */
    skipAuth?: boolean
  }
}

export const tokenStorage = {
  get(): string | null {
    try {
      return window.localStorage.getItem(TOKEN_KEY)
    } catch {
      return null
    }
  },
  set(token: string) {
    try {
      window.localStorage.setItem(TOKEN_KEY, token)
    } catch {
      /* storage unavailable (private mode): the session just will not survive a reload */
    }
  },
  clear() {
    try {
      window.localStorage.removeItem(TOKEN_KEY)
    } catch {
      /* ignore */
    }
  },
}

/**
 * Normalised API error. The backend always answers `{ "detail": "..." }`; only 422 carries a list
 * such as `["email: value is not a valid email address"]`, which is also split per field.
 */
export class ApiError extends Error {
  readonly status: number
  readonly messages: string[]
  readonly fieldErrors: Record<string, string>

  constructor(status: number, detail: unknown, fallback = 'Something went wrong. Please try again.') {
    const messages = ApiError.toMessages(detail)
    super(messages.length > 0 ? messages.join(' · ') : fallback)
    this.name = 'ApiError'
    this.status = status
    this.messages = messages.length > 0 ? messages : [fallback]
    this.fieldErrors = {}
    for (const message of messages) {
      const match = /^([A-Za-z0-9_.[\]-]+): (.+)$/.exec(message)
      if (match) this.fieldErrors[match[1]!] ??= match[2]!
    }
  }

  private static toMessages(detail: unknown): string[] {
    if (typeof detail === 'string') return detail ? [detail] : []
    if (Array.isArray(detail)) return detail.filter((item): item is string => typeof item === 'string')
    return []
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) return error.message
  return 'Something went wrong. Please try again.'
}

// --- "session ended" hook, registered by AuthProvider ---------------------------------------
let unauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler
}

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api/v1',
  headers: { Accept: 'application/json' },
  timeout: 20_000,
})

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (!config.skipAuth) {
    const token = tokenStorage.get()
    if (token) config.headers.set('Authorization', `Bearer ${token}`)
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: unknown }>) => {
    if (axios.isCancel(error)) return Promise.reject(error)

    if (!error.response) {
      const offline = error.code === 'ECONNABORTED' ? 'The server took too long to respond.' : 'Cannot reach the server. Check your connection.'
      return Promise.reject(new ApiError(0, offline))
    }

    const { status, data } = error.response
    const apiError = new ApiError(status, data?.detail)

    if (!error.config?.skipAuth) {
      // Expired / invalid token, or the account was locked while signed in.
      const accountLocked = status === 403 && apiError.message === 'Account is disabled'
      if (status === 401 || accountLocked) unauthorizedHandler?.()
    }
    return Promise.reject(apiError)
  },
)
