import { NgTemplateOutlet } from '@angular/common';
import {
  AfterViewInit,
  Component,
  ElementRef,
  NgZone,
  OnDestroy,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import Globe, { type GlobeInstance } from 'globe.gl';
import type { FeatureCollection, Point } from 'geojson';
import {
  CanvasTexture,
  CircleGeometry,
  Group,
  Mesh,
  MeshBasicMaterial,
  SRGBColorSpace,
  Vector3,
  type Object3D,
  type PerspectiveCamera,
  type ShaderMaterial,
} from 'three';

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
type StatsResponse = {
  periodo?: { start?: string; end?: string; dias?: number };
  filtros?: { min_mag?: number | null };
  resumen?: { total?: number; ultima_hora?: number; media_por_dia?: number };
  por_pais?: CountryRow[];
  distribuciones?: { magnitud?: BandRow[]; profundidad_km?: BandRow[] };
  comparacion_historica?: { referencia_2025?: { media_diaria?: number } };
  avisos?: string[];
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
type Band = { band: string; label: string; about: string; color?: string };
type BarInput = { label: string; about: string; count: number; color?: string };
type Bar = { label: string; count: string; share: number; tip: string; color: string };
type StatsView = {
  total: string;
  lastHour: string;
  dailyAvg: string;
  ref2025: string;
  dailyTip: string;
  refTip: string;
  comparable: boolean;
  avisos: string[];
  countries: Bar[];
  mag: Bar[];
  depth: Bar[];
};
type Tip = { text: string; x: number; y: number; flip: boolean };
type EventRow = {
  id: string;
  place: string;
  mag: string;
  depth: string;
  color: string;
  time: string;
  country: string;
};
type QuakeNode = { core: Mesh; wave: Mesh<CircleGeometry, MeshBasicMaterial> };
type GlobePoint = {
  lat: number;
  lng: number;
  baseSize: number;
  color: string;
  label: string;
  phase: number;
  node?: QuakeNode;
};
type CountryLabel = {
  lat: number;
  lng: number;
  rank: number;
  width: number;
  normal: Vector3;
  shown: boolean;
  el: HTMLElement;
};
type Star = { x: number; y: number; size: number; duration: number; delay: number };
type PanelId = 'estado' | 'filtros' | 'stats' | 'eventos';
type StatusLevel = 'ok' | 'warn' | 'error' | 'idle';

const GLOBE_RADIUS = 100;
const MAX_TABLE_ROWS = 300;
// Fracción del radio de la textura donde acaba el disco y donde va el anillo de la onda
const DOT_EDGE = 0.72;
const WAVE_EDGE = 0.87;
const LABEL_ALTITUDE = 0.012;
// Ancho medio por letra del rótulo (10 px en mayúsculas con espaciado)
const LABEL_CHAR_PX = 8;
const NO_DATA = 'ND';
const ROTATE_RESUME_MS = 5500;
// Seno de 60°: más cerca de los polos, acercar hacia el cursor haría girar el globo sobre su eje
const POLAR_ZOOM_LIMIT = 0.87;
// El histórico de 2025 cargado solo contiene terremotos de magnitud 4 o mayor
const HISTORY_MIN_MAG = 4;
const DEPTH_COLORS = { shallow: '#38bdf8', mid: '#6366f1', deep: '#c084fc', unknown: '#94a3b8' };
const MAG_BANDS: Band[] = [
  { band: '<2', label: '< 2', about: 'Magnitud menor que 2' },
  { band: '2-3', label: '2–3', about: 'Magnitud de 2 a menos de 3' },
  { band: '3-4', label: '3–4', about: 'Magnitud de 3 a menos de 4' },
  { band: '4-5', label: '4–5', about: 'Magnitud de 4 a menos de 5' },
  { band: '5-6', label: '5–6', about: 'Magnitud de 5 a menos de 6' },
  { band: '>=6', label: '≥ 6', about: 'Magnitud 6 o mayor' },
  { band: NO_DATA, label: 'S/D', about: 'Sin dato de magnitud' },
];
const DEPTH_BANDS: Band[] = [
  {
    band: '0-70',
    label: '< 70 km',
    about: 'Foco superficial, a menos de 70 km bajo la superficie',
    color: DEPTH_COLORS.shallow,
  },
  {
    band: '70-300',
    label: '70–300 km',
    about: 'Foco intermedio, entre 70 y 300 km bajo la superficie',
    color: DEPTH_COLORS.mid,
  },
  {
    band: '>=300',
    label: '≥ 300 km',
    about: 'Foco profundo, a 300 km o más bajo la superficie',
    color: DEPTH_COLORS.deep,
  },
  {
    band: NO_DATA,
    label: 'Sin dato',
    about: 'Profundidad no publicada por USGS',
    color: DEPTH_COLORS.unknown,
  },
];
const REF_TIP =
  'Media de terremotos por día en 2025 con los mismos filtros. Sirve de referencia para saber si el periodo es más o menos activo de lo habitual.';
const REF_LIMITED =
  'El histórico de 2025 solo contiene terremotos de magnitud 4 o mayor, así que su media no es comparable con la del periodo. Para comparar muestras equivalentes, filtra por magnitud mínima 4.';
const EMPTY_STATS: StatsView = {
  total: '—',
  lastHour: '—',
  dailyAvg: '—',
  ref2025: '—',
  dailyTip: 'Media de terremotos por día en el periodo.',
  refTip: REF_TIP,
  comparable: true,
  avisos: [],
  countries: [],
  mag: [],
  depth: toBars(DEPTH_BANDS.map((band) => ({ ...band, count: 0 })), null),
};

function quakes(count: number): string {
  return count === 1 ? '1 terremoto' : `${count} terremotos`;
}

// Cada barra pesa según el mayor recuento; sin total (estadísticas no disponibles)
// queda solo la descripción, que sirve de leyenda
function toBars(items: BarInput[], total: number | null): Bar[] {
  const max = Math.max(1, ...items.map((item) => item.count));
  return items.map(({ label, about, count, color }) => {
    const percent = total ? Math.round((count / total) * 100) : 0;
    return {
      label,
      color: color ?? '',
      count: total === null ? '—' : String(count),
      share: total === null ? 0 : count / max,
      tip: total === null ? `${about}.` : `${about}: ${quakes(count)} (${percent} % del periodo).`,
    };
  });
}

// Bandas fijas: las que la API no devuelve cuentan 0 y siguen a la vista
function bandBars(bands: Band[], rows: BandRow[] | undefined, total: number): Bar[] {
  const counts = new Map((rows ?? []).map((row) => [row.banda, row.count]));
  return toBars(
    bands.map((band) => ({ ...band, count: counts.get(band.band) ?? 0 })),
    total
  );
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NgTemplateOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent implements AfterViewInit, OnDestroy {
  @ViewChild('globeHost', { static: true }) globeHost!: ElementRef<HTMLDivElement>;

  readonly starField: Star[] = Array.from({ length: 420 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: 0.8 + Math.random() * 2.2,
    duration: 1.4 + Math.random() * 4.2,
    delay: Math.random() * 6,
  }));

  readonly mode = signal('…');
  readonly status = signal('Cargando');
  readonly apiFailed = signal(false);
  readonly lastRead = signal('—');
  readonly generated = signal('—');
  readonly lastIngestion = signal('—');
  readonly period = signal('—');
  readonly refreshSeconds = signal(60);
  readonly tip = signal<Tip | null>(null);
  readonly staleWarning = signal('');
  readonly count = signal(0);
  readonly total = signal(0);
  readonly omitted = signal(0);
  readonly truncated = signal(false);
  readonly startLocal = signal('');
  readonly endLocal = signal('');
  readonly minMag = signal<number | null>(null);
  readonly countryId = signal('');
  readonly stats = signal<StatsView>(EMPTY_STATS);
  readonly eventRows = signal<EventRow[]>([]);
  readonly collapsed = signal<Record<PanelId, boolean>>({
    estado: false,
    filtros: false,
    stats: false,
    eventos: false,
  });

  readonly statusLevel = computed<StatusLevel>(() => {
    if (this.apiFailed()) return 'error';
    if (this.status() === 'Cargando') return 'idle';
    return this.staleWarning() || this.truncated() ? 'warn' : 'ok';
  });
  readonly warnings = computed(() => {
    const list: string[] = [];
    if (this.apiFailed()) list.push('La API o el túnel no responden. Se mantiene la última lectura correcta.');
    if (this.staleWarning()) list.push(this.staleWarning());
    if (this.truncated()) {
      list.push(`Respuesta truncada: se muestran ${this.count()} de ${this.total()} terremotos.`);
    }
    return list;
  });

  private readonly zone = inject(NgZone);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly dateFormat = new Intl.DateTimeFormat('es-ES', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
  private readonly disc = new CircleGeometry(1, 48);
  private readonly dotMaterials = new Map<string, MeshBasicMaterial>();
  private waveTexture?: CanvasTexture;

  private globe?: GlobeInstance;
  private glow?: Object3D;
  private timer?: ReturnType<typeof setTimeout>;
  private frame = 0;
  private dragging = false;
  private hovering = false;
  private pointerOver = false;
  private rotateAfter = 0;
  private controller = new AbortController();
  private destroyed = false;
  private config?: Config;
  private points: GlobePoint[] = [];
  private labels: CountryLabel[] = [];
  private labelsPlacedAt = 0;
  private viewportHeight = 1;
  private auraRadius = 0;
  private onResize = () => this.resizeGlobe();
  private onPointerDown = () => {
    this.dragging = true;
    this.pointerOver = true;
  };
  private trackPointer = (event: PointerEvent) => {
    this.pointerOver = event.type !== 'pointerleave';
  };
  private onPointerUp = () => {
    if (!this.dragging) return;
    this.dragging = false;
    this.rotateAfter = performance.now() + ROTATE_RESUME_MS;
  };

  ngAfterViewInit(): void {
    this.zone.runOutsideAngular(() => this.createGlobe());
    void this.loadCountries();
    void this.bootstrap();
  }

  isCollapsed(id: PanelId): boolean {
    return this.collapsed()[id];
  }

  toggle(id: PanelId): void {
    this.collapsed.update((state) => ({ ...state, [id]: !state[id] }));
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

  clearFilters(): void {
    this.startLocal.set('');
    this.endLocal.set('');
    this.minMag.set(null);
    this.countryId.set('');
    this.applyFilters();
  }

  // Ayuda flotante de los elementos con data-tip: sale al lado del panel, hacia el globo,
  // para no tapar su contenido
  showTip(event: Event): void {
    const target = (event.target as Element).closest<HTMLElement>('[data-tip]');
    const panel = target?.closest('.panel')?.getBoundingClientRect();
    if (!target || !panel) {
      this.tip.set(null);
      return;
    }
    const box = target.getBoundingClientRect();
    const flip = panel.left + panel.width / 2 > window.innerWidth / 2;
    this.tip.set({
      text: target.dataset['tip'] ?? '',
      x: flip ? panel.left - 10 : panel.right + 10,
      y: Math.max(60, Math.min(window.innerHeight - 60, box.top + box.height / 2)),
      flip,
    });
  }

  private createGlobe(): void {
    const el = this.globeHost.nativeElement;
    this.globe = new Globe(el, { animateIn: false, waitForGlobeReady: true })
      .globeImageUrl(this.flatTexture('#0a1628'))
      .backgroundColor('rgba(0,0,0,0)')
      .showAtmosphere(true)
      .atmosphereColor('#3b9dff')
      .atmosphereAltitude(0.3)
      .polygonsData([])
      .polygonCapColor(() => '#0a1628')
      .polygonSideColor(() => '#0a1628')
      .polygonStrokeColor(() => 'rgba(125, 211, 252, 0.55)')
      .polygonAltitude(0.004)
      .polygonsTransitionDuration(0)
      .objectsData([])
      .objectAltitude(0.01)
      .objectThreeObject((d: object) => this.buildQuake(d as GlobePoint))
      .objectLabel('label')
      .onObjectHover((quake: object | null) => {
        this.hovering = Boolean(quake);
      })
      .htmlElementsData([])
      .htmlAltitude(LABEL_ALTITUDE)
      .htmlElement((d: object) => (d as CountryLabel).el)
      .htmlTransitionDuration(0);

    const controls = this.globe.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.55;
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = GLOBE_RADIUS * 1.2;
    controls.maxDistance = GLOBE_RADIUS * 6;
    el.addEventListener('pointerdown', this.onPointerDown);
    el.addEventListener('pointermove', this.trackPointer, { passive: true });
    el.addEventListener('pointerleave', this.trackPointer);
    window.addEventListener('pointerup', this.onPointerUp);
    window.addEventListener('pointercancel', this.onPointerUp);

    this.globe.pointOfView({ lat: 18, lng: 5, altitude: 2.15 }, 0);
    this.resizeGlobe();
    window.addEventListener('resize', this.onResize);
    this.frame = requestAnimationFrame(this.animate);
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

  // lighten mezcla el color con blanco (0 = color puro, 1 = blanco)
  private rgba(hex: string, alpha: number, lighten = 0): string {
    const n = parseInt(hex.slice(1), 16);
    const channel = (shift: number) =>
      Math.round(((n >> shift) & 255) * (1 - lighten) + 255 * lighten);
    return `rgba(${channel(16)}, ${channel(8)}, ${channel(0)}, ${alpha})`;
  }

  private radialTexture(stops: [number, string][]): CanvasTexture {
    const size = 128;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d')!;
    const gradient = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    for (const [offset, color] of stops) gradient.addColorStop(offset, color);
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);
    const texture = new CanvasTexture(canvas);
    texture.colorSpace = SRGBColorSpace;
    return texture;
  }

  // Disco nítido hasta DOT_EDGE del radio, con borde claro y un halo tenue alrededor
  private dotMaterial(color: string): MeshBasicMaterial {
    let material = this.dotMaterials.get(color);
    if (!material) {
      const map = this.radialTexture([
        [0, this.rgba(color, 0.95, 0.7)],
        [0.3, this.rgba(color, 0.9, 0.1)],
        [DOT_EDGE - 0.1, this.rgba(color, 0.85)],
        [DOT_EDGE - 0.03, this.rgba(color, 1, 0.5)],
        [DOT_EDGE + 0.02, this.rgba(color, 0.28)],
        [1, this.rgba(color, 0)],
      ]);
      material = new MeshBasicMaterial({ map, transparent: true, depthWrite: false });
      this.dotMaterials.set(color, material);
    }
    return material;
  }

  private buildQuake(point: GlobePoint): Object3D {
    this.waveTexture ??= this.radialTexture([
      [0, 'rgba(255, 255, 255, 0)'],
      [WAVE_EDGE - 0.14, 'rgba(255, 255, 255, 0)'],
      [WAVE_EDGE, 'rgba(255, 255, 255, 1)'],
      [1, 'rgba(255, 255, 255, 0)'],
    ]);
    const core = new Mesh(this.disc, this.dotMaterial(point.color));
    const wave = new Mesh(
      this.disc,
      new MeshBasicMaterial({
        map: this.waveTexture,
        color: point.color,
        transparent: true,
        depthWrite: false,
      })
    );
    wave.raycast = () => {};
    wave.renderOrder = 1;
    core.renderOrder = 2;
    point.node = { core, wave };
    return new Group().add(wave, core);
  }

  private animate = (): void => {
    this.frame = requestAnimationFrame(this.animate);
    if (!this.globe) return;
    const camera = this.globe.camera() as PerspectiveCamera;
    const altitude = camera.position.length() / GLOBE_RADIUS - 1;
    const halfFov = Math.tan((camera.fov * Math.PI) / 360);
    const now = performance.now();
    const time = now / 1000;
    // El giro solo se detiene al pulsar o arrastrar y con el ratón sobre un terremoto.
    // El globo recuerda la última posición del ratón, así que fuera del lienzo no cuenta
    const onQuake = this.hovering && this.pointerOver;
    const controls = this.globe.controls();
    controls.autoRotate = !this.dragging && !onQuake && now > this.rotateAfter;
    controls.zoomToCursor =
      Math.abs(camera.position.y) < camera.position.length() * POLAR_ZOOM_LIMIT;
    this.animateGlow(time, altitude, halfFov);
    this.animateQuakes(time, altitude, halfFov);
    this.placeLabels(altitude, camera);
  };

  // Radio en píxeles casi constante: grandes de lejos y algo menores al acercar
  private animateQuakes(time: number, altitude: number, halfFov: number): void {
    const unitsPerPx =
      (2 * Math.min(altitude, 2.6) * GLOBE_RADIUS * halfFov) / this.viewportHeight;
    const farness = Math.max(0, Math.min(1, (altitude - 0.2) / 2));
    const basePx = 5 + 4 * farness;
    for (const point of this.points) {
      const node = point.node;
      if (!node) continue;
      const radius = point.baseSize * basePx * unitsPerPx;
      const beat = 1 + 0.14 * Math.sin(time * 3 + point.phase);
      node.core.scale.setScalar((radius * beat) / DOT_EDGE);
      const progress = (time / 2.4 + point.phase) % 1;
      node.wave.scale.setScalar((radius * (1 + 2.2 * progress)) / WAVE_EDGE);
      node.wave.material.opacity = 0.9 * (1 - progress) ** 2;
    }
  }

  private animateGlow(time: number, altitude: number, halfFov: number): void {
    if (!this.glow?.parent) this.glow = this.findAtmosphere();
    const material = (this.glow as Mesh | undefined)?.material as ShaderMaterial | undefined;
    if (material?.uniforms) {
      material.uniforms['coefficient'].value = 0.1 + 0.035 * Math.sin(time * 0.9);
      material.uniforms['power'].value = 3.4 + 0.5 * Math.sin(time * 0.55 + 1);
    }
    const radius =
      ((this.viewportHeight / 2) * Math.tan(Math.asin(1 / (1 + altitude)))) / halfFov;
    if (Math.abs(radius - this.auraRadius) > 0.5) {
      this.auraRadius = radius;
      this.host.nativeElement.style.setProperty('--globe-r', `${radius.toFixed(1)}px`);
    }
  }

  private findAtmosphere(): Object3D | undefined {
    let found: Object3D | undefined;
    this.globe?.scene().traverse((obj) => {
      if ((obj as Object3D & { __globeObjType?: string }).__globeObjType === 'atmosphere') {
        found = obj;
      }
    });
    return found;
  }

  // Reparto de rótulos sin solapes: primero los países de mayor rango (LABELRANK de
  // Natural Earth) y los que ya estaban visibles; al acercar entran rangos menores
  private placeLabels(altitude: number, camera: PerspectiveCamera): void {
    const now = performance.now();
    if (!this.globe || now - this.labelsPlacedAt < 150) return;
    this.labelsPlacedAt = now;
    const maxRank = altitude > 1.9 ? 3 : altitude > 1.2 ? 4 : altitude > 0.7 ? 5 : 9;
    const toCamera = camera.position.clone().normalize();
    const minFacing = GLOBE_RADIUS / camera.position.length() + 0.1;
    const candidates = this.labels
      .filter((label) => label.rank <= maxRank && label.normal.dot(toCamera) > minFacing)
      .sort((a, b) => a.rank - b.rank || Number(b.shown) - Number(a.shown));

    const placed: { x: number; y: number; width: number }[] = [];
    const visible = new Set<CountryLabel>();
    for (const label of candidates) {
      const { x, y } = this.globe.getScreenCoords(label.lat, label.lng, LABEL_ALTITUDE);
      const free = placed.every(
        (other) =>
          Math.abs(other.x - x) > (other.width + label.width) / 2 || Math.abs(other.y - y) > 18
      );
      if (!free) continue;
      placed.push({ x, y, width: label.width });
      visible.add(label);
    }
    for (const label of this.labels) {
      const show = visible.has(label);
      if (show === label.shown) continue;
      label.shown = show;
      label.el.classList.toggle('shown', show);
    }
  }

  private resizeGlobe(): void {
    if (!this.globe) return;
    const el = this.globeHost.nativeElement;
    this.viewportHeight = Math.max(1, el.clientHeight);
    this.globe.width(el.clientWidth);
    this.globe.height(el.clientHeight);
  }

  private buildLabel(props: Record<string, unknown>): CountryLabel[] {
    const name = String(props['NAME_ES'] ?? props['NAME'] ?? '');
    const lat = Number(props['LABEL_Y']);
    const lng = Number(props['LABEL_X']);
    if (!name || !this.globe || !Number.isFinite(lat) || !Number.isFinite(lng)) return [];
    const el = document.createElement('div');
    el.className = 'country-label';
    el.textContent = name;
    const { x, y, z } = this.globe.getCoords(lat, lng, 0);
    return [
      {
        lat,
        lng,
        rank: Number(props['LABELRANK'] ?? 9),
        width: name.length * LABEL_CHAR_PX + 8,
        normal: new Vector3(x, y, z).normalize(),
        shown: false,
        el,
      },
    ];
  }

  private async loadCountries(): Promise<void> {
    try {
      const countries = await this.readJson<FeatureCollection>('datos/paises.geojson');
      const features = countries.features ?? [];
      this.globe?.polygonsData(features);
      this.labels = features.flatMap((feature) => this.buildLabel(feature.properties ?? {}));
      this.globe?.htmlElementsData(this.labels);
    } catch {
      /* sin fronteras dibujadas; el globo sigue usable */
    }
  }

  private async bootstrap(): Promise<void> {
    try {
      const config = await this.readJson<Config>('config.json');
      if (!['demo', 'api'].includes(config.mode)) throw new Error('Modo inválido');
      this.config = config;
      this.refreshSeconds.set(Math.round(Math.max(30000, Number(config.refreshMs) || 60000) / 1000));
      const replay = config.dataMode === 'replay';
      this.mode.set(config.mode === 'demo' ? 'DEMO' : replay ? 'REPRODUCCIÓN' : 'LIVE');
      await this.refresh();
    } catch {
      this.status.set('Sin config.json');
      this.apiFailed.set(true);
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

  private updateStale(lastIngestionMs: number | null | undefined): void {
    if (typeof lastIngestionMs !== 'number' || !Number.isFinite(lastIngestionMs)) {
      this.staleWarning.set('No consta ninguna ingesta de USGS.');
      return;
    }
    const ageMs = Date.now() - lastIngestionMs;
    const threshold = Math.max(180000, this.refreshSeconds() * 3000);
    this.staleWarning.set(
      ageMs > threshold
        ? `Datos desactualizados: la última ingesta fue hace ${Math.round(ageMs / 60000)} min.`
        : ''
    );
  }

  private depthColor(depth: number | null): string {
    if (depth === null) return DEPTH_COLORS.unknown;
    if (depth < 70) return DEPTH_COLORS.shallow;
    if (depth < 300) return DEPTH_COLORS.mid;
    return DEPTH_COLORS.deep;
  }

  private escape(text: string): string {
    return text.replace(/[&<>"']/g, (ch) => `&#${ch.charCodeAt(0)};`);
  }

  private quakeCard(row: EventRow): string {
    const shown = (value: string) => (value === NO_DATA ? 'Sin dato' : value);
    return [
      '<div class="quake-card">',
      `<strong>${this.escape(row.place)}</strong>`,
      '<dl>',
      `<dt>Magnitud</dt><dd class="mag">${shown(row.mag)}</dd>`,
      `<dt>Profundidad</dt><dd class="depth" style="--depth: ${row.color}">${shown(row.depth)}</dd>`,
      `<dt>Fecha</dt><dd class="time">${row.time}</dd>`,
      `<dt>País</dt><dd class="country">${this.escape(row.country)}</dd>`,
      '</dl>',
      `<small>ID ${this.escape(row.id)}</small>`,
      '</div>',
    ].join('');
  }

  // Fase estable por evento para que el pulso no salte en cada refresco
  private phaseOf(id: string): number {
    let hash = 0;
    for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) % 6283;
    return hash / 1000;
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
        const [lon, lat, rawDepth] = c;
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
        const id = String(feature.id ?? 'ND');
        const magnitude = typeof p.mag === 'number' && Number.isFinite(p.mag) ? p.mag : null;
        const depth = typeof rawDepth === 'number' && Number.isFinite(rawDepth) ? rawDepth : null;
        const row: EventRow = {
          id,
          place: p.place ?? 'Sin descripción',
          mag: magnitude === null ? NO_DATA : magnitude.toFixed(1),
          depth: depth === null ? NO_DATA : `${Math.round(depth)} km`,
          color: this.depthColor(depth),
          time: this.date(p.time),
          country: p.country_name ?? 'Sin país asignado',
        };
        rows.push(row);
        points.push({
          lat,
          lng: lon,
          baseSize:
            magnitude === null ? 0.95 : Math.max(0.75, Math.min(2.1, 0.75 + (magnitude + 1) * 0.15)),
          color: row.color,
          label: this.quakeCard(row),
          phase: this.phaseOf(id),
        });
      }

      this.points = points;
      this.globe?.objectsData(points);
      this.count.set(points.length);
      this.total.set(data.metadata?.total ?? points.length);
      this.omitted.set(omitted);
      this.eventRows.set(rows.slice(0, MAX_TABLE_ROWS));
      this.truncated.set(Boolean(data.metadata?.truncated));
      this.lastRead.set(this.date(Date.now()));
      this.generated.set(this.date(data.metadata?.generated));
      this.lastIngestion.set(this.date(data.metadata?.last_ingestion));
      this.updateStale(data.metadata?.last_ingestion ?? null);
      this.apiFailed.set(false);
      this.status.set(config.mode === 'demo' ? 'Demo' : 'Conectada');
      if (config.mode === 'api') await this.loadStats(config, headers, qs);
    } catch {
      if (!this.destroyed) {
        this.apiFailed.set(true);
        this.status.set('Sin respuesta');
      }
    } finally {
      if (!this.destroyed && config.mode === 'api') {
        this.timer = setTimeout(() => void this.refresh(), this.refreshSeconds() * 1000);
      }
    }
  }

  private async loadStats(
    config: Config,
    headers: Record<string, string>,
    qs: string
  ): Promise<void> {
    if (this.truncated()) {
      this.stats.set({
        ...EMPTY_STATS,
        avisos: ['Respuesta truncada: no se calculan estadísticas globales sobre una muestra.'],
      });
      return;
    }
    try {
      const data = await this.readJson<StatsResponse>(
        `${config.apiUrl.replace(/\/$/, '')}/api/estadisticas${qs}`,
        headers
      );
      const summary = data.resumen ?? {};
      const total = summary.total ?? 0;
      const ref = data.comparacion_historica?.referencia_2025?.media_diaria;
      const comparable = (data.filtros?.min_mag ?? -Infinity) >= HISTORY_MIN_MAG;
      const avisos = data.avisos ?? [];
      const countries = (data.por_pais ?? []).slice(0, 5).map((row) => ({
        label: row.country_name,
        about:
          row.country_id === 'SIN_PAIS'
            ? 'Sin país asignado (en el mar o fuera de cualquier frontera)'
            : row.country_name,
        count: row.count,
      }));
      this.stats.set({
        total: String(total),
        lastHour: String(summary.ultima_hora ?? 0),
        dailyAvg:
          typeof summary.media_por_dia === 'number' ? summary.media_por_dia.toFixed(1) : '—',
        ref2025: typeof ref === 'number' ? ref.toFixed(1) : '—',
        dailyTip: `Terremotos del periodo divididos entre los días naturales (UTC) que abarca: ${data.periodo?.dias ?? 1}.`,
        refTip: comparable ? REF_TIP : REF_LIMITED,
        comparable,
        avisos: comparable ? avisos : [...avisos, REF_LIMITED],
        countries: toBars(countries, total),
        mag: bandBars(MAG_BANDS, data.distribuciones?.magnitud, total),
        depth: bandBars(DEPTH_BANDS, data.distribuciones?.profundidad_km, total),
      });
      const start = Date.parse(data.periodo?.start ?? '');
      const end = Date.parse(data.periodo?.end ?? '');
      this.period.set(`${this.date(start)} – ${this.date(end)}`);
    } catch {
      this.stats.set({ ...EMPTY_STATS, avisos: ['No se han podido cargar las estadísticas.'] });
    }
  }

  private date(value: unknown): string {
    if (typeof value !== 'number' || !Number.isFinite(value)) return 'ND';
    return this.dateFormat.format(new Date(value));
  }

  ngOnDestroy(): void {
    this.destroyed = true;
    clearTimeout(this.timer);
    cancelAnimationFrame(this.frame);
    this.controller.abort();
    window.removeEventListener('resize', this.onResize);
    window.removeEventListener('pointerup', this.onPointerUp);
    window.removeEventListener('pointercancel', this.onPointerUp);
    const el = this.globeHost.nativeElement;
    el.removeEventListener('pointerdown', this.onPointerDown);
    el.removeEventListener('pointermove', this.trackPointer);
    el.removeEventListener('pointerleave', this.trackPointer);
    try {
      (this.globe as { _destructor?: () => void } | undefined)?._destructor?.();
    } catch {
      /* ignore */
    }
  }
}
