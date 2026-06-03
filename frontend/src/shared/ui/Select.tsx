import { SelectHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cn(
        'focus-ring h-10 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm leading-none text-stone-900 disabled:bg-stone-50 disabled:text-stone-400',
        className,
      )}
      {...props}
    />
  );
}
