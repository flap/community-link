// Normalização nome→slug replicada do backend (app/slugs.py::slugify).
// Mesma sequência determinística: NFKD → remove acentos → lower →
// [^a-z0-9]+ → '-' → trim de hífens → truncar 60 → trim à direita.
// Produz resultado idêntico ao backend para o mesmo nome (RF-001).
export function slugify(name) {
  return (name || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '') // remove marcas de acento (combining marks)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60)
    .replace(/-+$/g, '')
}
