import type { APIRoute } from "astro";

const API_BASE = import.meta.env.PUBLIC_API_BASE ?? "http://localhost:8000";

function toIcalDate(iso: string): string {
  // "2026-06-04T23:00:00+11:00" → "20260604T120000Z"
  return new Date(iso).toISOString().replace(/[-:]/g, "").replace(/\.\d{3}/, "");
}

function foldLine(line: string): string {
  if (line.length <= 75) return line;
  const chunks: string[] = [];
  let i = 0;
  chunks.push(line.slice(0, 75));
  i = 75;
  while (i < line.length) {
    chunks.push(" " + line.slice(i, i + 74));
    i += 74;
  }
  return chunks.join("\r\n");
}

export const GET: APIRoute = async () => {
  let maintenances: any[] = [];
  try {
    const res = await fetch(`${API_BASE}/maintenances/`);
    if (res.ok) maintenances = await res.json();
  } catch {
    // serve empty calendar if API unreachable
  }

  const now = toIcalDate(new Date().toISOString());

  const events = maintenances
    .map((m: any) => {
      const communes = m.communes_concernees.join(", ");
      const services = m.services.join(", ");
      const summary = `Maintenance Helia — ${communes}`;
      const description = `Services: ${services}\\nImpact: ${m.impact}\\nID: ${m.id}`;
      return [
        "BEGIN:VEVENT",
        foldLine(`UID:helia-${m.id}@helia.nc`),
        `DTSTAMP:${now}`,
        `DTSTART:${toIcalDate(m.timestamp_debut)}`,
        `DTEND:${toIcalDate(m.timestamp_fin)}`,
        foldLine(`SUMMARY:${summary}`),
        foldLine(`DESCRIPTION:${description}`),
        "URL:https://helia.nc/etat-du-reseau",
        "END:VEVENT",
      ].join("\r\n");
    })
    .join("\r\n");

  const cal = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Helia NC//Maintenances//FR",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:Helia NC Maintenances",
    "X-WR-TIMEZONE:Pacific/Noumea",
    events,
    "END:VCALENDAR",
  ].join("\r\n");

  return new Response(cal, {
    headers: { "Content-Type": "text/calendar; charset=utf-8" },
  });
};
