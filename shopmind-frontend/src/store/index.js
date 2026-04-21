// src/store/index.js — Zustand global state

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// ── Auth Store ────────────────────────────────────────────────────────────────
export const useAuthStore = create(
    persist(
        (set, get) => ({
            user: null,
            accessToken: null,
            refreshToken: null,
            isLoggedIn: false,

            setAuth: (user, tokens) => {
                localStorage.setItem('access_token', tokens.access_token)
                localStorage.setItem('refresh_token', tokens.refresh_token)
                set({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token, isLoggedIn: true })
            },

            setUser: (user) => set({ user }),

            logout: () => {
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
                set({ user: null, accessToken: null, refreshToken: null, isLoggedIn: false })
            },
        }),
        { name: 'shopmind-auth', partialize: s => ({ user: s.user, isLoggedIn: s.isLoggedIn }) }
    )
)

// ── Cart Store ────────────────────────────────────────────────────────────────
export const useCartStore = create((set, get) => ({
    cart: null,
    isOpen: false,
    isLoading: false,

    setCart: (cart) => set({ cart }),
    openCart: () => set({ isOpen: true }),
    closeCart: () => set({ isOpen: false }),
    toggleCart: () => set(s => ({ isOpen: !s.isOpen })),
    setLoading: (v) => set({ isLoading: v }),

    get itemCount() {
        return get().cart?.item_count ?? 0
    },
}))

// ── UI Store ──────────────────────────────────────────────────────────────────
export const useUIStore = create((set) => ({
    searchQuery: '',
    searchOpen: false,
    mobileMenuOpen: false,

    setSearchQuery: q => set({ searchQuery: q }),
    openSearch: () => set({ searchOpen: true }),
    closeSearch: () => set({ searchOpen: false }),
    toggleMobileMenu: () => set(s => ({ mobileMenuOpen: !s.mobileMenuOpen })),
    closeMobileMenu: () => set({ mobileMenuOpen: false }),
}))