// src/pages/HomePage.jsx

import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, Sparkles, TrendingUp, Star, Package } from 'lucide-react'
import { productsAPI, recoAPI } from '../services/api'
import { useAuthStore, useCartStore } from '../store'
import { cartAPI } from '../services/api'
import ProductCard from '../components/product/ProductCard'
import { Skeleton, SectionHeader, Button, Badge, Spinner } from '../components/ui'

// ── Skeleton grid ─────────────────────────────────────────────────────────────
function ProductGridSkeleton({ count = 4 }) {
    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                    <Skeleton style={{ height: 180 }} />
                    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <Skeleton style={{ height: 10, width: '40%' }} />
                        <Skeleton style={{ height: 14, width: '90%' }} />
                        <Skeleton style={{ height: 14, width: '70%' }} />
                        <Skeleton style={{ height: 20, width: '50%' }} />
                    </div>
                </div>
            ))}
        </div>
    )
}

// ── Category pill ─────────────────────────────────────────────────────────────
const CATEGORIES = [
    { id: 'electronics', label: 'Electronics', emoji: '📱' },
    { id: 'fashion_men', label: "Men's Fashion", emoji: '👔' },
    { id: 'fashion_women', label: "Women's Fashion", emoji: '👗' },
    { id: 'home_appliances', label: 'Appliances', emoji: '🏠' },
    { id: 'books', label: 'Books', emoji: '📚' },
    { id: 'sports_fitness', label: 'Sports', emoji: '🏃' },
    { id: 'beauty_skincare', label: 'Beauty', emoji: '✨' },
    { id: 'gaming', label: 'Gaming', emoji: '🎮' },
]

export default function HomePage() {
    const { isLoggedIn } = useAuthStore()
    const { setCart } = useCartStore()

    // Fetch cart on load
    useEffect(() => {
        if (isLoggedIn) {
            cartAPI.get().then(({ data }) => setCart(data)).catch(() => { })
        }
    }, [isLoggedIn])

    const { data: featured, isLoading: featuredLoading } = useQuery({
        queryKey: ['featured'],
        queryFn: () => productsAPI.featured().then(r => r.data.products),
        staleTime: 5 * 60 * 1000,
    })

    const { data: trending, isLoading: trendingLoading } = useQuery({
        queryKey: ['trending'],
        queryFn: () => recoAPI.trending('daily').then(r => r.data.products),
        staleTime: 60 * 1000,
    })

    const { data: personalized, isLoading: recoLoading } = useQuery({
        queryKey: ['reco-personalized'],
        queryFn: () => recoAPI.personalized({ limit: 8, use_ai: true }).then(r => r.data),
        enabled: isLoggedIn,
        staleTime: 30 * 60 * 1000,
    })

    const { data: popular, isLoading: popularLoading } = useQuery({
        queryKey: ['popular'],
        queryFn: () => recoAPI.popular().then(r => r.data.products),
        staleTime: 5 * 60 * 1000,
    })

    return (
        <div>
            {/* ── Hero ──────────────────────────────────────────────────────────── */}
            <section style={{
                padding: '5rem 1.5rem 4rem',
                maxWidth: 'var(--content-max)', margin: '0 auto',
                display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4rem',
                alignItems: 'center',
            }}>
                <div className="fade-up">
                    <Badge variant="accent" className="mb-6" style={{ marginBottom: '1.5rem' }}>
                        <Sparkles size={10} style={{ marginRight: 4 }} />
                        AI-Powered Recommendations
                    </Badge>
                    <h1 style={{
                        fontFamily: 'var(--font-display)',
                        fontSize: 'clamp(2.5rem, 5vw, 4rem)',
                        lineHeight: 1.1, marginBottom: '1.25rem',
                        letterSpacing: '-0.02em',
                    }}>
                        Shop smarter,<br />
                        <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>not harder</span>
                    </h1>
                    <p style={{
                        fontSize: '1.1rem', color: 'var(--text-secondary)',
                        maxWidth: 420, lineHeight: 1.7, marginBottom: '2rem',
                    }}>
                        Nemotron AI learns your taste and surfaces exactly what you'll love —
                        before you even know you want it.
                    </p>
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                        <Link to={isLoggedIn ? '/recommendations' : '/register'}>
                            <Button size="lg">
                                {isLoggedIn ? 'My Recommendations' : 'Get Started'}
                                <ArrowRight size={16} />
                            </Button>
                        </Link>
                        <Link to="/products">
                            <Button variant="secondary" size="lg">Browse Catalogue</Button>
                        </Link>
                    </div>

                    {/* Stats */}
                    <div style={{ display: 'flex', gap: '2rem', marginTop: '2.5rem' }}>
                        {[
                            { label: 'Products', value: '50+' },
                            { label: 'Categories', value: '20' },
                            { label: 'AI Engine', value: 'Nemotron' },
                        ].map(stat => (
                            <div key={stat.label}>
                                <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', color: 'var(--accent)' }}>{stat.value}</p>
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{stat.label}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Hero Visual */}
                <div style={{ position: 'relative' }} className="fade-up hidden-mobile">
                    <div style={{
                        width: '100%', aspectRatio: '1', borderRadius: 'var(--radius-xl)',
                        background: 'linear-gradient(135deg, var(--bg-surface) 0%, var(--bg-raised) 100%)',
                        border: '1px solid var(--border)', overflow: 'hidden', position: 'relative',
                    }}>
                        {/* Decorative grid */}
                        <div style={{
                            position: 'absolute', inset: 0,
                            backgroundImage: 'radial-gradient(circle at 1px 1px, var(--border) 1px, transparent 0)',
                            backgroundSize: '32px 32px',
                        }} />
                        <div style={{
                            position: 'absolute', inset: 0,
                            background: 'radial-gradient(ellipse at 60% 40%, var(--accent-glow) 0%, transparent 60%)',
                        }} />
                        {/* AI Chip visual */}
                        <div style={{
                            position: 'absolute', top: '50%', left: '50%',
                            transform: 'translate(-50%, -50%)',
                            textAlign: 'center',
                        }}>
                            <div style={{
                                width: 96, height: 96, borderRadius: '50%',
                                background: 'var(--accent)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                margin: '0 auto 1rem',
                                boxShadow: '0 0 60px var(--accent-glow)',
                                animation: 'pulse 3s ease-in-out infinite',
                            }}>
                                <Sparkles size={40} color="var(--text-inverse)" />
                            </div>
                            <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginBottom: 4 }}>Nemotron AI</p>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Powered by OpenRouter</p>
                        </div>
                    </div>
                </div>

                <style>{`@media(max-width:768px){.hidden-mobile{display:none!important}}`}</style>
            </section>

            {/* ── Categories ────────────────────────────────────────────────────── */}
            <section style={{ padding: '0 1.5rem 4rem', maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                <div style={{ display: 'flex', gap: '0.75rem', overflowX: 'auto', paddingBottom: 8 }}>
                    {CATEGORIES.map((cat, i) => (
                        <Link key={cat.id} to={`/products?category=${cat.id}`}
                            style={{ animationDelay: `${i * 0.05}s` }}
                            className="fade-up"
                        >
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0,
                                padding: '0.625rem 1rem', borderRadius: 'var(--radius-lg)',
                                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                                fontSize: '0.8rem', color: 'var(--text-secondary)',
                                transition: 'all 0.2s', cursor: 'pointer', whiteSpace: 'nowrap',
                            }}
                                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-accent)'; e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.background = 'var(--accent-subtle)' }}
                                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.color = 'var(--text-secondary)'; e.currentTarget.style.background = 'var(--bg-surface)' }}
                            >
                                <span>{cat.emoji}</span>
                                {cat.label}
                            </div>
                        </Link>
                    ))}
                </div>
            </section>

            {/* ── AI Personalized (logged in) ───────────────────────────────────── */}
            {isLoggedIn && (
                <section style={{ padding: '0 1.5rem 5rem', maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                    <SectionHeader
                        label="Nemotron AI"
                        title="Picked for you"
                        subtitle={personalized?.strategy}
                        action={<Link to="/recommendations"><Button variant="ghost" size="sm">See all <ArrowRight size={14} /></Button></Link>}
                    />
                    {recoLoading ? <ProductGridSkeleton count={4} /> : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}
                            className="stagger">
                            {(personalized?.products ?? []).slice(0, 8).map(item => (
                                <div key={item.product.id} className="fade-up">
                                    <ProductCard product={item.product} reason={item.reason} showReason />
                                </div>
                            ))}
                        </div>
                    )}
                </section>
            )}

            {/* ── Trending ──────────────────────────────────────────────────────── */}
            <section style={{
                padding: '4rem 1.5rem',
                background: 'var(--bg-surface)',
                borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)',
            }}>
                <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                    <SectionHeader
                        label="Real-time"
                        title={<><TrendingUp size={24} style={{ display: 'inline', marginRight: 8 }} />Trending Today</>}
                        action={<Link to="/products?sort=trending"><Button variant="ghost" size="sm">See all <ArrowRight size={14} /></Button></Link>}
                    />
                    {trendingLoading ? <ProductGridSkeleton count={4} /> : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}
                            className="stagger">
                            {(trending ?? []).slice(0, 8).map((item, i) => (
                                <div key={item.product?.id ?? i} className="fade-up">
                                    <ProductCard product={item.product} />
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </section>

            {/* ── Featured ──────────────────────────────────────────────────────── */}
            <section style={{ padding: '4rem 1.5rem', maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                <SectionHeader
                    label="Curated"
                    title={<><Star size={22} style={{ display: 'inline', marginRight: 8, color: 'var(--accent)' }} />Featured Products</>}
                    action={<Link to="/products?featured=true"><Button variant="ghost" size="sm">View all <ArrowRight size={14} /></Button></Link>}
                />
                {featuredLoading ? <ProductGridSkeleton count={4} /> : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}
                        className="stagger">
                        {(featured ?? []).slice(0, 8).map(p => (
                            <div key={p.id} className="fade-up">
                                <ProductCard product={p} />
                            </div>
                        ))}
                    </div>
                )}
            </section>

            {/* ── Popular ───────────────────────────────────────────────────────── */}
            <section style={{
                padding: '4rem 1.5rem',
                background: 'var(--bg-surface)',
                borderTop: '1px solid var(--border)', borderBottom: '1px solid var(--border)',
            }}>
                <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto' }}>
                    <SectionHeader
                        label="Community Loved"
                        title="Most Popular"
                        action={<Link to="/products"><Button variant="ghost" size="sm">All products <ArrowRight size={14} /></Button></Link>}
                    />
                    {popularLoading ? <ProductGridSkeleton count={4} /> : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}
                            className="stagger">
                            {(popular ?? []).slice(0, 8).map((item, i) => (
                                <div key={item.product?.id ?? i} className="fade-up">
                                    <ProductCard product={item.product} />
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </section>

            {/* ── CTA ───────────────────────────────────────────────────────────── */}
            {!isLoggedIn && (
                <section style={{
                    padding: '6rem 1.5rem',
                    maxWidth: 'var(--content-max)', margin: '0 auto',
                    textAlign: 'center',
                }}>
                    <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'var(--accent)', marginBottom: '1rem' }}>
                        Get Started Free
                    </p>
                    <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(2rem, 4vw, 3rem)', marginBottom: '1rem' }}>
                        Your AI shopping assistant<br />awaits
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem', maxWidth: 400, margin: '0 auto 2rem' }}>
                        Create a free account and let Nemotron learn your style to deliver personalised recommendations.
                    </p>
                    <Link to="/register">
                        <Button size="lg">
                            Create Free Account <ArrowRight size={16} />
                        </Button>
                    </Link>
                </section>
            )}
        </div>
    )
}