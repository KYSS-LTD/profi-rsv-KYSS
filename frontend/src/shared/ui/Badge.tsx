import { HTMLAttributes } from 'react';
import { cn } from '../lib/cn';

type BadgeTone = 'neutral' | 'brand' | 'blue' | 'green' | 'amber' | 'red';

const tones: Record<BadgeTone, string> = {
  neutral: 'border-stone-200 bg-stone-50 text-stone-600',
  brand: 'border-brand-200 bg-brand-50 text-brand-700',
  blue: 'border-sky-200 bg-sky-50 text-sky-700',
  green: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  amber: 'border-amber-200 bg-amber-50 text-amber-700',
  red: 'border-red-200 bg-red-50 text-red-700',
};

export function Badge({ tone = 'neutral', className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: BadgeTone }) {
  return (
    <span
      className={cn(
        'inline-flex min-h-7 max-w-full items-center justify-center gap-1 rounded-full border px-3 text-xs font-medium leading-none',
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
