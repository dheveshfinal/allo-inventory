export type ReservationStatus = "pending" | "confirmed" | "released";

export interface Reservation {
  id: number;
  stock_id: number;
  quantity: number;
  status: ReservationStatus;
  expires_at: string;
  created_at: string;
  confirmed_at: string | null;
  released_at: string | null;
  product_name: string;
  warehouse_name: string;
  price: number;
}
