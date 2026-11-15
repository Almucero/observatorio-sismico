import { Component, OnDestroy, signal } from '@angular/core';
import { LeafletDirective } from '@bluehalo/ngx-leaflet';
import * as L from 'leaflet';
import type { FeatureCollection, Point } from 'geojson';

type Properties = {
  mag: number | null;
  place: string;
  time: number;
  updated: number;
  country_name?: string | null;
  country_id?: string | null;
};
type Events = FeatureCollection<Point, Properties> & {
  metadata?: {
    generated?: number;
    last_ingestion?: number | null;
    mode?: string;
    truncated?: boolean;
    count?: number;
    total?: number;
  };
};
type Config = {
  mode: 'demo' | 'api';
  apiUrl: string;
  refreshMs: number;
  skipNgrokWarning: boolean;
  dataMode?: 'live' | 'replay';
};
type CountryRow = { country_id: string; country_name: string; count: number };
type BandRow = { banda: string; count: number };
type EventRow = {
  id: string;
  place: string;
  mag: number | null;
  time: string;
  country: string;
};

@Component({
  selector: 'app-root', standalone: true, imports: [LeafletDirective],
  templateUrl: './app.component.html', styleUrl: './app.component.css'
})
export class AppComponent implements OnDestroy {
  readonly mode = signal('Cargando configuración');
  readonly status = signal('Preparando el mapa…');
  readonly lastRead = signal('Sin lectura');
  readonly generated = signal('Sin información');
  readonly lastIngestion = signal('Sin información');
  readonly staleWarning = signal('');
  readonly count = signal(0);
  readonly omitted = signal(0);
  readonly truncated = signal(false);
  readonly countriesStatus = signal('Cargando catálogo');
  readonly startLocal = signal('');
  readonly endLocal = signal('');
  readonly minMag = signal<number | null>(null);
  readonly countryId = signal('');
  readonly statsSummary = signal('Sin estadísticas');
  readonly statsAvisos = signal<string[]>([]);
  readonly statsCountries = signal<CountryRow[]>([]);
  readonly statsMag = signal<BandRow[]>([]);
  readonly statsDepth = signal<BandRow[]>([]);
  readonly statsHour = signal<{ hora: string; count: number }[]>([]);
  readonly statsHourMax = signal(1);
  readonly statsMagMax = signal(1);
  readonly statsDepthMax = signal(1);
  readonly eventRows = signal<EventRow[]>([]);
  readonly options: L.MapOptions = { center: L.latLng(18, 0), zoom: 2, minZoom: 2, maxZoom: 8, preferCanvas: true, worldCopyJump: false };
  private map?: L.Map;
  private events = L.layerGroup();
  private timer?: ReturnType<typeof setTimeout>;
  private controller = new AbortController();
  private destroyed = false;
  private config?: Config;

  async onMapReady(map: L.Map): Promise<void> {
    this.map = map;
    const base = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, noWrap: true, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);
    const borders = L.geoJSON(undefined, { style: { color: '#334155', weight: 1, fill: false },
      onEachFeature: (feature, layer) => {
        const name = document.createElement('span');
        name.textContent = feature.properties?.NAME_ES ?? feature.properties?.ADMIN ?? 'Sin nombre';
        layer.bindTooltip(name);
      }
    }).addTo(map);
    this.events.addTo(map);
    L.control.layers({ 'OpenStreetMap': base }, { 'Países (Natural Earth)': borders, 'Terremotos': this.events }).addTo(map);
    map.attributionControl.addAttribution('Fronteras: Natural Earth · Datos reales: USGS');
    try {
      borders.addData(await this.readJson<FeatureCollection>('datos/paises.geojson'));
      this.countriesStatus.set('Catálogo de países cargado');
    } catch { this.countriesStatus.set('No se pudo cargar el catálogo de países'); }
    if (this.destroyed) return;
    try {
      const config = await this.readJson<Config>('config.json');
      if (!['demo', 'api'].includes(config.mode)) throw new Error('Modo inválido');
      this.config = config;
      const replay = config.dataMode === 'replay';
      this.mode.set(
        config.mode === 'demo'
          ? 'DEMOSTRACIÓN · datos ficticios'
          : replay
            ? 'REPRODUCCIÓN · datos aislados de live'
            : 'API · datos del backend'
      );
      await this.refresh();
    } catch { this.status.set('Error: revisa public/config.json'); }
  }

  onStart(event: Event): void { this.startLocal.set((event.target as HTMLInputElement).value); }
  onEnd(event: Event): void { this.endLocal.set((event.target as HTMLInputElement).value); }
  onMinMag(event: Event): void {
    const raw = (event.target as HTMLInputElement).value;
    this.minMag.set(raw === '' ? null : Number(raw));
  }
  onCountry(event: Event): void { this.countryId.set((event.target as HTMLInputElement).value.trim().toUpperCase()); }

  applyFilters(): void {
    clearTimeout(this.timer);
    void this.refresh();
  }

  barWidth(value: number, max: number): number {
    return Math.max(4, Math.round((value / Math.max(max, 1)) * 100));
  }

  private queryParams(): string {
    const params = new URLSearchParams();
    if (this.startLocal()) params.set('start', new Date(this.startLocal()).toISOString());
    if (this.endLocal()) params.set('end', new Date(this.endLocal()).toISOString());
    if (this.minMag() !== null && Number.isFinite(this.minMag()!)) params.set('min_mag', String(this.minMag()));
    if (this.countryId()) params.set('country_id', this.countryId());
    if (this.config?.dataMode === 'replay') params.set('mode', 'replay');
    const qs = params.toString();
    return qs ? `?${qs}` : '';
  }

  private async readJson<T>(url: string, headers: Record<string, string> = {}): Promise<T> {
    const response = await fetch(url, { headers, cache: 'no-store',
      signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(15000)]) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json() as Promise<T>;
  }

  private updateStale(lastIngestionMs: number | null | undefined, refreshMs: number): void {
    if (typeof lastIngestionMs !== 'number' || !Number.isFinite(lastIngestionMs)) {
      this.staleWarning.set('Sin marca de última ingesta: el productor puede no haber consultado USGS aún.');
      return;
    }
    const ageMs = Date.now() - lastIngestionMs;
    const threshold = Math.max(180000, refreshMs * 3);
    if (ageMs > threshold) {
      const mins = Math.round(ageMs / 60000);
      this.staleWarning.set(`Ingesta desactualizada (~${mins} min). Revisa productor, red o USGS.`);
    } else {
      this.staleWarning.set('');
    }
  }

  private async refresh(): Promise<void> {
    const config = this.config;
    if (!config) return;
    try {
      const qs = this.queryParams();
      const url = config.mode === 'demo'
        ? 'datos/terremotos-demo.geojson'
        : `${config.apiUrl.replace(/\/$/, '')}/api/eventos${qs}`;
      const headers: Record<string, string> = {};
      if (config.mode === 'api' && config.skipNgrokWarning) headers['ngrok-skip-browser-warning'] = '1';
      const data = await this.readJson<Events>(url, headers);
      if (this.destroyed) return;
      if (data.type !== 'FeatureCollection' || !Array.isArray(data.features)) throw new Error('Se esperaba FeatureCollection');
      const next = L.layerGroup(); let omitted = 0; let count = 0;
      const rows: EventRow[] = [];
      for (const feature of data.features) {
        const p = feature.properties;
        const c = feature.geometry?.type === 'Point' ? feature.geometry.coordinates : [];
        const [lon, lat, depth] = c;
        if (!p || !Number.isFinite(lon) || !Number.isFinite(lat) || Math.abs(lon) > 180 || Math.abs(lat) > 90) { omitted++; continue; }
        const magnitude = typeof p.mag === 'number' && Number.isFinite(p.mag) ? p.mag : null;
        const depthOk = typeof depth === 'number' && Number.isFinite(depth);
        const color = !depthOk ? '#64748b' : depth < 70 ? '#e8a317' : depth < 300 ? '#e35b37' : '#7b3fb6';
        const popup = document.createElement('div');
        popup.textContent = `${p.place ?? 'Sin descripción'}\nMagnitud: ${magnitude ?? 'ND'}\nProfundidad: ${depthOk ? depth + ' km' : 'ND'}\nFecha UTC: ${this.date(p.time)}\nPaís: ${p.country_name ?? 'Sin país asignado'}\nID: ${feature.id ?? 'ND'}`;
        L.circleMarker([lat, lon], { radius: magnitude === null ? 4 : Math.max(3, Math.min(18, 3 + (magnitude + 1) * 2)), color, fillColor: color, fillOpacity: .75, weight: 1 }).bindPopup(popup).addTo(next);
        count++;
        rows.push({
          id: String(feature.id ?? 'ND'),
          place: p.place ?? 'Sin descripción',
          mag: magnitude,
          time: this.date(p.time),
          country: p.country_name ?? 'Sin país asignado',
        });
      }
      this.events.clearLayers(); this.events.addLayer(next);
      this.count.set(count); this.omitted.set(omitted);
      this.eventRows.set(rows.slice(0, 100));
      this.truncated.set(Boolean(data.metadata?.truncated));
      this.lastRead.set(new Date().toISOString());
      this.generated.set(this.date(data.metadata?.generated));
      this.lastIngestion.set(this.date(data.metadata?.last_ingestion));
      this.updateStale(data.metadata?.last_ingestion ?? null, Number(config.refreshMs) || 60000);
      this.status.set(config.mode === 'demo' ? 'Ejemplo estático: no representa actividad real' : 'API accesible · consulta completada');
      if (config.mode === 'api') await this.loadStats(config, headers, qs);
    } catch {
      if (!this.destroyed) this.status.set('No se pudo actualizar: se conserva la última lectura. Revisa API, túnel y CORS.');
    } finally {
      if (!this.destroyed && config.mode === 'api') this.timer = setTimeout(() => void this.refresh(), Math.max(30000, Number(config.refreshMs) || 60000));
    }
  }

  private async loadStats(config: Config, headers: Record<string, string>, qs: string): Promise<void> {
    if (this.truncated()) {
      this.statsSummary.set('Estadísticas omitidas: la respuesta de eventos está truncada.');
      this.statsAvisos.set([]);
      this.statsCountries.set([]);
      this.statsMag.set([]);
      this.statsDepth.set([]);
      return;
    }
    try {
      const stats = await this.readJson<{
        resumen?: { total?: number; ultima_hora?: number; sin_magnitud?: number; sin_pais?: number; media_por_dia?: number; dias_cero?: number };
        por_pais?: CountryRow[];
        por_hora?: { hora: string; count: number }[];
        distribuciones?: { magnitud?: BandRow[]; profundidad_km?: BandRow[] };
        comparacion_historica?: {
          delta?: number;
          referencia_2025?: { media_diaria?: number; total?: number };
        };
        avisos?: string[];
      }>(`${config.apiUrl.replace(/\/$/, '')}/api/estadisticas${qs}`, headers);
      const r = stats.resumen ?? {};
      const ref = stats.comparacion_historica?.referencia_2025;
      this.statsSummary.set(
        `Total ${r.total ?? 0} · última hora UTC ${r.ultima_hora ?? 0} · media/día periodo ${r.media_por_dia ?? 'ND'} · días cero ${r.dias_cero ?? 0}` +
        (ref?.media_diaria !== undefined ? ` · media diaria 2025 (mismos filtros) ${ref.media_diaria}` : '') +
        (stats.comparacion_historica?.delta !== undefined ? ` · Δ vs ventana anterior ${stats.comparacion_historica.delta}` : '')
      );
      this.statsAvisos.set(stats.avisos ?? []);
      const countries = stats.por_pais ?? [];
      const mag = stats.distribuciones?.magnitud ?? [];
      const depth = stats.distribuciones?.profundidad_km ?? [];
      const hours = (stats.por_hora ?? []).slice(-24);
      this.statsCountries.set(countries.slice(0, 12));
      this.statsMag.set(mag);
      this.statsDepth.set(depth);
      this.statsHour.set(hours);
      this.statsMagMax.set(Math.max(1, ...mag.map((x) => x.count)));
      this.statsDepthMax.set(Math.max(1, ...depth.map((x) => x.count)));
      this.statsHourMax.set(Math.max(1, ...hours.map((x) => x.count)));
    } catch {
      this.statsSummary.set('No se pudieron cargar las estadísticas');
    }
  }

  private date(value: unknown): string {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'ND';
    const d = new Date(value); return Number.isNaN(d.getTime()) ? 'ND' : d.toISOString();
  }
  ngOnDestroy(): void { this.destroyed = true; clearTimeout(this.timer); this.controller.abort(); }
}
