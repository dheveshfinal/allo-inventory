import { Routes, Route } from 'react-router-dom'
import { ProductsPage } from './modules/products/ProductsPage'
import { WarehousesPage } from './modules/warehouses/WarehousesPage'
import { ReservationPage } from './modules/reservations/ReservationPage'
// Assuming checkout page was dynamic
// import { CheckoutPage } from './modules/checkout/CheckoutPage'

function App() {
  return (
    <div className="min-h-screen bg-neutral-900 text-neutral-100 p-8">
      <header className="mb-8 border-b border-neutral-800 pb-4">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
          Allo Inventory Dashboard
        </h1>
        <nav className="mt-4 flex gap-4 text-sm font-medium">
          <a href="/" className="hover:text-blue-400 transition-colors">Products</a>
          <a href="/warehouses" className="hover:text-blue-400 transition-colors">Warehouses</a>
        </nav>
      </header>
      
      <main>
        <Routes>
          <Route path="/" element={<ProductsPage />} />
          <Route path="/warehouses" element={<WarehousesPage />} />
          <Route path="/checkout/:id" element={<ReservationPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
