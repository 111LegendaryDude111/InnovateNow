export function StatusItem({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function OutputBlock({ label, value }) {
  return (
    <article>
      <span>{label}</span>
      <p>{value}</p>
    </article>
  );
}
