import { fetchApi } from "../../lib/api";
import { Product } from "./types";

export const productService = {
  getProducts: () => fetchApi<Product[]>("/products/"),
  getProduct: (id: number) => fetchApi<Product>(`/products/${id}`),
};
