import { getStore } from "@netlify/blobs";

const headers = {
  "Content-Type": "application/json",
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

function reply(status, body) {
  return new Response(JSON.stringify(body), { status, headers });
}

export default async (request) => {
  if (request.method === "OPTIONS") {
    return new Response("", { status: 204, headers });
  }

  const store = getStore("observatorio");

  if (request.method === "GET") {
    const reading = await store.get("ultima-lectura", { type: "json" });
    if (!reading?.events?.features) {
      return reply(404, { ok: false, detail: "sin lectura guardada" });
    }
    return reply(200, reading);
  }

  if (request.method === "POST") {
    let body;
    try {
      body = await request.json();
    } catch {
      return reply(400, { ok: false, detail: "json inválido" });
    }
    if (body?.events?.type !== "FeatureCollection" || !Array.isArray(body.events.features)) {
      return reply(400, { ok: false, detail: "se esperaba FeatureCollection" });
    }
    const reading = {
      savedAt: Date.now(),
      events: body.events,
      stats: body.stats ?? null,
    };
    await store.setJSON("ultima-lectura", reading);
    return reply(200, { ok: true, savedAt: reading.savedAt, count: body.events.features.length });
  }

  return reply(405, { ok: false, detail: "método no permitido" });
};
