import { fetchApi } from "../../lib/api";
import { Warehouse } from "./types";

export const warehouseService = {
  getWarehouses: () => fetchApi<Warehouse[]>("/warehouses/"),
  getWarehouse: (id: number) => fetchApi<Warehouse>(`/warehouses/${id}`),
};
