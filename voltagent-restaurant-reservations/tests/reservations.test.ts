import { describe, expect, it } from "vitest";
import { ReservationBook } from "../src/reservations.ts";

describe("ReservationBook", () => {
  it("offers nearby times when the evening is full for a party of 4", () => {
    const result = new ReservationBook().checkAvailability("2026-12-12", "19:00", 4);
    expect(result.available).toBe(false);
    expect(result).toMatchObject({ alternativeTimes: expect.arrayContaining(["18:30"]) });
  });

  it("seats a party at the smallest free table that fits", () => {
    const result = new ReservationBook().book("Test Guest", "2026-12-13", "20:00", 3);
    expect(result).toMatchObject({ ok: true, booking: { tableId: "T3" } });
  });

  it("refuses a booking that would double-book a table", () => {
    const book = new ReservationBook();
    expect(book.book("A", "2026-12-12", "19:00", 4).ok).toBe(false);
  });

  it("rejects times outside the seating grid", () => {
    expect(new ReservationBook().checkAvailability("2026-12-12", "19:10", 2).available).toBe(false);
  });

  it("modifies a booking and leaves it untouched when the new slot is full", () => {
    const book = new ReservationBook();
    expect(book.modify("LF-1006", { time: "19:30", partySize: 3 })).toMatchObject({ ok: true });
    const failed = book.modify("LF-1001", { partySize: 8 });
    expect(failed.ok).toBe(false);
    expect(book.get("LF-1001")?.partySize).toBe(4);
  });

  it("cancels a booking and frees its table", () => {
    const book = new ReservationBook();
    expect(book.cancel("LF-1003").ok).toBe(true);
    expect(book.checkAvailability("2026-12-12", "19:00", 6).available).toBe(true);
    expect(book.cancel("LF-9999").ok).toBe(false);
  });
});
