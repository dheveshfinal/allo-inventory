import { Warehouse } from "../warehouses/types";

export interface StockInfo {
  warehouse: Warehouse;
  total_units: number;
  reserved_units: number;
  available_units: number;
}

export interface Product {
  id: number;
  name: string;
  description: string | null;
  sku: string;
  price: number;
  stocks: StockInfo[];
}
