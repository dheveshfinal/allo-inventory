"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useProducts } from "./useProducts";
import { reservationService } from "../reservations/reservationService";

export function ProductsPage() {
  const { products, loading, error } = useProducts();
  const router = useRouter();
  const [reservingId, setReservingId] = useState<string | null>(null);
  const [reserveError, setReserveError] = useState<string | null>(null);

  if (loading) return <div className="p-8 text-center">Loading products...</div>;
  if (error) return <div className="p-8 text-center text-red-500">Error: {error}</div>;

  const handleReserve = async (productId: number, warehouseId: number) => {
    setReserveError(null);
    const key = `res_${productId}_${warehouseId}`;
    setReservingId(key);
    
    // Generate idempotency key
    const idempotencyKey = crypto.randomUUID();
    
    try {
      const reservation = await reservationService.create({
        product_id: productId,
        warehouse_id: warehouseId,
        quantity: 1
      }, idempotencyKey);
      
      router.push(`/checkout/${reservation.id}`);
    } catch (err: any) {
      if (err.status === 409) {
        setReserveError("Sorry, this item just went out of stock in this warehouse.");
      } else {
        setReserveError(err.message || "Failed to reserve item");
      }
      setReservingId(null);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Available Products</h1>
      
      {reserveError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6">
          {reserveError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {products.map((product) => (
          <div key={product.id} className="border rounded-lg p-6 shadow-sm flex flex-col bg-card">
            <h2 className="text-xl font-bold mb-2">{product.name}</h2>
            <p className="text-gray-600 mb-4 flex-1">{product.description}</p>
            <div className="text-2xl font-bold mb-4">${product.price.toFixed(2)}</div>
            
            <div className="border-t pt-4 mt-auto">
              <h3 className="font-semibold mb-3">Availability by Warehouse:</h3>
              <div className="space-y-3">
                {product.stocks.map((stock) => {
                  const isAvailable = stock.available_units > 0;
                  const key = `res_${product.id}_${stock.warehouse.id}`;
                  const isReserving = reservingId === key;
                  
                  return (
                    <div key={stock.warehouse.id} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{stock.warehouse.name}</div>
                        <div className={`text-sm ${isAvailable ? 'text-green-600' : 'text-red-500'}`}>
                          {stock.available_units} units available
                        </div>
                      </div>
                      <button 
                        onClick={() => handleReserve(product.id, stock.warehouse.id)}
                        disabled={!isAvailable || isReserving}
                        className={`px-4 py-2 rounded font-medium transition-colors ${
                          !isAvailable 
                            ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                            : 'bg-black text-white hover:bg-gray-800'
                        }`}
                      >
                        {isReserving ? 'Reserving...' : 'Reserve'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
