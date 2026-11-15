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

  // El menú es un popover nativo: se dibuja por encima de todo sin que lo recorte el
  // panel, así que hay que colocarlo a mano bajo el botón
  onBeforeToggle(event: Event): void {
    const opening = (event as ToggleEvent).newState === 'open';
    this.open.set(opening);
    if (!opening) return;
    this.query.set('');
    this.active.set(Math.max(0, this.options().findIndex((o) => o.value === this.value())));
    const box = this.trigger.nativeElement.getBoundingClientRect();
    const width = Math.max(box.width, 200);
    const style = this.menu.nativeElement.style;
    style.width = `${width}px`;
    const fits = box.left + width <= window.innerWidth - 8;
    style.left = `${Math.max(8, fits ? box.left : box.right - width)}px`;
    style.top = `${box.bottom + 6}px`;
    style.maxHeight = `${Math.max(120, Math.min(400, window.innerHeight - box.bottom - 18))}px`;
  }

  onToggle(): void {
    if (!this.open()) return;
    this.search?.nativeElement.focus();
    this.revealActive();
  }

  onSearch(event: Event): void {
    this.query.set((event.target as HTMLInputElement).value);
    this.active.set(0);
  }

  @HostListener('keydown', ['$event'])
  onKey(event: KeyboardEvent): void {
    if (!this.open()) return;
    const step = event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0;
    if (step) {
      const last = this.visible().length - 1;
      this.active.update((index) => Math.max(0, Math.min(last, index + step)));
      this.revealActive();
    } else if (event.key === 'Enter') {
      const option = this.visible()[this.active()];
      if (option) this.pick(option);
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
  close(): void {
    if (this.open()) this.menu.nativeElement.hidePopover();
  }

  private revealActive(): void {
    requestAnimationFrame(() =>
      this.menu.nativeElement.querySelector('.active')?.scrollIntoView({ block: 'nearest' })
    );
  }
}
