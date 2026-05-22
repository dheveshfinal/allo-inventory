import { useState, useEffect } from "react";
import { Reservation } from "./types";
import { reservationService } from "./reservationService";

export function useReservation(id: number) {
  const [reservation, setReservation] = useState<Reservation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    reservationService.get(id)
      .then((data) => {
        setReservation(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [id]);

  return { reservation, setReservation, loading, error };
}
