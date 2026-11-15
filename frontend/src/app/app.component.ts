import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, signal } from '@angular/core';
import Globe, { type GlobeInstance } from 'globe.gl';
import type { Feature, FeatureCollection, Geometry, Point, Position } from 'geojson';

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
type GlobePoint = {
  lat: number;
  lng: number;
  baseSize: number;
  color: string;
  label: string;
  phase: number;
};
type CountryLabel = { lat: number; lng: number; name: string };
type Star = { x: number; y: number; size: number; duration: number; delay: number };
type PanelId = 'tl' | 'tr' | 'bl' | 'br';

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements AfterViewInit, OnDestroy {
  @ViewChild('globeHost', { static: true }) globeHost!: ElementRef<HTMLDivElement>;

  readonly starField: Star[] = Array.from({ length: 280 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: 0.8 + Math.random() * 2.6,
    duration: 1.4 + Math.random() * 4.2,
    delay: Math.random() * 6,
  }));

  readonly mode = signal('Cargando…');
  readonly status = signal('Preparando globo');
  readonly lastRead = signal('—');
  readonly generated = signal('—');
  readonly lastIngestion = signal('—');
  readonly staleWarning = signal('');
  readonly count = signal(0);
  readonly omitted = signal(0);
  readonly truncated = signal(false);
  readonly startLocal = signal('');
  readonly endLocal = signal('');
  readonly minMag = signal<number | null>(null);
  readonly countryId = signal('');
  readonly statsTotal = signal('—');
  readonly statsLastHour = signal('—');
  readonly statsDailyAvg = signal('—');
  readonly statsRef2025 = signal('—');
  readonly statsAvisos = signal<string[]>([]);
  readonly statsCountries = signal<CountryRow[]>([]);
  readonly statsMag = signal<BandRow[]>([]);
  readonly statsDepth = signal<BandRow[]>([]);
  readonly statsMagMax = signal(1);
  readonly statsDepthMax = signal(1);
  readonly eventRows = signal<EventRow[]>([]);
  readonly panelTl = signal(false);
  readonly panelTr = signal(false);
  readonly panelBl = signal(false);
  readonly panelBr = signal(false);

  private globe?: GlobeInstance;
  private timer?: ReturnType<typeof setTimeout>;
  private resumeRotateTimer?: ReturnType<typeof setTimeout>;
  private pulseTimer?: ReturnType<typeof setInterval>;
  private controller = new AbortController();
  private destroyed = false;
  private config?: Config;
  private lastPoints: GlobePoint[] = [];
  private onResize = () => this.resizeGlobe();
  private onControlsChange = () => this.syncVisuals();
  private onUserInteract = () => this.pauseAutoRotate();

  ngAfterViewInit(): void {
    const ocean = this.flatTexture('#0a1628');
    this.globe = new Globe(this.globeHost.nativeElement, {
      animateIn: false,
      waitForGlobeReady: true,
    })
      .globeImageUrl(ocean)
      .backgroundColor('rgba(0,0,0,0)')
      .showAtmosphere(true)
      .atmosphereColor('#38bdf8')
      .atmosphereAltitude(0.28)
      .polygonsData([])
      .polygonCapColor(() => '#0a1628')
      .polygonSideColor(() => '#0a1628')
      .polygonStrokeColor(() => 'rgba(125, 211, 252, 0.55)')
      .polygonAltitude(0.004)
      .polygonsTransitionDuration(0)
      .labelsData([])
      .labelLat('lat')
      .labelLng('lng')
      .labelText('name')
      .labelColor(() => 'rgba(186, 230, 253, 0.82)')
      .labelSize(0.55)
      .labelDotRadius(0)
      .labelAltitude(0.012)
      .labelResolution(2)
      .labelsTransitionDuration(0)
      .htmlElementsData([])
      .htmlLat('lat')
      .htmlLng('lng')
      .htmlAltitude(0.018)
      .htmlElement((d: object) => this.makeQuakeEl(d as GlobePoint))
      .htmlElementVisibilityModifier((el: HTMLElement, visible: boolean) => {
        el.style.opacity = visible ? '1' : '0';
        el.style.pointerEvents = visible ? 'auto' : 'none';
      })
      .htmlTransitionDuration(0)
      .ringsData([])
      .ringColor(() => (t: number) => `rgba(56, 189, 248, ${Math.max(0, 0.5 * (1 - t))})`)
      .ringMaxRadius((d: object) => 0.8 + (d as GlobePoint).baseSize)
      .ringPropagationSpeed(1.8)
      .ringRepeatPeriod(2000)
      .enablePointerInteraction(true);

    const controls = this.globe.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.55;
    controls.enableZoom = true;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 120;
    controls.addEventListener('change', this.onControlsChange);
    controls.addEventListener('start', this.onUserInteract);
    this.globeHost.nativeElement.addEventListener('wheel', this.onUserInteract, { passive: true });
    this.globeHost.nativeElement.addEventListener('pointerdown', this.onUserInteract);

    this.globe.pointOfView({ lat: 18, lng: 5, altitude: 2.15 }, 0);
    this.resizeGlobe();
    window.addEventListener('resize', this.onResize);
    this.pulseTimer = setInterval(() => this.syncVisuals(), 50);
    void this.loadBorders();
    void this.bootstrap();
  }

  togglePanel(id: PanelId): void {
    if (id === 'tl') this.panelTl.update((v) => !v);
    if (id === 'tr') this.panelTr.update((v) => !v);
    if (id === 'bl') this.panelBl.update((v) => !v);
    if (id === 'br') this.panelBr.update((v) => !v);
  }

  onStart(event: Event): void {
    this.startLocal.set((event.target as HTMLInputElement).value);
  }
  onEnd(event: Event): void {
    this.endLocal.set((event.target as HTMLInputElement).value);
  }
  onMinMag(event: Event): void {
    const raw = (event.target as HTMLInputElement).value;
    this.minMag.set(raw === '' ? null : Number(raw));
  }
  onCountry(event: Event): void {
    this.countryId.set((event.target as HTMLInputElement).value.trim().toUpperCase());
  }

  applyFilters(): void {
    clearTimeout(this.timer);
    void this.refresh();
  }

  barWidth(value: number, max: number): number {
    return Math.max(6, Math.round((value / Math.max(max, 1)) * 100));
  }

  private flatTexture(color: string): string {
    const canvas = document.createElement('canvas');
    canvas.width = 8;
    canvas.height = 8;
    const ctx = canvas.getContext('2d');
    if (!ctx) return color;
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, 8, 8);
    return canvas.toDataURL('image/png');
  }

  private altitude(): number {
    return this.globe?.pointOfView()?.altitude ?? 2.2;
  }

  private zoomFactor(): number {
    const alt = this.altitude();
    const t = Math.max(0, Math.min(1, (alt - 0.35) / 2.0));
    return 0.2 + t * 1.15;
  }

  private htmlPx(point: GlobePoint): number {
    const t = Date.now() / 1000;
    const breathe = 1 + 0.22 * Math.sin(t * 3.2 + point.phase);
    return Math.max(7, 11 * point.baseSize * this.zoomFactor() * breathe);
  }

  private makeQuakeEl(point: GlobePoint): HTMLElement {
    const el = document.createElement('div');
    el.className = 'quake';
    el.style.setProperty('--c', point.color);
    el.style.setProperty('--s', `${this.htmlPx(point)}px`);
    el.style.setProperty('--delay', `${(point.phase % 2).toFixed(2)}s`);
    el.title = point.label.replace(/<br\s*\/?>/gi, '\n');
    (el as HTMLElement & { __point?: GlobePoint }).__point = point;
    return el;
  }

  private syncVisuals(): void {
    if (!this.globe) return;
    const t = Date.now() / 1000;
    const breath = 0.24 + 0.1 * (0.5 + 0.5 * Math.sin(t * 1.15));
    this.globe.atmosphereAltitude(breath);
    this.globe.atmosphereColor(
      `rgb(${56 + Math.round(30 * Math.sin(t * 0.9))}, ${160 + Math.round(40 * Math.sin(t * 1.1 + 1))}, 248)`
    );

    if (!this.lastPoints.length) return;
    const nodes = this.globeHost.nativeElement.querySelectorAll('.quake');
    nodes.forEach((node) => {
      const el = node as HTMLElement & { __point?: GlobePoint };
      if (!el.__point) return;
      el.style.setProperty('--s', `${this.htmlPx(el.__point)}px`);
    });
  }

  private pauseAutoRotate(): void {
    const controls = this.globe?.controls();
    if (!controls) return;
    controls.autoRotate = false;
    clearTimeout(this.resumeRotateTimer);
    this.resumeRotateTimer = setTimeout(() => {
      if (!this.destroyed && this.globe) this.globe.controls().autoRotate = true;
    }, 5500);
  }

  private resizeGlobe(): void {
    if (!this.globe) return;
    const el = this.globeHost.nativeElement;
    this.globe.width(el.clientWidth);
    this.globe.height(el.clientHeight);
    this.syncVisuals();
  }

  private featureCentroid(feature: Feature<Geometry>): CountryLabel | null {
    const props = feature.properties as { NAME?: string; ADMIN?: string; LABELRANK?: number } | null;
    const rank = props?.LABELRANK ?? 99;
    if (rank > 4) return null;
    const name = props?.NAME || props?.ADMIN;
    if (!name) return null;

    const geom = feature.geometry;
    if (!geom) return null;
    const rings: Position[][] = [];
    if (geom.type === 'Polygon') rings.push(...geom.coordinates);
    if (geom.type === 'MultiPolygon') {
      for (const poly of geom.coordinates) rings.push(...poly);
    }
    if (!rings.length) return null;

    let best = rings[0];
    let bestLen = best.length;
    for (const ring of rings) {
      if (ring.length > bestLen) {
        best = ring;
        bestLen = ring.length;
      }
    }

    let sx = 0;
    let sy = 0;
    let n = 0;
    for (const pos of best) {
      const [lng, lat] = pos;
      if (!Number.isFinite(lng) || !Number.isFinite(lat)) continue;
      sx += lng;
      sy += lat;
      n++;
    }
    if (!n) return null;
    return { lat: sy / n, lng: sx / n, name };
  }

  private async loadBorders(): Promise<void> {
    try {
      const countries = await this.readJson<FeatureCollection>('datos/paises.geojson');
      const features = countries.features ?? [];
      this.globe?.polygonsData(features);
      const labels = features
        .map((f) => this.featureCentroid(f))
        .filter((x): x is CountryLabel => x !== null);
      this.globe?.labelsData(labels);
    } catch {
      /* sin fronteras dibujadas; el globo sigue usable */
    }
  }

  private async bootstrap(): Promise<void> {
    try {
      const config = await this.readJson<Config>('config.json');
      if (!['demo', 'api'].includes(config.mode)) throw new Error('Modo inválido');
      this.config = config;
      const replay = config.dataMode === 'replay';
      this.mode.set(
        config.mode === 'demo' ? 'DEMO' : replay ? 'REPRODUCCIÓN' : 'LIVE'
      );
      await this.refresh();
    } catch {
      this.status.set('Error en config.json');
    }
  }

  private queryParams(): string {
    const params = new URLSearchParams();
    if (this.startLocal()) params.set('start', new Date(this.startLocal()).toISOString());
    if (this.endLocal()) params.set('end', new Date(this.endLocal()).toISOString());
    if (this.minMag() !== null && Number.isFinite(this.minMag()!)) {
      params.set('min_mag', String(this.minMag()));
    }
    if (this.countryId()) params.set('country_id', this.countryId());
    if (this.config?.dataMode === 'replay') params.set('mode', 'replay');
    const qs = params.toString();
    return qs ? `?${qs}` : '';
  }

  private async readJson<T>(url: string, headers: Record<string, string> = {}): Promise<T> {
    const response = await fetch(url, {
      headers,
      cache: 'no-store',
      signal: AbortSignal.any([this.controller.signal, AbortSignal.timeout(15000)]),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json() as Promise<T>;
  }

  private updateStale(lastIngestionMs: number | null | undefined, refreshMs: number): void {
    if (typeof lastIngestionMs !== 'number' || !Number.isFinite(lastIngestionMs)) {
      this.staleWarning.set('Sin última ingesta de USGS');
      return;
    }
    const ageMs = Date.now() - lastIngestionMs;
    const threshold = Math.max(180000, refreshMs * 3);
    this.staleWarning.set(
      ageMs > threshold
        ? `Datos desactualizados: última ingesta hace ~${Math.round(ageMs / 60000)} min`
        : ''
    );
  }

  private depthColor(depth: number | null, depthOk: boolean): string {
    if (!depthOk) return '#94a3b8';
    if (depth! < 70) return '#38bdf8';
    if (depth! < 300) return '#3b82f6';
    return '#a78bfa';
  }

  private applyPoints(points: GlobePoint[]): void {
    this.lastPoints = points;
    this.globe?.htmlElementsData(points);
    this.globe?.ringsData(points.filter((p) => p.baseSize >= 1.15).slice(0, 40));
    this.syncVisuals();
  }

  private async refresh(): Promise<void> {
    const config = this.config;
    if (!config) return;
    try {
      const qs = this.queryParams();
      const url =
        config.mode === 'demo'
          ? 'datos/terremotos-demo.geojson'
          : `${config.apiUrl.replace(/\/$/, '')}/api/eventos${qs}`;
      const headers: Record<string, string> = {};
      if (config.mode === 'api' && config.skipNgrokWarning) {
        headers['ngrok-skip-browser-warning'] = '1';
      }
      const data = await this.readJson<Events>(url, headers);
      if (this.destroyed) return;
      if (data.type !== 'FeatureCollection' || !Array.isArray(data.features)) {
        throw new Error('Se esperaba FeatureCollection');
      }

      const points: GlobePoint[] = [];
      const rows: EventRow[] = [];
      let omitted = 0;
      for (const feature of data.features) {
        const p = feature.properties;
        const c = feature.geometry?.type === 'Point' ? feature.geometry.coordinates : [];
        const [lon, lat, depth] = c;
        if (
          !p ||
          !Number.isFinite(lon) ||
          !Number.isFinite(lat) ||
          Math.abs(lon) > 180 ||
          Math.abs(lat) > 90
        ) {
          omitted++;
          continue;
        }
        const magnitude = typeof p.mag === 'number' && Number.isFinite(p.mag) ? p.mag : null;
        const depthOk = typeof depth === 'number' && Number.isFinite(depth);
        const label = [
          p.place ?? 'Sin descripción',
          `Mag ${magnitude ?? 'ND'}`,
          `Prof ${depthOk ? depth + ' km' : 'ND'}`,
          this.date(p.time),
          p.country_name ?? 'Sin país asignado',
          String(feature.id ?? 'ND'),
        ].join('<br/>');
        points.push({
          lat,
          lng: lon,
          baseSize: magnitude === null ? 0.95 : Math.max(0.75, Math.min(2.1, 0.75 + (magnitude + 1) * 0.15)),
          color: this.depthColor(depthOk ? depth : null, depthOk),
          label,
          phase: Math.random() * Math.PI * 2,
        });
        rows.push({
          id: String(feature.id ?? 'ND'),
          place: p.place ?? 'Sin descripción',
          mag: magnitude,
          time: this.date(p.time),
          country: p.country_name ?? 'Sin país',
        });
      }

      this.applyPoints(points);
      this.count.set(points.length);
      this.omitted.set(omitted);
      this.eventRows.set(rows.slice(0, 40));
      this.truncated.set(Boolean(data.metadata?.truncated));
      this.lastRead.set(this.date(Date.now()));
      this.generated.set(this.date(data.metadata?.generated));
      this.lastIngestion.set(this.date(data.metadata?.last_ingestion));
      this.updateStale(data.metadata?.last_ingestion ?? null, Number(config.refreshMs) || 60000);
      this.status.set(config.mode === 'demo' ? 'Demo estática' : 'Conectada');
      if (config.mode === 'api') await this.loadStats(config, headers, qs);
    } catch {
      if (!this.destroyed) {
        this.status.set('Fallo API/túnel (se conserva última lectura)');
        if (this.lastPoints.length) this.applyPoints(this.lastPoints);
      }
    } finally {
      if (!this.destroyed && config.mode === 'api') {
        this.timer = setTimeout(
          () => void this.refresh(),
          Math.max(30000, Number(config.refreshMs) || 60000)
        );
      }
    }
  }

  private async loadStats(
    config: Config,
    headers: Record<string, string>,
    qs: string
  ): Promise<void> {
    if (this.truncated()) {
      this.statsTotal.set('—');
      this.statsLastHour.set('—');
      this.statsDailyAvg.set('—');
      this.statsRef2025.set('—');
      this.statsAvisos.set(['Respuesta truncada: sin estadísticas globales']);
      this.statsCountries.set([]);
      this.statsMag.set([]);
      this.statsDepth.set([]);
      return;
    }
    try {
      const stats = await this.readJson<{
        resumen?: {
          total?: number;
          ultima_hora?: number;
          media_por_dia?: number;
          dias_cero?: number;
        };
        por_pais?: CountryRow[];
        distribuciones?: { magnitud?: BandRow[]; profundidad_km?: BandRow[] };
        comparacion_historica?: { referencia_2025?: { media_diaria?: number }; delta?: number };
        avisos?: string[];
      }>(`${config.apiUrl.replace(/\/$/, '')}/api/estadisticas${qs}`, headers);
      const r = stats.resumen ?? {};
      const ref = stats.comparacion_historica?.referencia_2025?.media_diaria;
      this.statsTotal.set(String(r.total ?? 0));
      this.statsLastHour.set(String(r.ultima_hora ?? 0));
      this.statsDailyAvg.set(
        typeof r.media_por_dia === 'number' ? r.media_por_dia.toFixed(1) : '—'
      );
      this.statsRef2025.set(typeof ref === 'number' ? ref.toFixed(1) : '—');
      this.statsAvisos.set(stats.avisos ?? []);
      const mag = stats.distribuciones?.magnitud ?? [];
      const depth = stats.distribuciones?.profundidad_km ?? [];
      this.statsCountries.set((stats.por_pais ?? []).slice(0, 5));
      this.statsMag.set(mag);
      this.statsDepth.set(depth);
      this.statsMagMax.set(Math.max(1, ...mag.map((x) => x.count)));
      this.statsDepthMax.set(Math.max(1, ...depth.map((x) => x.count)));
    } catch {
      this.statsTotal.set('—');
      this.statsLastHour.set('—');
      this.statsDailyAvg.set('—');
      this.statsRef2025.set('—');
    }
  }

  private date(value: unknown): string {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'ND';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return 'ND';
    return (
      d.toLocaleString('es-ES', {
        timeZone: 'UTC',
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }) + ' UTC'
    );
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    clearTimeout(this.timer);
    clearTimeout(this.resumeRotateTimer);
    clearInterval(this.pulseTimer);
    this.controller.abort();
    window.removeEventListener('resize', this.onResize);
    const controls = this.globe?.controls();
    controls?.removeEventListener('change', this.onControlsChange);
    controls?.removeEventListener('start', this.onUserInteract);
    this.globeHost.nativeElement.removeEventListener('wheel', this.onUserInteract);
    this.globeHost.nativeElement.removeEventListener('pointerdown', this.onUserInteract);
    try {
      (this.globe as { _destructor?: () => void } | undefined)?._destructor?.();
    } catch {
      /* ignore */
    }
  }
}
