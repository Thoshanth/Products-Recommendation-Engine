// src/pages/OrdersPage.jsx

import { useQuery } from '@tanstack/react-query'
import { Navigate, Link } from 'react-router-dom'
import { Package, ChevronRight, Clock, CheckCircle, Truck, XCircle } from 'lucide-react'
import { ordersAPI } from '../services/api'
import { useAuthStore } from '../store'
import { Skeleton, Empty, Badge, Button } from '../components/ui'

const STATUS_CONFIG = {
    pending: { color: 'var(--warning)', icon: Clock, label: 'Pending' },
    confirmed: { color: 'var(--accent)', icon: CheckCircle, label: 'Confirmed' },
    processing: { color: '#60a5fa', icon: Package, label: 'Processing' },
    shipped: { color: '#a78bfa', icon: Truck, label: 'Shipped' },
    out_for_delivery: { color: 'var(--accent)', icon: Truck, label: 'Out for Delivery' },
    delivered: { color: 'var(--success)', icon: CheckCircle, label: 'Delivered' },
    cancelled: { color: 'var(--error)', icon: XCircle, label: 'Cancelled' },
    returned: { color: 'var(--error)', icon: XCircle, label: 'Returned' },
    refunded: { color: 'var(--text-muted)', icon: CheckCircle, label: 'Refunded' },
}

export default function OrdersPage() {
    const { isLoggedIn } = useAuthStore()
    if (!isLoggedIn) return <Navigate to="/login" replace />

    const { data, isLoading } = useQuery({
        queryKey: ['orders'],
        queryFn: () => ordersAPI.list({ per_page: 20 }).then(r => r.data),
        staleTime: 60 * 1000,
    })

    const orders = data?.orders ?? []

    return (
        <div style={{ maxWidth: 800, margin: '0 auto', padding: '2.5rem 1.5rem' }}>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', marginBottom: '2rem' }}>My Orders</h1>

            {isLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {Array.from({ length: 3 }).map((_, i) => (
                        <div key={i} style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                                <Skeleton style={{ height: 14, width: 140 }} />
                                <Skeleton style={{ height: 20, width: 80, borderRadius: 99 }} />
                            </div>
                            <Skeleton style={{ height: 12, width: 200 }} />
                        </div>
                    ))}
                </div>
            ) : orders.length === 0 ? (
                <Empty icon="📦" title="No orders yet" message="Your order history will appear here."
                    action={<Link to="/products"><Button>Start Shopping</Button></Link>} />
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }} className="stagger">
                    {orders.map(order => {
                        const cfg = STATUS_CONFIG[order.status] ?? STATUS_CONFIG.pending
                        const Icon = cfg.icon
                        return (
                            <div key={order.id} className="fade-up" style={{
                                background: 'var(--bg-surface)', border: '1px solid var(--border)',
                                borderRadius: 'var(--radius-md)', padding: '1.25rem',
                                transition: 'all 0.2s',
                            }}
                                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border-accent)' }}
                                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border)' }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                                    <div>
                                        <p style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: 2 }}>{order.order_number}</p>
                                        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            {new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                                        </p>
                                    </div>
                                    <span style={{
                                        display: 'flex', alignItems: 'center', gap: 5,
                                        padding: '4px 10px', borderRadius: 99, fontSize: '0.75rem', fontWeight: 500,
                                        background: `${cfg.color}15`, color: cfg.color, border: `1px solid ${cfg.color}30`,
                                    }}>
                                        <Icon size={12} />
                                        {cfg.label}
                                    </span>
                                </div>

                                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                                    {order.items.slice(0, 3).map(item => (
                                        <div key={item.product_id} style={{
                                            display: 'flex', alignItems: 'center', gap: 6,
                                            background: 'var(--bg-raised)', borderRadius: 'var(--radius-sm)', padding: '4px 8px',
                                        }}>
                                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{item.product_name}</span>
                                            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>×{item.quantity}</span>
                                        </div>
                                    ))}
                                    {order.items.length > 3 && (
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', padding: '4px 0' }}>
                                            +{order.items.length - 3} more
                                        </span>
                                    )}
                                </div>

                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span style={{ fontWeight: 700, color: 'var(--accent)' }}>
                                        ₹{order.total_amount.toLocaleString('en-IN')}
                                    </span>
                                    {order.estimated_delivery && order.status !== 'delivered' && order.status !== 'cancelled' && (
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                            Est. delivery: {new Date(order.estimated_delivery).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                                        </span>
                                    )}
                                </div>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}