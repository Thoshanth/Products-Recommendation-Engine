// src/components/layout/Navbar.jsx

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ShoppingBag, Search, User, Menu, X, Sparkles, Heart } from 'lucide-react'
import { useAuthStore, useCartStore, useUIStore } from '../../store'
import { authAPI } from '../../services/api'
import toast from 'react-hot-toast'

export default function Navbar() {
    const { user, isLoggedIn, logout, refreshToken } = useAuthStore()
    const { cart, toggleCart, itemCount } = useCartStore()
    const { openSearch, toggleMobileMenu, mobileMenuOpen } = useUIStore()
    const navigate = useNavigate()
    const [userMenuOpen, setUserMenuOpen] = useState(false)

    const cartCount = cart?.item_count ?? 0

    async function handleLogout() {
        try {
            const rt = localStorage.getItem('refresh_token')
            if (rt) await authAPI.logout(rt)
        } catch { }
        logout()
        navigate('/')
        toast.success('Logged out')
        setUserMenuOpen(false)
    }

    const navLinks = [
        { to: '/products', label: 'Catalogue' },
        { to: '/recommendations', label: 'For You' },
        { to: '/products?sort=trending', label: 'Trending' },
    ]

    return (
        <header style={{
            position: 'sticky', top: 0, zIndex: 100,
            height: 'var(--nav-height)',
            background: 'rgba(15,15,15,0.85)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid var(--border)',
        }}>
            <nav style={{
                maxWidth: 'var(--content-max)', margin: '0 auto',
                padding: '0 1.5rem', height: '100%',
                display: 'flex', alignItems: 'center', gap: '2rem',
            }}>
                {/* Logo */}
                <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                    <div style={{
                        width: 32, height: 32, borderRadius: 8,
                        background: 'var(--accent)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                        <Sparkles size={16} color="var(--text-inverse)" strokeWidth={2.5} />
                    </div>
                    <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', letterSpacing: '-0.01em' }}>
                        ShopMind
                    </span>
                </Link>

                {/* Desktop nav links */}
                <div style={{ display: 'flex', gap: '0.25rem', flex: 1 }} className="hidden-mobile">
                    {navLinks.map(l => (
                        <Link
                            key={l.to} to={l.to}
                            style={{
                                padding: '0.5rem 0.875rem', borderRadius: 'var(--radius-sm)',
                                fontSize: '0.875rem', color: 'var(--text-secondary)',
                                transition: 'all 0.15s ease',
                            }}
                            onMouseEnter={e => { e.target.style.color = 'var(--text-primary)'; e.target.style.background = 'var(--bg-glass)' }}
                            onMouseLeave={e => { e.target.style.color = 'var(--text-secondary)'; e.target.style.background = 'transparent' }}
                        >
                            {l.label}
                        </Link>
                    ))}
                </div>

                {/* Right actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginLeft: 'auto' }}>
                    {/* Search */}
                    <button
                        onClick={openSearch}
                        style={{
                            width: 38, height: 38, borderRadius: 'var(--radius-sm)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'transparent', border: 'none',
                            color: 'var(--text-secondary)',
                            transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-glass)'; e.currentTarget.style.color = 'var(--text-primary)' }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)' }}
                    >
                        <Search size={18} />
                    </button>

                    {/* Wishlist */}
                    {isLoggedIn && (
                        <Link to="/wishlist" style={{
                            width: 38, height: 38, borderRadius: 'var(--radius-sm)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: 'var(--text-secondary)', transition: 'all 0.15s',
                        }}
                            onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-glass)'; e.currentTarget.style.color = 'var(--accent)' }}
                            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)' }}
                        >
                            <Heart size={18} />
                        </Link>
                    )}

                    {/* Cart */}
                    <button
                        onClick={toggleCart}
                        style={{
                            width: 38, height: 38, borderRadius: 'var(--radius-sm)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'transparent', border: 'none',
                            color: 'var(--text-secondary)', position: 'relative',
                            transition: 'all 0.15s',
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = 'var(--bg-glass)'; e.currentTarget.style.color = 'var(--text-primary)' }}
                        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-secondary)' }}
                    >
                        <ShoppingBag size={18} />
                        {cartCount > 0 && (
                            <span style={{
                                position: 'absolute', top: 4, right: 4,
                                width: 16, height: 16,
                                background: 'var(--accent)', color: 'var(--text-inverse)',
                                borderRadius: '50%', fontSize: 10, fontWeight: 600,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}>
                                {cartCount > 9 ? '9+' : cartCount}
                            </span>
                        )}
                    </button>

                    {/* User Menu */}
                    {isLoggedIn ? (
                        <div style={{ position: 'relative' }}>
                            <button
                                onClick={() => setUserMenuOpen(v => !v)}
                                style={{
                                    display: 'flex', alignItems: 'center', gap: '0.5rem',
                                    padding: '0.375rem 0.75rem 0.375rem 0.375rem',
                                    borderRadius: 'var(--radius-sm)',
                                    background: 'var(--bg-raised)', border: '1px solid var(--border)',
                                    color: 'var(--text-primary)', fontSize: '0.875rem',
                                    transition: 'all 0.15s',
                                }}
                            >
                                <div style={{
                                    width: 26, height: 26, borderRadius: '50%',
                                    background: 'var(--accent)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: 11, fontWeight: 600, color: 'var(--text-inverse)',
                                }}>
                                    {user?.name?.[0]?.toUpperCase() ?? 'U'}
                                </div>
                                <span className="hidden-mobile">{user?.name?.split(' ')[0]}</span>
                            </button>

                            {userMenuOpen && (
                                <div style={{
                                    position: 'absolute', top: 'calc(100% + 8px)', right: 0,
                                    background: 'var(--bg-surface)', border: '1px solid var(--border)',
                                    borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
                                    minWidth: 180, overflow: 'hidden', zIndex: 200,
                                    animation: 'fadeUp 0.2s var(--ease-out)',
                                }}>
                                    {[
                                        { to: '/profile', label: 'My Profile' },
                                        { to: '/orders', label: 'My Orders' },
                                        { to: '/wishlist', label: 'Wishlist' },
                                        { to: '/loyalty', label: '⭐ Loyalty Points' },
                                    ].map(item => (
                                        <Link
                                            key={item.to} to={item.to}
                                            onClick={() => setUserMenuOpen(false)}
                                            style={{
                                                display: 'block', padding: '0.625rem 1rem',
                                                fontSize: '0.875rem', color: 'var(--text-secondary)',
                                                transition: 'all 0.1s',
                                            }}
                                            onMouseEnter={e => { e.target.style.background = 'var(--bg-hover)'; e.target.style.color = 'var(--text-primary)' }}
                                            onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = 'var(--text-secondary)' }}
                                        >
                                            {item.label}
                                        </Link>
                                    ))}
                                    <div style={{ height: 1, background: 'var(--border)', margin: '0.25rem 0' }} />
                                    <button
                                        onClick={handleLogout}
                                        style={{
                                            display: 'block', width: '100%', textAlign: 'left',
                                            padding: '0.625rem 1rem', fontSize: '0.875rem',
                                            color: 'var(--error)', background: 'transparent', border: 'none',
                                            transition: 'all 0.1s',
                                        }}
                                        onMouseEnter={e => e.target.style.background = 'var(--bg-hover)'}
                                        onMouseLeave={e => e.target.style.background = 'transparent'}
                                    >
                                        Sign Out
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <Link to="/login">
                            <button style={{
                                padding: '0.5rem 1rem', borderRadius: 'var(--radius-sm)',
                                background: 'var(--accent)', color: 'var(--text-inverse)',
                                border: 'none', fontSize: '0.875rem', fontWeight: 500,
                                transition: 'all 0.15s',
                            }}
                                onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-dim)'}
                                onMouseLeave={e => e.currentTarget.style.background = 'var(--accent)'}
                            >
                                Sign In
                            </button>
                        </Link>
                    )}
                </div>
            </nav>

            <style>{`
        @media (max-width: 768px) { .hidden-mobile { display: none !important; } }
      `}</style>
        </header>
    )
}