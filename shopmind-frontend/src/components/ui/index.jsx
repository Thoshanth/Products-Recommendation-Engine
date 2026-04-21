// src/components/ui/index.jsx — Shared UI primitives

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import clsx from 'clsx'

// ── Button ────────────────────────────────────────────────────────────────────
export function Button({ children, variant = 'primary', size = 'md', loading, disabled, className, ...props }) {
    const base = 'inline-flex items-center justify-center gap-2 font-medium transition-all duration-200 rounded-[var(--radius-sm)] select-none'
    const variants = {
        primary: 'bg-[var(--accent)] text-[var(--text-inverse)] hover:bg-[var(--accent-dim)] shadow-[var(--shadow-accent)] disabled:opacity-50',
        secondary: 'bg-[var(--bg-raised)] text-[var(--text-primary)] border border-[var(--border)] hover:border-[var(--border-accent)] hover:bg-[var(--bg-hover)]',
        ghost: 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-glass)]',
        danger: 'bg-[var(--error)] text-white hover:opacity-90',
        outline: 'border border-[var(--accent)] text-[var(--accent)] hover:bg-[var(--accent-subtle)]',
    }
    const sizes = {
        xs: 'px-3 py-1.5 text-xs',
        sm: 'px-4 py-2 text-sm',
        md: 'px-5 py-2.5 text-sm',
        lg: 'px-7 py-3.5 text-base',
    }
    return (
        <button
            className={clsx(base, variants[variant], sizes[size], className)}
            disabled={disabled || loading}
            {...props}
        >
            {loading && <Loader2 size={14} className="animate-spin" />}
            {children}
        </button>
    )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ children, variant = 'default', className }) {
    const variants = {
        default: 'bg-[var(--bg-raised)] text-[var(--text-secondary)] border border-[var(--border)]',
        accent: 'bg-[var(--accent-subtle)] text-[var(--accent)] border border-[var(--border-accent)]',
        success: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
        error: 'bg-red-500/10 text-red-400 border border-red-500/20',
        hot: 'bg-gradient-to-r from-orange-500 to-red-500 text-white border-0',
    }
    return (
        <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium tracking-wide', variants[variant], className)}>
            {children}
        </span>
    )
}

// ── Input ─────────────────────────────────────────────────────────────────────
export function Input({ label, error, icon, className, ...props }) {
    return (
        <div className="flex flex-col gap-1.5">
            {label && <label className="text-xs font-medium text-[var(--text-secondary)] uppercase tracking-wider">{label}</label>}
            <div className="relative">
                {icon && <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">{icon}</span>}
                <input
                    className={clsx(
                        'w-full bg-[var(--bg-raised)] border border-[var(--border)] rounded-[var(--radius-sm)]',
                        'px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-muted)]',
                        'focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]/30',
                        'transition-all duration-200',
                        icon && 'pl-10',
                        error && 'border-[var(--error)]',
                        className
                    )}
                    {...props}
                />
            </div>
            {error && <span className="text-xs text-[var(--error)]">{error}</span>}
        </div>
    )
}

// ── Card ──────────────────────────────────────────────────────────────────────
export function Card({ children, className, hover, ...props }) {
    return (
        <div
            className={clsx(
                'bg-[var(--bg-surface)] border border-[var(--border)] rounded-[var(--radius-md)]',
                hover && 'transition-all duration-300 hover:border-[var(--border-accent)] hover:shadow-[var(--shadow-accent)] hover:-translate-y-0.5',
                className
            )}
            {...props}
        >
            {children}
        </div>
    )
}

// ── Skeleton ──────────────────────────────────────────────────────────────────
export function Skeleton({ className }) {
    return (
        <div
            className={clsx('rounded', className)}
            style={{
                background: 'linear-gradient(90deg, var(--bg-raised) 25%, var(--bg-hover) 50%, var(--bg-raised) 75%)',
                backgroundSize: '400px 100%',
                animation: 'shimmer 1.4s infinite',
            }}
        />
    )
}

// ── Star Rating ───────────────────────────────────────────────────────────────
export function Stars({ rating, count, size = 12 }) {
    const full = Math.floor(rating)
    const half = rating % 1 >= 0.5
    const empty = 5 - full - (half ? 1 : 0)
    return (
        <span className="inline-flex items-center gap-1">
            <span className="flex">
                {'★'.repeat(full)}
                {half ? '½' : ''}
                {'☆'.repeat(empty)}
            </span>
            <span className="text-[var(--text-muted)]" style={{ fontSize: size * 0.9 }}>
                {rating.toFixed(1)}
            </span>
            {count && (
                <span className="text-[var(--text-muted)]" style={{ fontSize: size * 0.85 }}>
                    ({count.toLocaleString()})
                </span>
            )}
        </span>
    )
}

// ── Price ─────────────────────────────────────────────────────────────────────
export function Price({ selling, mrp, currency = '₹', size = 'md' }) {
    const sizes = { sm: 'text-sm', md: 'text-base', lg: 'text-xl', xl: 'text-2xl' }
    const disc = mrp > selling ? Math.round((mrp - selling) / mrp * 100) : 0
    return (
        <span className="inline-flex items-baseline gap-2 flex-wrap">
            <span className={clsx('font-semibold text-[var(--text-primary)]', sizes[size])}>
                {currency}{selling.toLocaleString('en-IN')}
            </span>
            {disc > 0 && (
                <>
                    <span className="text-sm text-[var(--text-muted)] line-through">
                        {currency}{mrp.toLocaleString('en-IN')}
                    </span>
                    <span className="text-sm font-medium text-[var(--success)]">{disc}% off</span>
                </>
            )}
        </span>
    )
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 20 }) {
    return <Loader2 size={size} className="animate-spin text-[var(--accent)]" />
}

// ── Empty State ───────────────────────────────────────────────────────────────
export function Empty({ icon, title, message, action }) {
    return (
        <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
            {icon && <div className="text-5xl mb-2">{icon}</div>}
            <h3 className="font-display text-xl text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-display)' }}>
                {title}
            </h3>
            {message && <p className="text-sm text-[var(--text-secondary)] max-w-xs">{message}</p>}
            {action}
        </div>
    )
}

// ── Section Header ────────────────────────────────────────────────────────────
export function SectionHeader({ label, title, subtitle, action }) {
    return (
        <div className="flex items-end justify-between mb-8">
            <div>
                {label && (
                    <p className="text-xs font-medium uppercase tracking-[0.15em] text-[var(--accent)] mb-2">{label}</p>
                )}
                <h2 style={{ fontFamily: 'var(--font-display)' }}
                    className="text-2xl md:text-3xl text-[var(--text-primary)] leading-tight">
                    {title}
                </h2>
                {subtitle && <p className="text-sm text-[var(--text-secondary)] mt-1">{subtitle}</p>}
            </div>
            {action}
        </div>
    )
}