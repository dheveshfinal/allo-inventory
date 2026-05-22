import { useEffect, useRef } from "react";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

type WebSocketMessage = 
  | { type: "stock_update"; product_id: number; warehouse_id: number; available: number; stock_id?: number }
  | { type: "reservation_confirmed"; reservation_id: number };

export function useWebSocket(roomId: string, onMessage: (msg: WebSocketMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);

  // Keep the ref updated with the latest callback
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/${roomId}`);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data);
      } catch (e) {
        console.error("Failed to parse websocket message", e);
      }
    };

    ws.onerror = (error) => {
      // Ignore errors that happen when React Strict Mode instantly aborts the connection during mount
      if (ws.readyState !== WebSocket.CLOSED && ws.readyState !== WebSocket.CLOSING) {
        console.error("WebSocket error:", error);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [roomId]);
}
