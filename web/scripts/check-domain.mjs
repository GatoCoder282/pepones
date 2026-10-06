import assert from "node:assert/strict";
import { weeklyAvailability, whatsappLink } from "../src/lib/availability.ts";

const weekly = {
  demo: false,
  status: "available",
  startsAt: "2026-10-05T12:00:00-04:00",
  endsAt: "2026-10-12T00:00:00-04:00",
};
assert.equal(
  weeklyAvailability(weekly, Date.parse("2026-10-05T15:59:59Z")),
  "upcoming",
);
assert.equal(
  weeklyAvailability(weekly, Date.parse("2026-10-05T16:00:00Z")),
  "available",
);
assert.equal(
  weeklyAvailability(weekly, Date.parse("2026-10-12T04:00:00Z")),
  "expired",
);
assert.equal(weeklyAvailability({ ...weekly, status: "sold-out" }), "sold-out");
assert.equal(weeklyAvailability({ ...weekly, status: "draft" }), "unavailable");
assert.equal(weeklyAvailability({ ...weekly, demo: true }), "demo");
assert.equal(whatsappLink(null, "Big Peps"), null);
const url = new URL(whatsappLink("59100000000", "Caribeña & queso"));
assert.equal(
  url.searchParams.get("text"),
  "¡Hola, Pepones! Quisiera consultar por Caribeña & queso.",
);
console.log(
  "8 comprobaciones de disponibilidad, límites horarios y enlace WhatsApp aprobadas.",
);
