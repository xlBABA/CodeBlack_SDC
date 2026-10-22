import { useSyncExternalStore } from 'react'
import { STORAGE_PREFIX } from '@/config/product'
import { DEMO_PROFILE } from '@/content/demo-profile'
import type { DataMode, StudentProfile } from '@/types/api'
import { api } from './api'

// The analysed profile lives here and in sessionStorage, so a refresh keeps it. The whole
// profile is kept (not only profile_id) because every endpoint takes the profile itself.

export type StoredProfile = {
  profile: StudentProfile
  data_mode: DataMode
  analyzed_at: string
  demo: boolean
}

const KEY = `${STORAGE_PREFIX}:profile`
const listeners = new Set<() => void>()

function read(): StoredProfile | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as StoredProfile) : null
  } catch {
    return null
  }
}

let current = read()

function write(next: StoredProfile | null) {
  current = next
  try {
    if (next) sessionStorage.setItem(KEY, JSON.stringify(next))
    else sessionStorage.removeItem(KEY)
  } catch {
    // storage blocked: the profile still lives in memory for this visit
  }
  listeners.forEach((fn) => fn())
}

const subscribe = (fn: () => void) => {
  listeners.add(fn)
  return () => {
    listeners.delete(fn)
  }
}

export const getProfile = () => current
export const useStoredProfile = () => useSyncExternalStore(subscribe, () => current)

/** Sends the draft to POST /profile/analyze and keeps the normalised result. */
export async function analyzeAndStore(draft: StudentProfile, { demo = false, signal }: { demo?: boolean; signal?: AbortSignal } = {}) {
  const res = await api.analyzeProfile(draft, { signal })
  write({ profile: res.data, data_mode: res.data_mode, analyzed_at: res.generated_at, demo })
  return res
}

export const loadDemoProfile = (signal?: AbortSignal) => analyzeAndStore(DEMO_PROFILE, { demo: true, signal })

export function clearProfile() {
  write(null)
}
