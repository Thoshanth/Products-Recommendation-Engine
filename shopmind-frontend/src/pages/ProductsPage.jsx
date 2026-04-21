// src/pages/ProductsPage.jsx

import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, SlidersHorizontal, X } from 'lucide-react'
import { productsAPI } from '../services/api'
import ProductCard from '../components/product/ProductCard'
import { Skeleton, Button, Input, Spinner } from '../components/ui'

const CATEGORIES = [
    { id: '', label: 'All' },
    { id: 'electronics', label: 'Electronics' },
    { id: 'laptops_computers', label: 'Laptops' },
    { id: 'audio', label: 'Audio' },
    { id: 'gaming', label: 'Gaming' },
    { id: 'fashion_men', label: "Men's Fashion" },
    { id: 'fashion_women', label: "Women's Fashion" },
    { id: 'fashion_kids', label: "Kids' Fashion" },
    { id: 'home_appliances', label: 'Appliances' },
    { id: 'home_decor', label: 'Home & Decor' },
    { id: 'beauty_skincare', label: 'Beauty' },
    { id: 'sports_fitness', label: 'Sports' },
    { id: 'books', label: 'Books' },
    { id: 'health_wellness', label: 'Health' },
    { id: 'toys_games', label: 'Toys' },
]

const SORTS = [
    { id: 'relevance', label: 'Relevance' },
    { id: 'price_asc', label: 'Price: Low to High' },
    { id: 'price_desc', label: 'Price: High to Low' },
    { id: 'rating', label: 'Top Rated' },
    { id: 'newest', label: 'Newest' },
]

export default function ProductsPage() {
    const [searchParams, setSearchParams] = useSearchParams()
    const [query, setQuery] = useState(searchParams.get('q') ?? '')
    const [category, setCategory] = useState(searchParams.get('category') ?? '')
    const [sortBy, setSortBy] = useState('relevance')
    const [minPrice, setMinPrice] = useState('')
    const [maxPrice, setMaxPrice] = useState('')
    const [minRating, setMinRating] = useState('')
    const [inStock, setInStock] = useState(false)
    const [page, setPage] = useState(1)
    const [showFilters, setShowFilters] = useState(false)
    const [debouncedQ, setDebouncedQ] = useState(query)

    // Debounce search
    useEffect(() => {
        const t = setTimeout(() => setDebouncedQ(query), 400)
        return () => clearTimeout(t)
    }, [query])

    // Reset page on filter change
    useEffect(() => { setPage(1) }, [debouncedQ, category, sortBy, minPrice, maxPrice, inStock])

    const isSearchMode = debouncedQ.trim().length > 0

    const { data, isLoading, isFetching } = useQuery({
        queryKey: ['products', debouncedQ, category, sortBy, minPrice, maxPrice, inStock, page],
        queryFn: () => {
            if (isSearchMode) {
                return productsAPI.search({
                    q: debouncedQ, category: category || undefined,
                    sort_by: sortBy, page, per_page: 20,
                    min_price: minPrice || undefined, max_price: maxPrice || undefined,
                    min_rating: minRating || undefined,
                    in_stock_only: inStock,
                }).then(r => r.data)
            } else if (category) {
                return productsAPI.byCategory(category, { page, per_page: 20 }).then(r => ({ ...r.data, results: r.data.products }))
            } else {
                return productsAPI.list({ page, per_page: 20, in_stock_only: inStock }).then(r => ({ ...r.data, results: r.data.products }))
            }
        },
        keepPreviousData: true,
        staleTime: 60 * 1000,
    })

    const products = data?.results ?? data?.products ?? []
    const total = data?.total ?? 0
    const totalPages = data?.total_pages ?? 1

    return (
        <div style={{ maxWidth: 'var(--content-max)', margin: '0 auto', padding: '2rem 1.5rem' }}>
            {/* Header */}
            <div style={{ marginBottom: '2rem' }}>
                <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: 4 }}>
                    {category ? CATEGORIES.find(c => c.id === category)?.label ?? 'Products' : 'All Products'}
                </h1>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    {total > 0 ? `${total.toLocaleString()} products found` : ''}
                </p>
            </div>

            {/* Search bar */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: 240, position: 'relative' }}>
                    <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        type="text"
                        placeholder="Search products, brands, categories..."
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        style={{
                            width: '100%', paddingLeft: 40, paddingRight: query ? 36 : 12,
                            height: 42, background: 'var(--bg-raised)', border: '1px solid var(--border)',
                            borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.875rem',
                            transition: 'border-color 0.15s', outline: 'none',
                        }}
                        onFocus={e => e.target.style.borderColor = 'var(--accent)'}
                        onBlur={e => e.target.style.borderColor = 'var(--border)'}
                    />
                    {query && (
                        <button onClick={() => setQuery('')}
                            style={{
                                position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                                background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
                            }}>
                            <X size={14} />
                        </button>
                    )}
                </div>
                <Button variant="secondary" size="sm" onClick={() => setShowFilters(v => !v)}>
                    <SlidersHorizontal size={14} /> Filters
                </Button>
                <select
                    value={sortBy} onChange={e => setSortBy(e.target.value)}
                    style={{
                        height: 42, padding: '0 12px', background: 'var(--bg-raised)',
                        border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                        color: 'var(--text-primary)', fontSize: '0.875rem', cursor: 'pointer',
                    }}
                >
                    {SORTS.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                </select>
            </div>

            {/* Filters panel */}
            {showFilters && (
                <div style={{
                    background: 'var(--bg-surface)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.5rem',
                    display: 'flex', gap: '1.5rem', flexWrap: 'wrap', alignItems: 'flex-end',
                    animation: 'fadeUp 0.2s var(--ease-out)',
                }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Min Price (₹)</label>
                        <input type="number" placeholder="0" value={minPrice} onChange={e => setMinPrice(e.target.value)}
                            style={{ width: 100, padding: '6px 10px', background: 'var(--bg-raised)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.875rem' }} />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Max Price (₹)</label>
                        <input type="number" placeholder="100000" value={maxPrice} onChange={e => setMaxPrice(e.target.value)}
                            style={{ width: 100, padding: '6px 10px', background: 'var(--bg-raised)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.875rem' }} />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 6 }}>Min Rating</label>
                        <select value={minRating} onChange={e => setMinRating(e.target.value)}
                            style={{ padding: '6px 10px', background: 'var(--bg-raised)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', color: 'var(--text-primary)', fontSize: '0.875rem' }}>
                            <option value="">Any</option>
                            {[4.5, 4, 3.5, 3].map(r => <option key={r} value={r}>{r}+ ★</option>)}
                        </select>
                    </div>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                        <input type="checkbox" checked={inStock} onChange={e => setInStock(e.target.checked)}
                            style={{ accentColor: 'var(--accent)', width: 16, height: 16 }} />
                        In Stock Only
                    </label>
                    <Button variant="ghost" size="sm" onClick={() => { setMinPrice(''); setMaxPrice(''); setMinRating(''); setInStock(false) }}>
                        Reset
                    </Button>
                </div>
            )}

            {/* Category tabs */}
            <div style={{ display: 'flex', gap: '0.5rem', overflowX: 'auto', paddingBottom: 8, marginBottom: '1.5rem' }}>
                {CATEGORIES.map(cat => (
                    <button key={cat.id} onClick={() => setCategory(cat.id)}
                        style={{
                            padding: '0.375rem 0.875rem', borderRadius: 'var(--radius-lg)', flexShrink: 0,
                            background: category === cat.id ? 'var(--accent)' : 'var(--bg-raised)',
                            color: category === cat.id ? 'var(--text-inverse)' : 'var(--text-secondary)',
                            border: `1px solid ${category === cat.id ? 'var(--accent)' : 'var(--border)'}`,
                            fontSize: '0.8rem', cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'var(--font-body)',
                        }}
                    >
                        {cat.label}
                    </button>
                ))}
            </div>

            {/* Products grid */}
            {isLoading ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}>
                    {Array.from({ length: 8 }).map((_, i) => (
                        <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
                            <Skeleton style={{ height: 180 }} />
                            <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: 8 }}>
                                <Skeleton style={{ height: 10, width: '40%' }} />
                                <Skeleton style={{ height: 14, width: '90%' }} />
                                <Skeleton style={{ height: 20, width: '50%' }} />
                            </div>
                        </div>
                    ))}
                </div>
            ) : products.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
                    <p style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔍</p>
                    <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', marginBottom: 8 }}>No products found</h3>
                    <p style={{ color: 'var(--text-secondary)' }}>Try different keywords or clear your filters.</p>
                </div>
            ) : (
                <>
                    {isFetching && !isLoading && (
                        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
                            <Spinner size={16} />
                        </div>
                    )}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' }}
                        className="stagger">
                        {products.map(p => (
                            <div key={p.id} className="fade-up">
                                <ProductCard product={p} />
                            </div>
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '2.5rem', flexWrap: 'wrap' }}>
                            <Button variant="secondary" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</Button>
                            {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
                                const pg = i + 1
                                return (
                                    <button key={pg} onClick={() => setPage(pg)}
                                        style={{
                                            width: 36, height: 36, borderRadius: 'var(--radius-sm)',
                                            background: page === pg ? 'var(--accent)' : 'var(--bg-raised)',
                                            color: page === pg ? 'var(--text-inverse)' : 'var(--text-secondary)',
                                            border: `1px solid ${page === pg ? 'var(--accent)' : 'var(--border)'}`,
                                            cursor: 'pointer', fontSize: '0.875rem', fontFamily: 'var(--font-body)',
                                        }}
                                    >
                                        {pg}
                                    </button>
                                )
                            })}
                            <Button variant="secondary" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next →</Button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}