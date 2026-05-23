"use client";

import { useWarehouses } from "./useWarehouses";

export function WarehousesPage() {
  const { warehouses, loading, error } = useWarehouses();

  if (loading) return <div className="p-8 text-center">Loading warehouses...</div>;
  if (error) return <div className="p-8 text-center text-red-500">Error: {error}</div>;

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8">Our Warehouses</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {warehouses.map((warehouse) => (
          <div key={warehouse.id} className="border border-gray-200 rounded-lg p-6 shadow-sm bg-gray-50">
            <h2 className="text-xl font-bold mb-2">{warehouse.name}</h2>
            <p className="text-gray-600">{warehouse.location}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
