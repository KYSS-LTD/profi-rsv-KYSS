import { InputHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'focus-ring h-10 w-full rounded-xl border border-stone-200 bg-white px-3 text-sm leading-5 text-stone-900 transition-colors placeholder:text-stone-400 hover:border-stone-300 focus-visible:border-brand-400 disabled:bg-stone-50 disabled:text-stone-400',
        className,
      )}
      {...props}
    />
  );
}
