import { fetchApi } from "../../lib/api";
import { Reservation } from "./types";

export const reservationService = {
  create: (data: { product_id: number; warehouse_id: number; quantity: number }, idempotencyKey?: string) => 
    fetchApi<Reservation>("/reservations/", {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
      body: JSON.stringify(data),
    }),
    
  get: (id: number) => fetchApi<Reservation>(`/reservations/${id}`),
  
  confirm: (id: number, idempotencyKey?: string) => 
    fetchApi<Reservation>(`/reservations/${id}/confirm`, {
      method: "POST",
      headers: idempotencyKey ? { "Idempotency-Key": idempotencyKey } : undefined,
    }),
    
  release: (id: number) => 
    fetchApi<Reservation>(`/reservations/${id}/release`, {
      method: "POST",
    }),
};
