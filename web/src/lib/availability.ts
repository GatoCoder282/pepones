import type { Weekly } from "./content";

export function weeklyAvailability(weekly: Weekly, now = Date.now()) {
  if (weekly.demo) return "demo";
  if (weekly.status === "sold-out") return "sold-out";
  if (weekly.status !== "available") return "unavailable";
  if (weekly.startsAt && now < Date.parse(weekly.startsAt)) return "upcoming";
  if (weekly.endsAt && now >= Date.parse(weekly.endsAt)) return "expired";
  return "available";
}
export function whatsappLink(number: string | null, name?: string) {
  if (!number) return null;
  return `https://wa.me/${number}?text=${encodeURIComponent(`¡Hola, Pepones! ${name ? `Quisiera consultar por ${name}.` : "Quisiera consultar el menú disponible."}`)}`;
}
