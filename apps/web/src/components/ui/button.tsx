import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-semibold transition disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--brand)] px-4 py-2.5 text-white hover:bg-[var(--brand-dark)]",
        secondary:
          "border border-[var(--line)] bg-white px-4 py-2.5 hover:border-[var(--brand)]",
        ghost:
          "px-3 py-2 text-[var(--muted)] hover:bg-slate-100 hover:text-[var(--ink)]",
        danger: "px-3 py-2 text-red-700 hover:bg-red-50",
      },
    },
    defaultVariants: {
      variant: "primary",
    },
  },
);

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({ asChild, className, variant, ...props }: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  );
}
