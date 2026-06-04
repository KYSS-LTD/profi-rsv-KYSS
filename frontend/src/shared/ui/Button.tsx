import { ButtonHTMLAttributes } from 'react';
import { cn } from '../lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    'border-transparent bg-brand-button text-white shadow-brand-sm hover:shadow-brand hover:brightness-[1.06] active:brightness-95',
  secondary:
    'border-stone-200 bg-white text-stone-800 shadow-card hover:border-stone-300 hover:bg-stone-50 hover:shadow-card-hover',
  ghost: 'border-transparent bg-transparent text-stone-600 hover:bg-stone-100 hover:text-stone-950',
  danger: 'border-red-200 bg-red-50 text-red-700 hover:border-red-300 hover:bg-red-100',
};

const sizes: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-10 px-4 text-sm',
};

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'focus-ring inline-flex items-center justify-center gap-2 rounded-xl border text-center font-medium leading-5 transition-all duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50 disabled:active:scale-100',
        sizes[size],
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}
