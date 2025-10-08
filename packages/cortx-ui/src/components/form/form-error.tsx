"use client"

import * as React from "react"
import { cn } from "../../utils/cn"

export interface FormErrorProps extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode
}

export function FormError({ className, children, ...props }: FormErrorProps) {
  if (!children) return null

  return (
    <p
      className={cn("text-sm font-medium text-destructive", className)}
      role="alert"
      {...props}
    >
      {children}
    </p>
  )
}
