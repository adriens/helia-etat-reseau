import type { APIRoute } from "astro";

const API_BASE = import.meta.env.PUBLIC_API_BASE ?? "http://localhost:8000";

export const GET: APIRoute = async () => {
  let maintenances: any[] = [];
  try {
    const res = await fetch(`${API_BASE}/maintenances/`);
    if (res.ok) maintenances = await res.json();
  } catch {
    // serve empty feed if API unreachable
  }

  const esc = (s: string) =>
    s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

  const items = maintenances
    .map((m: any) => {
      const debut = new Date(m.timestamp_debut).toUTCString();
      const communes = m.communes_concernees.join(", ");
      const services = m.services.join(", ");
      const title = `Maintenance ${m.id} — ${communes}`;
      const desc = `Du ${m.timestamp_debut} au ${m.timestamp_fin}. Services : ${services}. Impact : ${m.impact}.`;
      return `
    <item>
      <title>${esc(title)}</title>
      <link>https://helia.nc/etat-du-reseau</link>
      <guid isPermaLink="false">helia-maintenance-${esc(m.id)}</guid>
      <pubDate>${debut}</pubDate>
      <description>${esc(desc)}</description>
      <category>${esc(m.impact)}</category>
    </item>`;
    })
    .join("");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Helia NC — Maintenances programmées</title>
    <link>https://helia.nc/etat-du-reseau</link>
    <atom:link href="/rss.xml" rel="self" type="application/rss+xml" />
    <description>Maintenances programmées sur le réseau Helia by OPT-NC.</description>
    <language>fr</language>
    <ttl>60</ttl>${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
};
