import restaurantData from "../data/restaurant.json" with { type: "json" };
import bookingData from "../data/bookings.json" with { type: "json" };

export type Booking = {
  id: string;
  name: string;
  date: string;
  time: string;
  partySize: number;
  tableId: string;
};

export type Restaurant = typeof restaurantData;

const toMinutes = (hhmm: string): number => {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

const toHHMM = (minutes: number): string =>
  `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;

export class ReservationBook {
  private bookings: Booking[];
  private nextId: number;

  constructor(
    private readonly restaurant: Restaurant = restaurantData,
    initial: Booking[] = bookingData as Booking[]
  ) {
    this.bookings = initial.map((b) => ({ ...b }));
    this.nextId = Math.max(1000, ...initial.map((b) => Number(b.id.split("-")[1]))) + 1;
  }

  list(): Booking[] {
    return this.bookings.map((b) => ({ ...b }));
  }

  get(id: string): Booking | undefined {
    return this.bookings.find((b) => b.id === id);
  }

  isValidSlot(time: string): boolean {
    const { open, lastSeating } = this.restaurant.openingHours;
    const t = toMinutes(time);
    return t >= toMinutes(open) && t <= toMinutes(lastSeating) && (t - toMinutes(open)) % this.restaurant.slotMinutes === 0;
  }

  // Free tables that fit the party, smallest first, ignoring one booking (used when moving it).
  freeTables(date: string, time: string, partySize: number, ignoreId?: string) {
    const start = toMinutes(time);
    const end = start + this.restaurant.seatingDurationMinutes;
    const busy = new Set(
      this.bookings
        .filter((b) => b.date === date && b.id !== ignoreId)
        .filter((b) => {
          const bs = toMinutes(b.time);
          return bs < end && start < bs + this.restaurant.seatingDurationMinutes;
        })
        .map((b) => b.tableId)
    );
    return this.restaurant.tables
      .filter((t) => t.seats >= partySize && !busy.has(t.id))
      .sort((a, b) => a.seats - b.seats);
  }

  checkAvailability(date: string, time: string, partySize: number) {
    if (!this.isValidSlot(time)) {
      return { available: false, reason: `Bookable times are every ${this.restaurant.slotMinutes} minutes from ${this.restaurant.openingHours.open} to ${this.restaurant.openingHours.lastSeating}.` };
    }
    const tables = this.freeTables(date, time, partySize);
    if (tables.length > 0) {
      return { available: true, tables: tables.map((t) => ({ id: t.id, seats: t.seats })) };
    }
    const requested = toMinutes(time);
    const alternatives: string[] = [];
    for (let t = toMinutes(this.restaurant.openingHours.open); t <= toMinutes(this.restaurant.openingHours.lastSeating); t += this.restaurant.slotMinutes) {
      if (this.freeTables(date, toHHMM(t), partySize).length > 0) alternatives.push(toHHMM(t));
    }
    alternatives.sort((a, b) => Math.abs(toMinutes(a) - requested) - Math.abs(toMinutes(b) - requested));
    return { available: false, reason: "No table fits at that time.", alternativeTimes: alternatives.slice(0, 3).sort() };
  }

  book(name: string, date: string, time: string, partySize: number) {
    if (!this.isValidSlot(time)) return { ok: false as const, error: "Invalid time slot." };
    const table = this.freeTables(date, time, partySize)[0];
    if (!table) return { ok: false as const, error: "No table available at that time." };
    const booking: Booking = { id: `LF-${this.nextId++}`, name, date, time, partySize, tableId: table.id };
    this.bookings.push(booking);
    return { ok: true as const, booking: { ...booking } };
  }

  modify(id: string, changes: { date?: string; time?: string; partySize?: number }) {
    const existing = this.get(id);
    if (!existing) return { ok: false as const, error: `No booking ${id}.` };
    const date = changes.date ?? existing.date;
    const time = changes.time ?? existing.time;
    const partySize = changes.partySize ?? existing.partySize;
    if (!this.isValidSlot(time)) return { ok: false as const, error: "Invalid time slot." };
    const table = this.freeTables(date, time, partySize, id)[0];
    if (!table) return { ok: false as const, error: "No table available for the new details; the original booking is unchanged." };
    Object.assign(existing, { date, time, partySize, tableId: table.id });
    return { ok: true as const, booking: { ...existing } };
  }

  cancel(id: string) {
    const index = this.bookings.findIndex((b) => b.id === id);
    if (index === -1) return { ok: false as const, error: `No booking ${id}.` };
    const [removed] = this.bookings.splice(index, 1);
    return { ok: true as const, cancelled: removed };
  }
}
