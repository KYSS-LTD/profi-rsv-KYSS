import { TextareaHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        'focus-ring min-h-24 w-full resize-y rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm leading-6 text-stone-900 transition-colors placeholder:text-stone-400 hover:border-stone-300 focus-visible:border-brand-400 disabled:bg-stone-50 disabled:text-stone-400',
        className,
      )}
      {...props}
    />
  );
}
