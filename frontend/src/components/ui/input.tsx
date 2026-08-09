import * as React from "react";

import { cn } from "@/lib/utils";

const Input = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(({ className, ...props }, ref) => (
  <input
    ref={ref}
    className={cn(
      "block w-full rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal",
      className
    )}
    {...props}
  />
));
Input.displayName = "Input";

export { Input };
