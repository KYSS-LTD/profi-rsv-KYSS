import type { ReactNode } from 'react';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  description: string;
  action?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <header className="mb-5 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow && <p className="text-xs font-bold uppercase tracking-[0.2em] text-tg-link">{eyebrow}</p>}
        <h1 className="mt-2 text-3xl font-black tracking-tight text-tg-text md:text-4xl">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-tg-hint md:text-base">{description}</p>
      </div>
      {action}
    </header>
  );
}
