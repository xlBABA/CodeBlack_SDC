import { use, type ComponentType } from 'react'

type PageModule = { default: ComponentType }

/**
 * Like React.lazy, but the chunk can be fetched ahead of time (on hover, or while the
 * previous page fades out) and, once loaded, renders synchronously without suspending:
 * the promise is tagged fulfilled, which use() reads before deciding to suspend.
 */
export function lazyPage(load: () => Promise<PageModule>) {
  let mod: PageModule | undefined
  let pending: Promise<void> | undefined

  const preload = (): Promise<void> => {
    if (!pending) {
      const p = load().then((m) => {
        mod = m
      })
      p.then(() => Object.assign(p, { status: 'fulfilled', value: undefined }))
      pending = p
    }
    return pending
  }

  function LazyPage() {
    use(preload())
    const Component = mod!.default
    return <Component />
  }
  return Object.assign(LazyPage, { preload })
}
