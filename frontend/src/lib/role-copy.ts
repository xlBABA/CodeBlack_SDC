// Product copy used when the API leaves a field empty. These are fixed explanations, not data.

/** Shown beside a score when the API returned no caveat, so no score ever appears without one. */
export const DEFAULT_CAVEAT = 'An estimate from the skills you reported, not a prediction or a hiring decision.'

export const roleTitleFromId = (id = '') => id.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')

export const fmtDate = (iso: string) => {
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('en-MY', { day: 'numeric', month: 'short', year: 'numeric' })
}
