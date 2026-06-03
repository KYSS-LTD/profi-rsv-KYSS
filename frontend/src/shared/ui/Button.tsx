import { ButtonHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
};

const variants: Record<ButtonVariant, string> = {
  primary: 'border-stone-900 bg-stone-900 text-white hover:bg-stone-800',
  secondary: 'border-stone-200 bg-white text-stone-800 hover:border-stone-300 hover:bg-stone-50',
  ghost: 'border-transparent bg-transparent text-stone-600 hover:bg-stone-100 hover:text-stone-950',
  danger: 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100',
};

export function Button({ className, variant = 'primary', type = 'button', ...props }: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-xl border px-4 text-center text-sm font-medium leading-5 transition disabled:cursor-not-allowed disabled:opacity-50',
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
