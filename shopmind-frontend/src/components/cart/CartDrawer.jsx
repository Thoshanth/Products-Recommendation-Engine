// src/components/cart/CartDrawer.jsx

import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X, ShoppingBag, Plus, Minus, Trash2, ArrowRight, Tag } from 'lucide-react'
import { useCartStore, useAuthStore } from '../../store'
import { cartAPI } from '../../services/api'
import { Button, Spinner, Price } from '../ui'
import toast from 'react-hot-toast'

export default function CartDrawer() {
    const { cart, isOpen, closeCart, setCart, isLoading, setLoading } = useCartStore()
    const { isLoggedIn } = useAuthStore()

    useEffect(() => {
        if (isOpen && isLoggedIn) fetchCart()
    }, [isOpen, isLoggedIn])

    async function fetchCart() {
        setLoading(true)
        try {
            const { data } = await cartAPI.get()
            setCart(data)
        } catch { }
        setLoading(false)
    }

    async function handleQty(productId, delta, current) {
        const newQty = current + delta
        try {
            if (newQty < 1) {
                const { data } = await cartAPI.remove(productId)
                setCart(data.cart)
            } else {
                const { data } = await cartAPI.updateQty(productId, { quantity: newQty })
                setCart(data.cart)
            }
        } catch (e) {
            toast.error(e.response?.data?.detail ?? 'Failed to update')
        }
    }

    async function handleRemove(productId) {
        try {
            const { data } = await cartAPI.remove(productId)
            setCart(data.cart)
            toast.success('Removed from cart')
        } catch { }
    }

    const items = cart?.items ?? []
    const totalAmount = cart?.total_amount ?? 0
    const totalMrp = cart?.total_mrp ?? 0
    const savings = totalMrp - (cart?.total_discount ?? 0 ? totalMrp - cart.total_amount + (cart?.delivery_charge ?? 0) : 0)

    return (
        <>
            {/* Backdrop */}
            {isOpen && (
                <div
                    onClick={closeCart}
                    style={{
                        position: 'fixed', inset: 0, zIndex: 150,
                        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
                        animation: 'fadeIn 0.2s ease',
                    }}
                />
            )}

            {/* Drawer */}
            <div style={{
                position: 'fixed', top: 0, right: 0, bottom: 0,
                width: 'min(420px, 100vw)', zIndex: 200,
                background: 'var(--bg-surface)',
                borderLeft: '1px solid var(--border)',
                display: 'flex', flexDirection: 'column',
                transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
                transition: 'transform 0.35s var(--ease-out)',
                boxShadow: isOpen ? '-20px 0 60px rgba(0,0,0,0.5)' : 'none',
            }}>
                {/* Header */}
                <div style={{
                    padding: '1.25rem 1.5rem',
                    borderBottom: '1px solid var(--border)',
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <ShoppingBag size={20} color="var(--accent)" />
                        <span style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem' }}>
                            Your Cart
                        </span>
                        {items.length > 0 && (
                            <span style={{
                                background: 'var(--accent)', color: 'var(--text-inverse)',
                                borderRadius: 99, padding: '0 8px', fontSize: 12, fontWeight: 600,
                            }}>
                                {cart?.item_count}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={closeCart}
                        style={{
                            width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            borderRadius: 'var(--radius-sm)', border: 'none',
                            background: 'var(--bg-raised)', color: 'var(--text-secondary)', cursor: 'pointer',
                        }}
                    >
                        <X size={16} />
                    </button>
                </div>

                {/* Body */}
                <div style={{ flex: 1, overflow: 'auto', padding: '1rem 1.5rem' }}>
                    {!isLoggedIn ? (
                        <div style={{ textAlign: 'center', paddingTop: '3rem' }}>
                            <ShoppingBag size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
                            <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Sign in to view your cart</p>
                            <Link to="/login" onClick={closeCart}>
                                <Button>Sign In</Button>
                            </Link>
                        </div>
                    ) : isLoading ? (
                        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '4rem' }}>
                            <Spinner />
                        </div>
                    ) : items.length === 0 ? (
                        <div style={{ textAlign: 'center', paddingTop: '3rem' }}>
                            <ShoppingBag size={48} color="var(--text-muted)" style={{ margin: '0 auto 1rem' }} />
                            <p style={{ fontFamily: 'var(--font-display)', fontSize: '1.25rem', marginBottom: 8 }}>Your cart is empty</p>
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
                                Discover products curated just for you
                            </p>
                            <Link to="/products" onClick={closeCart}>
                                <Button variant="outline">Browse Products</Button>
                            </Link>
                        </div>
                    ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {items.map(item => (
                                <div key={`${item.product_id}-${item.selected_size}-${item.selected_color}`}
                                    style={{
                                        display: 'flex', gap: '0.875rem',
                                        padding: '0.875rem', borderRadius: 'var(--radius-md)',
                                        background: 'var(--bg-raised)', border: '1px solid var(--border)',
                                    }}
                                >
                                    {/* Thumbnail */}
                                    <div style={{
                                        width: 64, height: 64, flexShrink: 0,
                                        borderRadius: 'var(--radius-sm)', overflow: 'hidden',
                                        background: 'var(--bg-hover)',
                                    }}>
                                        {item.thumbnail_url ? (
                                            <img src={item.thumbnail_url} alt={item.product_name}
                                                style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                        ) : (
                                            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5rem' }}>🛍️</div>
                                        )}
                                    </div>

                                    {/* Info */}
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <p style={{
                                            fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)', marginBottom: 4,
                                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
                                        }}>
                                            {item.product_name}
                                        </p>
                                        {(item.selected_size || item.selected_color) && (
                                            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                                                {[item.selected_size, item.selected_color].filter(Boolean).join(' · ')}
                                            </p>
                                        )}
                                        <Price selling={item.selling_price} mrp={item.mrp} size="sm" />

                                        {/* Qty controls */}
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 8 }}>
                                            <div style={{
                                                display: 'flex', alignItems: 'center', gap: 0,
                                                border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', overflow: 'hidden'
                                            }}>
                                                <button
                                                    onClick={() => handleQty(item.product_id, -1, item.quantity)}
                                                    style={{
                                                        width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer',
                                                        transition: 'background 0.15s'
                                                    }}
                                                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                                >
                                                    <Minus size={12} />
                                                </button>
                                                <span style={{ width: 28, textAlign: 'center', fontSize: '0.8rem', fontWeight: 500 }}>
                                                    {item.quantity}
                                                </span>
                                                <button
                                                    onClick={() => handleQty(item.product_id, 1, item.quantity)}
                                                    style={{
                                                        width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer',
                                                        transition: 'background 0.15s'
                                                    }}
                                                    onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-hover)'}
                                                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                                >
                                                    <Plus size={12} />
                                                </button>
                                            </div>
                                            <button onClick={() => handleRemove(item.product_id)}
                                                style={{
                                                    background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer',
                                                    padding: 4, borderRadius: 4, transition: 'color 0.15s'
                                                }}
                                                onMouseEnter={e => e.currentTarget.style.color = 'var(--error)'}
                                                onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                {items.length > 0 && (
                    <div style={{ padding: '1.25rem 1.5rem', borderTop: '1px solid var(--border)' }}>
                        {cart?.coupon_code && (
                            <div style={{
                                display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12,
                                padding: '0.5rem 0.75rem', borderRadius: 'var(--radius-sm)',
                                background: 'var(--accent-subtle)', border: '1px solid var(--border-accent)',
                                fontSize: '0.8rem', color: 'var(--accent)',
                            }}>
                                <Tag size={12} />
                                <span>{cart.coupon_code} applied — ₹{cart.coupon_discount.toLocaleString('en-IN')} off</span>
                            </div>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16 }}>
                            {cart?.total_discount > 0 && (
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                                    <span style={{ color: 'var(--text-secondary)' }}>You save</span>
                                    <span style={{ color: 'var(--success)', fontWeight: 500 }}>
                                        -₹{cart.total_discount.toLocaleString('en-IN')}
                                    </span>
                                </div>
                            )}
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                                <span style={{ color: 'var(--text-secondary)' }}>Delivery</span>
                                <span style={{ color: cart?.delivery_charge === 0 ? 'var(--success)' : 'var(--text-primary)' }}>
                                    {cart?.delivery_charge === 0 ? 'FREE' : `₹${cart.delivery_charge}`}
                                </span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid var(--border)' }}>
                                <span style={{ fontWeight: 600 }}>Total</span>
                                <span style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--accent)' }}>
                                    ₹{totalAmount.toLocaleString('en-IN')}
                                </span>
                            </div>
                        </div>

                        <Link to="/checkout" onClick={closeCart} style={{ display: 'block' }}>
                            <Button style={{ width: '100%', justifyContent: 'center' }} size="lg">
                                Checkout <ArrowRight size={16} />
                            </Button>
                        </Link>
                    </div>
                )}
            </div>
        </>
    )
}