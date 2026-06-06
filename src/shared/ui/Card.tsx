import type { HTMLAttributes, ReactNode } from 'react';
import clsx from 'clsx';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
}

export function Card({ children, className, ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-[28px] border border-black/5 bg-tg-secondaryBg p-4 shadow-soft dark:border-white/10',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
