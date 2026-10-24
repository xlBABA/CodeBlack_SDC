// The backend's cached catalogue (backend/app/data/cached), imported at build time so the
// skill list, aliases and landing examples always match the data the API scores against.
import resourcesJson from '../../../backend/app/data/cached/resources.json'
import rolesJson from '../../../backend/app/data/cached/roles.json'

export type CatalogRole = { role_id: string; role_title: string; onet_soc_code: string; core_skills: number }

export const CATALOG_ROLES: CatalogRole[] = rolesJson.map((r) => ({
  role_id: r.role_id,
  role_title: r.role_title,
  onet_soc_code: r.onet_soc_code,
  core_skills: r.required_skills.filter((s) => s.required).length,
}))

/** Real roles by id, in the order given; throws at build/dev time if an id is not in the data. */
export function catalogRoles(ids: string[]): CatalogRole[] {
  return ids.map((id) => {
    const role = CATALOG_ROLES.find((r) => r.role_id === id)
    if (!role) throw new Error(`role_id ${id} is not in roles.json`)
    return role
  })
}

type RawResource = {
  resource_id: string
  title: string
  provider: string
  url: string
  skill_ids: string[]
  estimated_hours: number | null
  team_estimate_hours?: number | null
}

/** Hours as the data states them: the provider's own figure, else the team's labelled estimate. */
export type CatalogResource = { resource_id: string; title: string; provider: string; url: string; hours: number; provider_stated: boolean }

export const CATALOG_RESOURCES: CatalogResource[] = (resourcesJson.resources as RawResource[]).flatMap((r) => {
  const hours = r.estimated_hours ?? r.team_estimate_hours
  return hours == null ? [] : [{ resource_id: r.resource_id, title: r.title, provider: r.provider, url: r.url, hours, provider_stated: r.estimated_hours != null }]
})

/** Real resources by id, in the order given; throws if an id is not in the data. */
export function catalogResources(ids: string[]): CatalogResource[] {
  return ids.map((id) => {
    const resource = CATALOG_RESOURCES.find((r) => r.resource_id === id)
    if (!resource) throw new Error(`resource_id ${id} is not in resources.json`)
    return resource
  })
}

export const formatHours = (h: number) => `${Number(h.toFixed(2))} h`
