import Link from "next/link";
export default function NotFound() {
  return (
    <main className="not-found">
      <p className="eyebrow">404 · Por aquí no era</p>
      <h1>
        Te ganó
        <br />
        el hambre.
      </h1>
      <p>Esta página no está en el menú.</p>
      <Link className="button" href="/">
        Volver a Pepones ↗
      </Link>
    </main>
  );
}
