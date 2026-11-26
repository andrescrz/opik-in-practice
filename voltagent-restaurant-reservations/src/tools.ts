import { createTool } from "@voltagent/core";
import { z } from "zod";
import type { ReservationBook } from "./reservations.ts";

const date = z.string().regex(/^\d{4}-\d{2}-\d{2}$/).describe("Date as YYYY-MM-DD");
const time = z.string().regex(/^\d{2}:\d{2}$/).describe("24-hour time as HH:MM");

export const buildTools = (book: ReservationBook) => [
  createTool({
    name: "check_availability",
    description: "Check whether a table for the party is free at a date and time. When nothing fits, returns the nearest bookable times.",
    parameters: z.object({ date, time, party_size: z.number().int().min(1).max(12) }),
    execute: async ({ date, time, party_size }) => book.checkAvailability(date, time, party_size),
  }),
  createTool({
    name: "book_table",
    description: "Create a reservation. Only call after availability was confirmed and the guest asked to book.",
    parameters: z.object({ guest_name: z.string(), date, time, party_size: z.number().int().min(1).max(12) }),
    execute: async ({ guest_name, date, time, party_size }) => book.book(guest_name, date, time, party_size),
  }),
  createTool({
    name: "modify_booking",
    description: "Change the date, time or party size of an existing booking by its id. Omit fields that stay the same.",
    parameters: z.object({
      booking_id: z.string(),
      date: date.optional(),
      time: time.optional(),
      party_size: z.number().int().min(1).max(12).optional(),
    }),
    execute: async ({ booking_id, date, time, party_size }) => book.modify(booking_id, { date, time, partySize: party_size }),
  }),
  createTool({
    name: "cancel_booking",
    description: "Cancel an existing booking by its id.",
    parameters: z.object({ booking_id: z.string() }),
    execute: async ({ booking_id }) => book.cancel(booking_id),
  }),
];
