// src/components/product/ProductCard.jsx

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Heart, ShoppingBag, Star, Zap } from 'lucide-react'
import { useCartStore, useAuthStore } from '../../store'
import { cartAPI, usersAPI, behaviorAPI } from '../../services/api'
import { Badge, Price, Stars } from '../ui'
import toast from 'react-hot-toast'

export default function ProductCard({ product, reason, showReason = false }) {
    const [wishlist, setWishlist] = useState(false)
    const [addingCart, setAddCart] = useState(false)
    const { isLoggedIn } = useAuthStore()
    const { setCart } = useCartStore()

    if (!product) return null

    const disc = product.mrp > product.selling_price
        ? Math.round((product.mrp - product.selling_price) / product.mrp * 100)
        : 0

    async function handleAddToCart(e) {
        e.preventDefault()
        if (!isLoggedIn) { toast.error('Please sign in to add to cart'); return }
        setAddCart(true)
        try {
            const { data } = await cartAPI.add({ product_id: product.id, quantity: 1 })
            setCart(data.cart)
            toast.success('Added to cart!')
            behaviorAPI.track({ event_type: 'add_to_cart', product_id: product.id, session_id: 'web', category: product.category })
        } catch (e) {
            toast.error(e.response?.data?.detail ?? 'Failed to add')
        } finally {
            setAddCart(false)
        }
    }

    async function handleWishlist(e) {
        e.preventDefault()
        if (!isLoggedIn) { toast.error('Please sign in'); return }
        try {
            if (wishlist) {
                await usersAPI.removeWishlist(product.id)
                setWishlist(false)
                toast.success('Removed from wishlist')
            } else {
                await usersAPI.addWishlist(product.id)
                setWishlist(true)
                toast.success('Saved to wishlist!')
            }
        } catch { }
    }

    function handleView() {
        behaviorAPI.track({ event_type: 'view', product_id: product.id, session_id: 'web', category: product.category })
    }

    return (
        <Link to={`/products/${product.id}`} onClick={handleView} style={{ display: 'block' }}>
            <div
                style={{
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-md)',
                    overflow: 'hidden',
                    transition: 'all 0.3s var(--ease-out)',
                    position: 'relative',
                }}
                onMouseEnter={e => {
                    e.currentTarget.style.borderColor = 'var(--border-accent)'
                    e.currentTarget.style.transform = 'translateY(-4px)'
                    e.currentTarget.style.boxShadow = 'var(--shadow-accent)'
                }}
                onMouseLeave={e => {
                    e.currentTarget.style.borderColor = 'var(--border)'
                    e.currentTarget.style.transform = 'translateY(0)'
                    e.currentTarget.style.boxShadow = 'none'
                }}
            >
                {/* Image */}
                <div style={{ position: 'relative', aspectRatio: '4/3', background: 'var(--bg-raised)', overflow: 'hidden' }}>
                    {product.thumbnail_url ? (
                        <img
                            src={product.thumbnail_url}
                            alt={product.name}
                            style={{ width: '100%', height: '100%', objectFit: 'cover', transition: 'transform 0.4s var(--ease-out)' }}
                            onMouseEnter={e => e.target.style.transform = 'scale(1.04)'}
                            onMouseLeave={e => e.target.style.transform = 'scale(1)'}
                            onError={e => { e.target.style.display = 'none' }}
                        />
                    ) : (
                        <div style={{
                            width: '100%', height: '100%',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '2.5rem',
                        }}>
                            🛍️
                        </div>
                    )}

                    {/* Badges */}
                    <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {disc >= 20 && <Badge variant="hot">{disc}% OFF</Badge>}
                        {product.badges?.slice(0, 1).map(b => (
                            <Badge key={b} variant="accent">{b}</Badge>
                        ))}
                    </div>

                    {/* Wishlist button */}
                    <button
                        onClick={handleWishlist}
                        style={{
                            position: 'absolute', top: 10, right: 10,
                            width: 32, height: 32, borderRadius: '50%',
                            background: 'rgba(15,15,15,0.7)', backdropFilter: 'blur(8px)',
                            border: '1px solid var(--border)', display: 'flex',
                            alignItems: 'center', justifyContent: 'center',
                            transition: 'all 0.2s', cursor: 'pointer',
                            color: wishlist ? 'var(--error)' : 'var(--text-muted)',
                        }}
                        onMouseEnter={e => e.currentTarget.style.color = 'var(--error)'}
                        onMouseLeave={e => e.currentTarget.style.color = wishlist ? 'var(--error)' : 'var(--text-muted)'}
                    >
                        <Heart size={14} fill={wishlist ? 'currentColor' : 'none'} />
                    </button>

                    {!product.in_stock && (
                        <div style={{
                            position: 'absolute', inset: 0,
                            background: 'rgba(15,15,15,0.7)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                        }}>
                            <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', fontWeight: 500 }}>Out of Stock</span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div style={{ padding: '1rem' }}>
                    <p style={{ fontSize: '0.7rem', color: 'var(--accent)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>
                        {product.brand_name}
                    </p>
                    <h3 style={{
                        fontSize: '0.9rem', fontWeight: 500, color: 'var(--text-primary)',
                        display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                        overflow: 'hidden', lineHeight: 1.4, marginBottom: 8,
                    }}>
                        {product.name}
                    </h3>

                    {product.rating > 0 && (
                        <div style={{ marginBottom: 8, fontSize: 12, color: 'var(--accent)' }}>
                            <Stars rating={product.rating} count={product.rating_count} size={12} />
                        </div>
                    )}

                    <Price selling={product.selling_price} mrp={product.mrp} size="md" />

                    {showReason && reason && (
                        <p style={{
                            marginTop: 8, fontSize: '0.7rem', color: 'var(--text-secondary)',
                            display: 'flex', alignItems: 'flex-start', gap: 4,
                        }}>
                            <Zap size={10} style={{ marginTop: 2, color: 'var(--accent)', flexShrink: 0 }} />
                            {reason}
                        </p>
                    )}

                    {/* Add to Cart */}
                    {product.in_stock && (
                        <button
                            onClick={handleAddToCart}
                            disabled={addingCart}
                            style={{
                                marginTop: 12, width: '100%',
                                padding: '0.5rem', borderRadius: 'var(--radius-sm)',
                                background: 'var(--bg-raised)', border: '1px solid var(--border)',
                                color: 'var(--text-primary)', fontSize: '0.8rem', fontWeight: 500,
                                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                                transition: 'all 0.2s', cursor: 'pointer',
                            }}
                            onMouseEnter={e => { e.currentTarget.style.background = 'var(--accent)'; e.currentTarget.style.color = 'var(--text-inverse)'; e.currentTarget.style.borderColor = 'var(--accent)' }}
                            onMouseLeave={e => { e.currentTarget.style.background = 'var(--bg-raised)'; e.currentTarget.style.color = 'var(--text-primary)'; e.currentTarget.style.borderColor = 'var(--border)' }}
                        >
                            <ShoppingBag size={13} />
                            {addingCart ? 'Adding...' : 'Add to Cart'}
                        </button>
                    )}
                </div>
            </div>
        </Link>
    )
}