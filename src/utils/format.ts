import { format, parseISO, isToday, isYesterday } from 'date-fns'

function normalizeDate(date: string | Date): Date | null {
  if (typeof date === 'string') {
    // If the backend returned a naive ISO string (no timezone offset), assume UTC.
    // Example naive form: 2026-08-06T10:08:00
    // If it already has a timezone (Z or ±hh:mm), parse directly.
    const hasOffset = /([zZ]|[+-]\d{2}:?\d{2})$/.test(date)
    const toParse = hasOffset ? date : `${date}Z`
    const d = parseISO(toParse)
    return Number.isNaN(d.getTime()) ? null : d
  }

  return Number.isNaN(date.getTime()) ? null : date
}

export function formatRelativeDate(date: string | Date): string {
  const d = normalizeDate(date)
  if (!d) return 'Unknown time'
  if (isToday(d)) return `Today ${format(d, 'h:mm a')}`
  if (isYesterday(d)) return `Yesterday ${format(d, 'h:mm a')}`
  return format(d, 'MMM d, yyyy · h:mm a')
}

export function formatDate(date: string | Date, pattern = 'MMM d, yyyy'): string {
  const d = normalizeDate(date)
  return d ? format(d, pattern) : 'Unknown date'
}

export function formatDateTime(date: string | Date): string {
  const d = normalizeDate(date)
  return d ? format(d, 'MMM d, yyyy · h:mm a') : 'Unknown time'
}

export function formatCurrency(amount: number, currency = 'INR'): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function formatPercent(value: number, decimals = 0): string {
  return `${value.toFixed(decimals)}%`
}
