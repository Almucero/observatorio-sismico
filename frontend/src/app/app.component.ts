import { AfterViewInit, Component, ElementRef, OnDestroy, ViewChild, signal } from '@angular/core';
import Globe, { type GlobeInstance } from 'globe.gl';
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
type GlobePoint = {
  lat: number;
  lng: number;
  baseSize: number;
  color: string;
  label: string;
};

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements AfterViewInit, OnDestroy {
  @ViewChild('globeHost', { static: true }) globeHost!: ElementRef<HTMLDivElement>;

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
  readonly statsSummary = signal('—');
  readonly statsAvisos = signal<string[]>([]);
  readonly statsCountries = signal<CountryRow[]>([]);
  readonly statsMag = signal<BandRow[]>([]);
  readonly statsDepth = signal<BandRow[]>([]);
  readonly statsMagMax = signal(1);
  readonly statsDepthMax = signal(1);
  readonly eventRows = signal<EventRow[]>([]);

  private globe?: GlobeInstance;
  private timer?: ReturnType<typeof setTimeout>;
  private resumeRotateTimer?: ReturnType<typeof setTimeout>;
  private controller = new AbortController();
  private destroyed = false;
  private config?: Config;
  private lastPoints: GlobePoint[] = [];
  private onResize = () => this.resizeGlobe();
  private onControlsChange = () => this.syncPointScale();
  private onUserInteract = () => this.pauseAutoRotate();

  ngAfterViewInit(): void {
    const ocean = this.flatTexture('#0b1f3a');
    this.globe = new Globe(this.globeHost.nativeElement, {
      animateIn: false,
      waitForGlobeReady: true,
    })
      .globeImageUrl(ocean)
      .backgroundColor('#020617')
      .showAtmosphere(true)
      .atmosphereColor('#2563eb')
      .atmosphereAltitude(0.16)
      .polygonsData([])
      .polygonCapColor(() => 'rgba(30, 64, 120, 0.92)')
      .polygonSideColor(() => 'rgba(15, 35, 70, 0.65)')
      .polygonStrokeColor(() => '#60a5fa')
      .polygonAltitude(0.004)
      .polygonsTransitionDuration(0)
      .pointsData([])
      .pointAltitude(0.008)
      .pointRadius((d: object) => this.scaledRadius(d as GlobePoint))
      .pointColor('color')
      .pointLabel('label')
      .pointsMerge(false)
      .enablePointerInteraction(true);

    const controls = this.globe.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.28;
    controls.enableZoom = true;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.addEventListener('change', this.onControlsChange);
    controls.addEventListener('start', this.onUserInteract);
    this.globeHost.nativeElement.addEventListener('wheel', this.onUserInteract, { passive: true });
    this.globeHost.nativeElement.addEventListener('pointerdown', this.onUserInteract);

    this.globe.pointOfView({ lat: 18, lng: 5, altitude: 2.15 }, 0);
    this.resizeGlobe();
    window.addEventListener('resize', this.onResize);
    void this.loadBorders();
    void this.bootstrap();
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

  private scaledRadius(point: GlobePoint): number {
    const alt = this.altitude();
    // Más lejos (alt alta) → puntos un poco mayores; cerca → muy pequeños para poder elegir
    const zoomFactor = Math.max(0.045, Math.min(0.22, alt * 0.085));
    return point.baseSize * zoomFactor;
  }

  private syncPointScale(): void {
    if (!this.globe || !this.lastPoints.length) return;
    this.globe.pointRadius((d: object) => this.scaledRadius(d as GlobePoint));
  }

  private pauseAutoRotate(): void {
    const controls = this.globe?.controls();
    if (!controls) return;
    controls.autoRotate = false;
    clearTimeout(this.resumeRotateTimer);
    this.resumeRotateTimer = setTimeout(() => {
      if (!this.destroyed && this.globe) this.globe.controls().autoRotate = true;
    }, 4500);
  }

  private resizeGlobe(): void {
    if (!this.globe) return;
    const el = this.globeHost.nativeElement;
    this.globe.width(el.clientWidth);
    this.globe.height(el.clientHeight);
    this.syncPointScale();
  }

  private async loadBorders(): Promise<void> {
    try {
      const countries = await this.readJson<FeatureCollection>('datos/paises.geojson');
      this.globe?.polygonsData(countries.features ?? []);
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
      this.staleWarning.set('Sin última ingesta');
      return;
    }
    const ageMs = Date.now() - lastIngestionMs;
    const threshold = Math.max(180000, refreshMs * 3);
    this.staleWarning.set(
      ageMs > threshold ? `Ingesta antigua (~${Math.round(ageMs / 60000)} min)` : ''
    );
  }

  private depthColor(depth: number | null, depthOk: boolean): string {
    if (!depthOk) return '#94a3b8';
    if (depth! < 70) return '#38bdf8';
    if (depth! < 300) return '#3b82f6';
    return '#a78bfa';
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
          baseSize: magnitude === null ? 0.55 : Math.max(0.4, Math.min(1.4, 0.4 + (magnitude + 1) * 0.1)),
          color: this.depthColor(depthOk ? depth : null, depthOk),
          label,
        });
        rows.push({
          id: String(feature.id ?? 'ND'),
          place: p.place ?? 'Sin descripción',
          mag: magnitude,
          time: this.date(p.time),
          country: p.country_name ?? 'Sin país',
        });
      }

      this.lastPoints = points;
      this.globe?.pointsData(points);
      this.syncPointScale();
      this.count.set(points.length);
      this.omitted.set(omitted);
      this.eventRows.set(rows.slice(0, 8));
      this.truncated.set(Boolean(data.metadata?.truncated));
      this.lastRead.set(new Date().toISOString());
      this.generated.set(this.date(data.metadata?.generated));
      this.lastIngestion.set(this.date(data.metadata?.last_ingestion));
      this.updateStale(data.metadata?.last_ingestion ?? null, Number(config.refreshMs) || 60000);
      this.status.set(config.mode === 'demo' ? 'Demo estática' : 'API OK');
      if (config.mode === 'api') await this.loadStats(config, headers, qs);
    } catch {
      if (!this.destroyed) {
        this.status.set('Fallo API/túnel · se conserva última lectura');
        if (this.lastPoints.length) {
          this.globe?.pointsData(this.lastPoints);
          this.syncPointScale();
        }
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
      this.statsSummary.set('Truncado: sin stats globales');
      this.statsAvisos.set([]);
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
      this.statsSummary.set(
        `n=${r.total ?? 0} · 1h=${r.ultima_hora ?? 0} · media/d=${r.media_por_dia ?? '—'} · media2025=${ref ?? '—'}`
      );
      this.statsAvisos.set((stats.avisos ?? []).slice(0, 1));
      const mag = stats.distribuciones?.magnitud ?? [];
      const depth = stats.distribuciones?.profundidad_km ?? [];
      this.statsCountries.set((stats.por_pais ?? []).slice(0, 5));
      this.statsMag.set(mag);
      this.statsDepth.set(depth);
      this.statsMagMax.set(Math.max(1, ...mag.map((x) => x.count)));
      this.statsDepthMax.set(Math.max(1, ...depth.map((x) => x.count)));
    } catch {
      this.statsSummary.set('Stats no disponibles');
    }
  }

  private date(value: unknown): string {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'ND';
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? 'ND' : d.toISOString().replace('.000Z', 'Z');
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    clearTimeout(this.timer);
    clearTimeout(this.resumeRotateTimer);
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
