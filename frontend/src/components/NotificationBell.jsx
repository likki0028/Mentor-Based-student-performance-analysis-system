
import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';

const VAPID_PUBLIC_KEY = 'BGAxpGedGqVVSXe-y-09QcqHbTnYIZ10XcHTwxxed14JmFvMZWlmk6naxxG0QNwY3_va6QUuvT7LiQRYeoQXEzs';

// Convert VAPID key to Uint8Array
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const raw = atob(base64);
    return Uint8Array.from([...raw].map(c => c.charCodeAt(0)));
}

const typeIcons = {
    attendance_alert: '🔴',
    assignment_new: '📘',
    marks_published: '⭐',
    risk_change: '⚠️',
    quiz_active: '🧩',
    deadline_reminder: '⏰',
    submission_update: '📥',
    system: '🔔',
};

const priorityColors = {
    low: '#6366f1',
    medium: '#f59e0b',
    high: '#ef4444',
};

function timeAgo(dateInput) {
    if (!dateInput) return 'Just now';
    
    let timestampMs;
    if (typeof dateInput === 'string') {
        let dStr = dateInput;
        // If string lacks timezone indicator (Z or +05:30), assume it's UTC from the backend
        if (!dStr.endsWith('Z') && !dStr.includes('+') && !dStr.match(/-\d{2}:\d{2}$/)) {
            dStr = dStr.replace(' ', 'T') + 'Z';
        }
        timestampMs = new Date(dStr).getTime();
    } else {
        timestampMs = dateInput;
    }
    
    if (isNaN(timestampMs)) return 'Just now';
    
    const diff = Date.now() - timestampMs;
    const mins = Math.floor(diff / 60000);
    
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
}

const NotificationBell = () => {
    const [open, setOpen] = useState(false);
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [pushEnabled, setPushEnabled] = useState(false);
    const dropdownRef = useRef(null);

    // Fetch unread count periodically
    useEffect(() => {
        fetchUnreadCount();
        const interval = setInterval(fetchUnreadCount, 60000); // Every 60s
        return () => clearInterval(interval);
    }, []);

    // Register service worker & push subscription on mount
    useEffect(() => {
        registerPush();
    }, []);

    // Close dropdown on outside click
    useEffect(() => {
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const fetchUnreadCount = async () => {
        try {
            const res = await api.get('/notifications/unread-count');
            setUnreadCount(res.data.count);
        } catch { /* ignore */ }
    };

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const res = await api.get('/notifications/?limit=30');
            setNotifications(res.data);
        } catch { /* ignore */ }
        setLoading(false);
    };

    const markAsRead = async (id) => {
        try {
            await api.put(`/notifications/${id}/read`);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch { /* ignore */ }
    };

    const markAllRead = async () => {
        try {
            await api.put('/notifications/read-all');
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            setUnreadCount(0);
        } catch { /* ignore */ }
    };

    const handleBellClick = () => {
        if (!open) fetchNotifications();
        setOpen(!open);
    };

    const [pushStatus, setPushStatus] = useState(pushEnabled ? 'ON' : 'OFF');

    const registerPush = async () => {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            setPushStatus('Not Supported');
            return;
        }
        try {
            setPushStatus('Registering...');
            const reg = await navigator.serviceWorker.register('/sw.js');
            await navigator.serviceWorker.ready;

            setPushStatus('Permission?');
            const permission = await Notification.requestPermission();
            if (permission !== 'granted') {
                setPushStatus('Blocked');
                return;
            }

            setPushStatus('Subscribing...');
            let sub = await reg.pushManager.getSubscription();
            if (!sub) {
                sub = await reg.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
                });
            }

            setPushStatus('Saving...');
            const key = sub.toJSON();
            await api.post('/notifications/subscribe', {
                endpoint: key.endpoint,
                p256dh: key.keys.p256dh,
                auth: key.keys.auth,
            });
            setPushEnabled(true);
            setPushStatus('ON');
        } catch (err) {
            console.error('Push registration failed:', err);
            setPushStatus('Err: ' + (err.message || 'Check Browser'));
        }
    };

    const sendTestNotification = async (priority) => {
        try {
            await api.post('/notifications/test', {
                title: `Test ${priority.toUpperCase()} Notification`,
                message: `This is a ${priority} priority test notification sent at ${new Date().toLocaleTimeString()}.`,
                priority
            });
            fetchNotifications();
            fetchUnreadCount();
        } catch { /* ignore */ }
    };

    return (
        <div ref={dropdownRef} style={{ position: 'relative' }}>
            {/* Bell Button */}
            <button
                onClick={handleBellClick}
                style={{
                    background: 'none', border: 'none', cursor: 'pointer', position: 'relative',
                    fontSize: '1.3rem', padding: '4px 8px', borderRadius: '8px',
                    transition: 'background 0.2s',
                    ...(open ? { background: 'var(--bg-secondary)' } : {}),
                }}
                title="Notifications"
            >
                🔔
                {unreadCount > 0 && (
                    <span style={{
                        position: 'absolute', top: 0, right: 2, background: '#ef4444',
                        color: 'white', fontSize: '0.6rem', fontWeight: 800,
                        width: 18, height: 18, borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: '2px solid white',
                        animation: 'pulse 2s ease-in-out infinite',
                    }}>
                        {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                )}
            </button>

            {/* Dropdown Panel */}
            {open && (
                <div style={{
                    position: 'absolute', top: '100%', right: 0, marginTop: 8,
                    width: 380, maxHeight: 500,
                    background: 'rgba(255,255,255,0.97)', backdropFilter: 'blur(20px)',
                    borderRadius: 16, border: '1px solid var(--border)',
                    boxShadow: '0 20px 60px rgba(0,0,0,0.15), 0 4px 12px rgba(0,0,0,0.08)',
                    zIndex: 1000, overflow: 'hidden',
                    animation: 'slideDown 0.2s ease-out',
                }}>
                    {/* Header */}
                    <div style={{
                        padding: '14px 18px', borderBottom: '1px solid var(--border)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    }}>
                        <h3 style={{ margin: 0, fontSize: '0.95rem', fontWeight: 700 }}>
                            Notifications
                        </h3>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                            <button 
                                onClick={registerPush}
                                style={{
                                    background: 'none', border: 'none', cursor: pushEnabled ? 'default' : 'pointer',
                                    fontSize: '0.65rem',
                                    color: pushEnabled ? '#22c55e' : '#6366f1', fontWeight: 600,
                                    textDecoration: pushEnabled ? 'none' : 'underline'
                                }}
                                title={pushEnabled ? "Push notifications enabled" : "Click to enable push notifications"}
                            >
                                {pushEnabled ? '🟢 Push ON' : `⚪ ${pushStatus}`}
                            </button>
                            {unreadCount > 0 && (
                                <button onClick={markAllRead} style={{
                                    background: 'none', border: 'none', cursor: 'pointer',
                                    color: '#6366f1', fontSize: '0.72rem', fontWeight: 600,
                                }}>
                                    Mark all read
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Notification List */}
                    <div style={{ overflowY: 'auto', maxHeight: 370 }}>
                        {loading ? (
                            <div style={{ padding: 24, textAlign: 'center', color: 'var(--text-muted)' }}>
                                Loading...
                            </div>
                        ) : notifications.length === 0 ? (
                            <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                                <p style={{ fontSize: '2rem', margin: 0 }}>🔕</p>
                                <p style={{ fontSize: '0.85rem', margin: '8px 0 0' }}>No notifications yet</p>
                            </div>
                        ) : (
                            notifications.map(n => (
                                <div
                                    key={n.id}
                                    onClick={() => { if (!n.is_read) markAsRead(n.id); }}
                                    style={{
                                        padding: '12px 18px', cursor: 'pointer',
                                        borderBottom: '1px solid rgba(0,0,0,0.04)',
                                        background: n.is_read ? 'transparent' : 'rgba(99,102,241,0.04)',
                                        transition: 'background 0.15s',
                                        display: 'flex', gap: 12, alignItems: 'flex-start',
                                    }}
                                    onMouseOver={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.02)'}
                                    onMouseOut={(e) => e.currentTarget.style.background = n.is_read ? 'transparent' : 'rgba(99,102,241,0.04)'}
                                >
                                    <span style={{ fontSize: '1.2rem', marginTop: 2 }}>
                                        {typeIcons[n.type] || '🔔'}
                                    </span>
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <p style={{
                                                margin: 0, fontSize: '0.82rem',
                                                fontWeight: n.is_read ? 500 : 700,
                                                color: n.is_read ? 'var(--text-muted)' : 'var(--text-main)',
                                            }}>
                                                {n.title}
                                            </p>
                                            {!n.is_read && (
                                                <span style={{
                                                    width: 8, height: 8, borderRadius: '50%',
                                                    background: priorityColors[n.priority] || '#6366f1',
                                                    flexShrink: 0, marginLeft: 8,
                                                }} />
                                            )}
                                        </div>
                                        <p style={{
                                            margin: '3px 0 0', fontSize: '0.73rem',
                                            color: 'var(--text-muted)', lineHeight: 1.4,
                                            overflow: 'hidden', textOverflow: 'ellipsis',
                                            display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                                        }}>
                                            {n.message}
                                        </p>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                                            <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>
                                                {timeAgo(n.created_at)}
                                            </span>
                                            <span style={{
                                                fontSize: '0.58rem', padding: '1px 6px', borderRadius: 8,
                                                background: `${priorityColors[n.priority] || '#6366f1'}15`,
                                                color: priorityColors[n.priority] || '#6366f1',
                                                fontWeight: 600, textTransform: 'uppercase',
                                            }}>
                                                {n.priority}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Animations */}
            <style>{`
                @keyframes pulse {
                    0%, 100% { transform: scale(1); }
                    50% { transform: scale(1.15); }
                }
                @keyframes slideDown {
                    from { opacity: 0; transform: translateY(-8px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            `}</style>
        </div>
    );
};

export default NotificationBell;
