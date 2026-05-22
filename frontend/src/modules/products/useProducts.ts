import { useState, useEffect } from "react";
import { Product } from "./types";
import { productService } from "./productService";
import { useWebSocket } from "../../lib/useWebSocket";

export function useProducts() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    productService.getProducts()
      .then((data) => {
        setProducts(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  useWebSocket("products_room", (msg) => {
    if (msg.type === "stock_update") {
      setProducts((prev) => 
        prev.map((p) => {
          if (p.id === msg.product_id) {
            const newStocks = p.stocks.map((s) => {
              if (s.warehouse.id === msg.warehouse_id) {
                return { ...s, available_units: msg.available };
              }
              return s;
            });
            return { ...p, stocks: newStocks };
          }
          return p;
        })
      );
    }
  });

  return { products, loading, error };
}
