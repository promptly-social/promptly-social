import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export const cn = (...inputs: ClassValue[]) => {
  return twMerge(clsx(inputs))
}

/**
 * Get the current frontend base URL (protocol + host)
 * Useful for constructing redirect URLs in OAuth flows
 */
export const getFrontendBaseUrl = (): string => {
  if (typeof window === 'undefined') {
    // Fallback for SSR or testing environments
    return 'http://localhost:8080'
  }
  return `${window.location.protocol}//${window.location.host}`
}
