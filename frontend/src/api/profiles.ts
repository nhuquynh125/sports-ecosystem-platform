import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/api/client'
import type {
  AvailabilitySlot,
  AvailabilitySlotPayload,
  PlayerProfile,
  PlayerProfileCreatePayload,
  PlayerProfileUpdatePayload,
} from '@/api/types'

export const profileKeys = {
  mine: ['player-profiles', 'mine'] as const,
  slots: (profileId: number) => ['player-profiles', profileId, 'availability'] as const,
}

export function useMyProfiles(enabled = true) {
  return useQuery({
    queryKey: profileKeys.mine,
    queryFn: () => api.get<PlayerProfile[]>('/player-profiles/me').then((r) => r.data),
    enabled,
  })
}

export function useCreateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: PlayerProfileCreatePayload) =>
      api.post<PlayerProfile>('/player-profiles', payload).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.mine }),
    meta: { silent: true },
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: PlayerProfileUpdatePayload }) =>
      api.patch<PlayerProfile>(`/player-profiles/${id}`, payload).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.mine }),
    meta: { silent: true },
  })
}

export function useDeleteProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.delete<void>(`/player-profiles/${id}`).then(() => undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.mine }),
  })
}

// --- weekly availability -------------------------------------------------------------------
export function useSlots(profileId: number | null) {
  return useQuery({
    queryKey: profileKeys.slots(profileId ?? 0),
    queryFn: () =>
      api.get<AvailabilitySlot[]>(`/player-profiles/${profileId}/availability`).then((r) => r.data),
    enabled: profileId !== null,
  })
}

export function useAddSlot(profileId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: AvailabilitySlotPayload) =>
      api.post<AvailabilitySlot>(`/player-profiles/${profileId}/availability`, payload).then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.slots(profileId) }),
    meta: { silent: true },
  })
}

export function useUpdateSlot(profileId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ slotId, payload }: { slotId: number; payload: Partial<AvailabilitySlotPayload> }) =>
      api
        .patch<AvailabilitySlot>(`/player-profiles/${profileId}/availability/${slotId}`, payload)
        .then((r) => r.data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.slots(profileId) }),
    meta: { silent: true },
  })
}

export function useDeleteSlot(profileId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (slotId: number) =>
      api.delete<void>(`/player-profiles/${profileId}/availability/${slotId}`).then(() => undefined),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: profileKeys.slots(profileId) }),
  })
}
