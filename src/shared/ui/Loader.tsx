export function Loader() {
  return (
    <div className="grid gap-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-28 animate-pulse rounded-[28px] bg-slate-200/80 dark:bg-white/10" />
      ))}
    </div>
  );
}
