import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useReservation } from "./useReservation";
import { reservationService } from "./reservationService";
import { useWebSocket } from "../../lib/useWebSocket";

export function ReservationPage() {
  const { id } = useParams<{ id: string }>();
  const reservationId = Number(id);
  console.log("Route ID:", id);
  console.log("Parsed Reservation ID:", reservationId);

  if (isNaN(reservationId)) {
    return <div>Invalid reservation ID</div>;
  }
  const { reservation, setReservation, loading, error } = useReservation(reservationId);
  const navigate = useNavigate();

  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Sync countdown timer
  useEffect(() => {
    if (!reservation || reservation.status !== "pending") return;

    const calculateTimeLeft = () => {
      const expiresAt = new Date(reservation.expires_at).getTime();
      const now = new Date().getTime();
      return Math.max(0, Math.floor((expiresAt - now) / 1000));
    };

    setTimeLeft(calculateTimeLeft());

    const interval = setInterval(() => {
      const remaining = calculateTimeLeft();
      setTimeLeft(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [reservation]);

  // Handle WebSocket updates for release
  useWebSocket("products_room", (msg) => {
    // If we receive a message that stock updated and our timer was running out, 
    // it's possible our reservation auto-released. We can re-fetch or optimistically update.
  });

  const handleConfirm = async () => {
    setActionError(null);
    setActionLoading(true);

    try {
      const idempotencyKey = crypto.randomUUID();
      const updated = await reservationService.confirm(reservationId, idempotencyKey);
      setReservation(prev => prev ? { ...prev, ...updated } : null);
    } catch (err: any) {
      if (err.status === 410) {
        setActionError("This reservation has expired.");
        setReservation(prev => prev ? { ...prev, status: "released" } : null);
      } else {
        setActionError(err.message || "Failed to confirm reservation");
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    setActionError(null);
    setActionLoading(true);

    try {
      const updated = await reservationService.release(reservationId);
      setReservation(prev => prev ? { ...prev, ...updated } : null);
    } catch (err: any) {
      setActionError(err.message || "Failed to cancel reservation");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="p-8 text-center flex flex-col items-center justify-center min-h-[50vh]">
    <div className="text-xl font-medium mb-4">Loading reservation...</div>
  </div>;

  if (error) return <div className="p-8 text-center text-red-500 min-h-[50vh] flex items-center justify-center">
    <div className="bg-red-50 border border-red-200 p-6 rounded-lg">Error: {error}</div>
  </div>;
  if (!reservation) return <div className="p-8 text-center min-h-[50vh] flex items-center justify-center">Reservation not found</div>;

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  const isPending = reservation.status === "pending" && timeLeft > 0;
  const isExpired = reservation.status === "released" || (reservation.status === "pending" && timeLeft <= 0);

  return (
    <div className="container mx-auto py-12 px-4 max-w-2xl">
      <div className="border rounded-xl shadow-lg bg-card overflow-hidden">
        <div className={`p-6 text-white ${reservation.status === 'confirmed' ? 'bg-green-600' :
          isExpired ? 'bg-red-600' : 'bg-black'
          }`}>
          <h1 className="text-2xl font-bold flex justify-between items-center">
            <span>Checkout</span>
            {isPending && (
              <span className="font-mono bg-white/20 px-3 py-1 rounded-md text-xl">
                {formatTime(timeLeft)}
              </span>
            )}
            {reservation.status === 'confirmed' && <span>Confirmed</span>}
            {isExpired && <span>Expired / Cancelled</span>}
          </h1>
        </div>

        <div className="p-6">
          {actionError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-6">
              {actionError}
            </div>
          )}

          <div className="space-y-4 text-lg mb-8">
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Item</span>
              <span className="font-medium">{reservation.product_name}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Price</span>
              <span className="font-medium">${reservation.price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-b pb-2">
              <span className="text-gray-500">Warehouse</span>
              <span className="font-medium">{reservation.warehouse_name}</span>
            </div>
            <div className="flex justify-between pt-2">
              <span className="font-bold text-xl">Total</span>
              <span className="font-bold text-xl">${reservation.price.toFixed(2)}</span>
            </div>
          </div>

          <div className="flex gap-4">
            {isPending && (
              <>
                <button
                  onClick={handleCancel}
                  disabled={actionLoading}
                  className="flex-1 px-4 py-3 rounded font-medium border border-gray-300 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={actionLoading}
                  className="flex-1 px-4 py-3 rounded font-medium bg-black text-white hover:bg-gray-800 disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Confirm Purchase'}
                </button>
              </>
            )}
            {reservation.status === 'confirmed' && (
              <button
                onClick={() => navigate('/')}
                className="w-full px-4 py-3 rounded font-medium bg-black text-white hover:bg-gray-800"
              >
                Continue Shopping
              </button>
            )}
            {isExpired && (
              <button
                onClick={() => navigate('/')}
                className="w-full px-4 py-3 rounded font-medium border border-gray-300 hover:bg-gray-50"
              >
                Return to Products
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
