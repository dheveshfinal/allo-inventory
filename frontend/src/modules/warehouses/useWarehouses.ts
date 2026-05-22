import { useState, useEffect } from "react";
import { Warehouse } from "./types";
import { warehouseService } from "./warehouseService";

export function useWarehouses() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    warehouseService.getWarehouses()
      .then((data) => {
        setWarehouses(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return { warehouses, loading, error };
}
