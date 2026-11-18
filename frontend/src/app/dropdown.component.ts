import {
  Component,
  ElementRef,
  HostListener,
  ViewChild,
  computed,
  input,
  output,
  signal,
} from '@angular/core';

export type DropdownOption = { value: string; label: string; short?: string; hint?: string };

let instances = 0;

function plain(text: string): string {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase();
}

@Component({
  selector: 'app-dropdown',
  standalone: true,
  templateUrl: './dropdown.component.html',
  styleUrl: './dropdown.component.css',
})
export class DropdownComponent {
  readonly options = input.required<DropdownOption[]>();
  readonly value = input('');
  readonly label = input('');
  readonly searchable = input(false);
  readonly valueChange = output<string>();

  @ViewChild('trigger', { static: true }) trigger!: ElementRef<HTMLButtonElement>;
  @ViewChild('menu', { static: true }) menu!: ElementRef<HTMLElement>;
  @ViewChild('search') search?: ElementRef<HTMLInputElement>;

  readonly menuId = `dropdown-${instances++}`;
  readonly open = signal(false);
  readonly query = signal('');
  readonly active = signal(0);
  readonly selected = computed(() => this.options().find((o) => o.value === this.value()));
  readonly visible = computed(() => {
    const query = plain(this.query());
    return query ? this.options().filter((o) => plain(o.label).includes(query)) : this.options();
  });

  private lastWidth = typeof window !== 'undefined' ? window.innerWidth : 0;
  private closedAt = 0;

  toggleMenu(event: Event): void {
    event.preventDefault();
    event.stopPropagation();
    // Si acaba de cerrarse por light-dismiss en este mismo tap/click, evitar reabrir
    if (performance.now() - this.closedAt < 250) {
      return;
    }
    if (this.open()) {
      this.close();
    } else {
      this.openMenu();
    }
  }

  openMenu(): void {
    if (this.open()) return;
    try {
      this.menu.nativeElement.showPopover();
    } catch {
      this.open.set(true);
    }
  }

  close(): void {
    if (this.open()) {
      try {
        this.menu.nativeElement.hidePopover();
      } catch {
        this.open.set(false);
      }
    }
  }

  // El menú es un popover nativo: se dibuja por encima de todo sin que lo recorte el
  // panel, así que hay que colocarlo a mano bajo el botón
  onBeforeToggle(event: Event): void {
    const opening = (event as ToggleEvent).newState === 'open';
    this.open.set(opening);
    if (!opening) {
      this.closedAt = performance.now();
      return;
    }
    this.query.set('');
    this.active.set(Math.max(0, this.options().findIndex((o) => o.value === this.value())));
    this.updatePosition();
  }

  private updatePosition(): void {
    if (typeof window === 'undefined') return;
    const box = this.trigger.nativeElement.getBoundingClientRect();
    const maxAllowedWidth = window.innerWidth - 16;
    const width = Math.min(maxAllowedWidth, Math.max(box.width, 200));
    const style = this.menu.nativeElement.style;
    style.width = `${width}px`;
    const fits = box.left + width <= window.innerWidth - 8;
    style.left = `${Math.max(8, fits ? box.left : box.right - width)}px`;

    const spaceBelow = window.innerHeight - box.bottom - 18;
    const spaceAbove = box.top - 18;
    if (spaceBelow < 160 && spaceAbove > spaceBelow) {
      style.top = 'auto';
      style.bottom = `${window.innerHeight - box.top + 6}px`;
      style.maxHeight = `${Math.max(120, Math.min(380, spaceAbove))}px`;
    } else {
      style.bottom = 'auto';
      style.top = `${box.bottom + 6}px`;
      style.maxHeight = `${Math.max(120, Math.min(380, spaceBelow))}px`;
    }
  }

  onToggle(): void {
    if (!this.open()) return;
    // Solo auto-enfocar en pantallas de escritorio (>600px).
    // En móviles, auto-enfocar dispara el teclado virtual de golpe y provoca saltos de viewport.
    if (typeof window !== 'undefined' && window.innerWidth > 600) {
      this.search?.nativeElement.focus();
    }
    this.revealActive();
  }

  onSearch(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
    this.active.set(0);
  }

  @HostListener('keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    if (!this.open()) {
      if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
        this.openMenu();
        event.preventDefault();
      }
      return;
    }
    const step = event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0;
    if (step) {
      const last = this.visible().length - 1;
      this.active.update((index) => Math.max(0, Math.min(last, index + step)));
      this.revealActive();
    } else if (event.key === 'Enter') {
      const option = this.visible()[this.active()];
      if (option) this.pick(option);
    } else if (event.key === 'Escape') {
      this.close();
      this.trigger.nativeElement.focus();
    } else {
      return;
    }
    event.preventDefault();
  }

  pick(option: DropdownOption): void {
    this.valueChange.emit(option.value);
    this.close();
    this.trigger.nativeElement.focus();
  }

  @HostListener('window:resize')
  onWindowResize(): void {
    if (typeof window === 'undefined') return;
    // En móviles el teclado virtual o la barra de direcciones cambian solo el alto.
    // Solo cerramos si realmente cambia el ancho de pantalla (giro de pantalla o resize en escritorio).
    if (window.innerWidth !== this.lastWidth) {
      this.lastWidth = window.innerWidth;
      this.close();
    }
  }

  private revealActive(): void {
    requestAnimationFrame(() =>
      this.menu.nativeElement.querySelector('.active')?.scrollIntoView({ block: 'nearest' })
    );
  }
}
