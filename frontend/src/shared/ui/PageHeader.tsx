import { ReactNode } from 'react';

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 grid gap-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
      <div className="min-w-0">
        {eyebrow && (
          <span className="mb-3 inline-flex items-center gap-2 rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-brand-700">
            <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
            {eyebrow}
          </span>
        )}
        <h1 className="text-balance text-display font-bold text-gradient-ink">{title}</h1>
        {description && <p className="mt-4 max-w-2xl text-base leading-relaxed text-stone-500">{description}</p>}
      </div>
      {actions && <div className="min-w-0">{actions}</div>}
    </div>
  );
}
