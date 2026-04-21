// src/pages/RecommendationsPage.jsx

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, TrendingUp, Star, Package, RefreshCw, Zap } from 'lucide-react'
import { recoAPI } from '../services/api'
import { useAuthStore } from '../store'
import ProductCard from '../components/product/ProductCard'
import { Button, Skeleton, SectionHeader, Badge, Spinner, Empty } from '../components/ui'
import { Link, Navigate } from 'react-router-dom'

function RecoGrid({ items = [], loading, showReason = true }) {
    if (loading) return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
            {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                    <Skeleton style={{ height: 180 }} />
                    <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
                        <Skeleton style={{ height: 10, width: '40%' }} />
                        <Skeleton style={{ height: 14, width: '85%' }} />
                        <Skeleton style={{ height: 14, width: '65%' }} />
                        <Skeleton style={{ height: 20, width: '45%' }} />
                    </div>
                </div>
            ))}
        </div>
    )
    if (!items.length) return (
        <Empty icon="🤖" title="No recommendations yet" message="Browse and interact with products to train your AI engine." />
    )
    return (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }} className="stagger">
            {items.map((item, i) => (
                <div key={item.product?.id ?? i} className="fade-up">
                    <ProductCard product={item.product} reason={item.reason} showReason={showReason} />
                </div>
            ))}
        </div>
    )
}

const TABS = [
    { id: 'personalized', label: 'For You', icon: Sparkles },
    { id: 'trending', label: 'Trending', icon: TrendingUp },
    { id: 'popular', label: 'Popular', icon: Star },
    { id: 'new', label: 'New Arrivals', icon: Package },
]

export default function RecommendationsPage() {
    const { isLoggedIn } = useAuthStore()
    const [activeTab, setActiveTab] = useState('personalized')
    const [forceRefresh, setForceRefresh] = useState(false)
    const [useAI, setUseAI] = useState(true)

    if (!isLoggedIn) return <Navigate to="/login" replace />

    const personalizedQ = useQuery({
        queryKey: ['reco-personalized-full', forceRefresh, useAI],
        queryFn: () => recoAPI.personalized({ limit: 20, use_ai: useAI, force_refresh: forceRefresh }).then(r => r.data),
        staleTime: 30 * 60 * 1000,
        enabled: activeTab === 'personalized',
    })

    const trendingQ = useQuery({
        queryKey: ['reco-trending-full'],
        queryFn: () => recoAPI.trending('daily').then(r => r.data),
        staleTime: 60 * 1000,
        enabled: activeTab === 'trending',
    })

    const popularQ = useQuery({
        queryKey: ['reco-popular-full'],
        queryFn: () => recoAPI.popular().then(r => r.data),
        staleTime: 5 * 60 * 1000,
        enabled: activeTab === 'popular',
    })

    const newQ = useQuery({
        queryKey: ['reco-new-full'],
        queryFn: () => recoAPI.newArrivals().then(r => r.data),
        staleTime: 5 * 60 * 1000,
        enabled: activeTab === 'new',
    })

    const current = {
        personalized: personalizedQ,
        trending: trendingQ,
        popular: popularQ,
        new: newQ,
    }[activeTab]

    const products = current?.data?.products ?? []
    const strategy = current?.data?.strategy ?? ''
    const fromCache = current?.data?.from_cache

    return (
        <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto', padding: '2.5rem 1.5rem' }}>
            {/* Header */}
            <div style={{ marginBottom: '2rem' }} className="fade-up">
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                        <p style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.15em', color: 'var(--accent)', marginBottom: 6 }}>
                            Powered by Nemotron AI
                        </p>
                        <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', marginBottom: 6 }}>
                            Your Recommendations
                        </h1>
                        {strategy && (
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                                <Zap size={12} color="var(--accent)" />
                                Strategy: {strategy}
                                {fromCache && <Badge variant="default" style={{ marginLeft: 4 }}>Cached</Badge>}
                            </p>
                        )}
                    </div>

                    {activeTab === 'personalized' && (
                        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
                            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                <input type="checkbox" checked={useAI} onChange={e => setUseAI(e.target.checked)}
                                    style={{ accentColor: 'var(--accent)', width: 16, height: 16 }} />
                                Use Nemotron AI
                            </label>
                            <Button variant="secondary" size="sm"
                                onClick={() => { setForceRefresh(v => !v); current?.refetch() }}
                                loading={current?.isFetching}
                            >
                                <RefreshCw size={14} /> Refresh
                            </Button>
                        </div>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '2rem', borderBottom: '1px solid var(--border)', paddingBottom: '0.25rem' }}>
                {TABS.map(tab => {
                    const Icon = tab.icon
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.5rem',
                                padding: '0.625rem 1rem', borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0',
                                background: 'transparent', border: 'none',
                                color: activeTab === tab.id ? 'var(--accent)' : 'var(--text-secondary)',
                                fontSize: '0.875rem', cursor: 'pointer', fontFamily: 'var(--font-body)',
                                borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                                transition: 'all 0.15s', marginBottom: -1,
                            }}
                        >
                            <Icon size={15} />
                            {tab.label}
                        </button>
                    )
                })}
            </div>

            {/* Products */}
            <RecoGrid
                items={products}
                loading={current?.isLoading}
                showReason={activeTab === 'personalized'}
            />
        </div>
    )
}