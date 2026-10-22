/** Splits copy into words; a word wrapped in *stars* is flagged as an accent (italic serif). */
export function richWords(text: string) {
  return text.split(' ').map((raw) => {
    const accent = /^\*.+\*[,.]?$/.test(raw)
    const word = accent ? raw.replace(/\*/g, '') : raw
    return { word, accent }
  })
}
