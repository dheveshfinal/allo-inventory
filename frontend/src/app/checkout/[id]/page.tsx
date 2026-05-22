import { ReservationPage } from "../../../modules/reservations/ReservationPage";

export default async function CheckoutRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return <ReservationPage id={id} />;
}