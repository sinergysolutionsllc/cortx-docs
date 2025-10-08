"use client"

import * as React from "react"
import { Label } from "../label"
import { cn } from "../../utils/cn"

export interface FormFieldProps {
  label: string
  htmlFor: string
  error?: string
  required?: boolean
  description?: string
  className?: string
  children: React.ReactNode
}

export function FormField({
  label,
  htmlFor,
  error,
  required = false,
  description,
  className,
  children,
}: FormFieldProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={htmlFor}>
        {label}
        {required && <span className="ml-1 text-destructive">*</span>}
      </Label>
      {description && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {children}
      {error && (
        <p className="text-sm font-medium text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
