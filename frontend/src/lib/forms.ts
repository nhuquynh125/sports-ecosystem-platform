import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'
import { z } from 'zod'
import { isApiError } from '@/api/client'

/**
 * Pushes backend 422 messages ("email: value is not a valid email address") onto the matching form
 * fields. Returns whatever could not be attached to a field (to show in a <FormAlert>), or null.
 */
export function applyApiErrors<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly (keyof T & string)[],
): string | null {
  if (!isApiError(error)) return 'Something went wrong. Please try again.'
  const attached = new Set<string>()
  for (const [key, message] of Object.entries(error.fieldErrors)) {
    if ((fields as readonly string[]).includes(key)) {
      setError(key as Path<T>, { type: 'server', message })
      attached.add(key)
    }
  }
  if (attached.size === 0) return error.message
  const rest = error.messages.filter((message) => ![...attached].some((key) => message.startsWith(`${key}: `)))
  return rest.length > 0 ? rest.join(' · ') : null
}

/** Mirrors backend rule NFR-SEC-02: 8+ characters, letters and digits, at most 72 bytes (bcrypt). */
export const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters long')
  .refine((value) => new TextEncoder().encode(value).length <= 72, 'Password must be at most 72 bytes long')
  .refine((value) => /\p{L}/u.test(value) && /\d/.test(value), 'Password must contain both letters and digits')

/** "" -> null, otherwise the trimmed string (for optional text columns). */
export function emptyToNull(value: string): string | null {
  const trimmed = value.trim()
  return trimmed === '' ? null : trimmed
}

export function numberOrNull(value: string): number | null {
  const trimmed = value.trim()
  return trimmed === '' ? null : Number(trimmed)
}
