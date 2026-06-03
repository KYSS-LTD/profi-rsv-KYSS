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
        {eyebrow && <p className="mb-2 text-xs font-medium uppercase tracking-[0.18em] text-stone-400">{eyebrow}</p>}
        <h1 className="text-balance text-3xl font-semibold tracking-tight text-stone-950 md:text-4xl">{title}</h1>
        {description && <p className="mt-3 max-w-3xl text-sm leading-6 text-stone-500">{description}</p>}
      </div>
      {actions && <div className="min-w-0">{actions}</div>}
    </div>
  );
}
