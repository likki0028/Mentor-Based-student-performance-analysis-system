import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';

const SubjectClassroom = () => {
    const { id } = useParams();
    const [subject, setSubject] = useState(null);
    const [assignments, setAssignments] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('materials');
    const [quizzes, setQuizzes] = useState([]);
    const [takingQuiz, setTakingQuiz] = useState(null); // quiz detail object when taking
    const [quizAnswers, setQuizAnswers] = useState({}); // { question_id: 'a'|'b'|'c'|'d' }
    const [quizSubmitting, setQuizSubmitting] = useState(false);
    const [quizResult, setQuizResult] = useState(null);

    // Doubts & Syllabus
    const [doubts, setDoubts] = useState([]);
    const [doubtsLoading, setDoubtsLoading] = useState(false);
    const [showDoubtForm, setShowDoubtForm] = useState(false);
    const [doubtForm, setDoubtForm] = useState({ title: '', content: '' });
    const [newComment, setNewComment] = useState({});
    const [syllabusData, setSyllabusData] = useState({ topics: [], total: 0, completed: 0, percentage: 0 });
    const [meetings, setMeetings] = useState([]);

    // Marks & Attendance
    const [myMarks, setMyMarks] = useState([]);
    const [myAttendance, setMyAttendance] = useState([]);
    const [studentProfile, setStudentProfile] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // 1. Always get the subject first, as it's the core of the page
                const subRes = await api.get(`/students/subjects/${id}`);
                setSubject(subRes.data);

                // 2. Fetch assignments and materials in parallel, but handle them safely
                const [assignRes, matRes] = await Promise.all([
                    api.get(`/assignments/?subject_id=${id}`).catch(err => {
                        console.error('Assignments Load Error:', err);
                        return { data: [] };
                    }),
                    api.get(`/materials/subject/${id}`).catch(err => {
                        console.error('Materials Load Error:', err);
                        return { data: [] };
                    })
                ]);

                setAssignments(assignRes.data || []);
                setMaterials(matRes.data || []);

                // Fetch quizzes for this subject
                try {
                    const quizRes = await api.get(`/quizzes/?subject_id=${id}`);
                    setQuizzes(quizRes.data || []);
                } catch { setQuizzes([]); }

                // Fetch doubts
                try {
                    const doubtRes = await api.get(`/doubts/subject/${id}`);
                    setDoubts(doubtRes.data || []);
                } catch { setDoubts([]); }

                // Fetch syllabus
                try {
                    const sylRes = await api.get(`/syllabus/subject/${id}`);
                    setSyllabusData(sylRes.data);
                } catch { setSyllabusData({ topics: [], total: 0, completed: 0, percentage: 0 }); }
                
                // Fetch meetings
                try {
                    const meetRes = await api.get(`/meetings/subject/${id}`);
                    setMeetings(meetRes.data || []);
                } catch { setMeetings([]); }

                // Fetch student profile + marks + attendance
                try {
                    const profRes = await api.get('/students/me');
                    setStudentProfile(profRes.data);
                    const [marksRes, attRes] = await Promise.all([
                        api.get(`/students/${profRes.data.id}/marks`),
                        api.get(`/students/${profRes.data.id}/attendance`)
                    ]);
                    // Filter marks for this subject only
                    setMyMarks((marksRes.data || []).filter(m => m.subject_id === parseInt(id)));
                    setMyAttendance((attRes.data || []).filter(a => a.subject_name === subRes.data.name));
                } catch { /* student profile may not exist */ }
            } catch (err) {
                console.error('Core Classroom Error:', err);
                setSubject(null);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleStartQuiz = async (quizId) => {
        try {
            const res = await api.get(`/quizzes/${quizId}`);
            if (res.data.already_attempted) {
                toast.error('You have already taken this quiz');
                return;
            }
            if (res.data.status !== 'active') {
                toast.error('This quiz is not currently active');
                return;
            }
            setTakingQuiz(res.data);
            setQuizAnswers({});
            setQuizResult(null);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to load quiz');
        }
    };

    const handleSubmitQuiz = async () => {
        if (!takingQuiz) return;
        const unanswered = takingQuiz.questions.filter(q => !quizAnswers[q.id]);
        if (unanswered.length > 0) {
            if (!window.confirm(`You have ${unanswered.length} unanswered question(s). Submit anyway?`)) return;
        }
        setQuizSubmitting(true);
        try {
            const answers = Object.entries(quizAnswers).map(([qid, opt]) => ({
                question_id: parseInt(qid),
                selected_option: opt
            }));
            const res = await api.post(`/quizzes/${takingQuiz.id}/submit`, { answers });
            setQuizResult(res.data);
            toast.success(`Quiz submitted! Score: ${res.data.marks_obtained}/${res.data.total_marks}`);
            // Refresh quiz list
            const quizRes = await api.get(`/quizzes/?subject_id=${id}`);
            setQuizzes(quizRes.data || []);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to submit quiz');
        }
        setQuizSubmitting(false);
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="skeleton" style={{ height: 200, borderRadius: 8, marginBottom: '2rem' }}></div>
                    <div className="grid grid-3">
                        <div className="skeleton" style={{ height: 100 }}></div>
                        <div className="skeleton" style={{ height: 100, gridColumn: 'span 2' }}></div>
                    </div>
                </div>
            </>
        );
    }

    if (!subject) {
        return (
            <>
                <Navbar />
                <div className="container text-center" style={{ marginTop: '5rem' }}>
                    <h2>Subject not found</h2>
                    <Link to="/student"><button>Back to Dashboard</button></Link>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            
            <div className="container page-enter" style={{ maxWidth: 1000 }}>
                {/* Banner */}
                <div className="classroom-banner" style={{
                    background: 'var(--gradient-primary)',
                    padding: '2.5rem',
                    borderRadius: '8px',
                    color: 'white',
                    marginBottom: '1.5rem',
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    <h1 style={{ color: 'white', fontSize: '2.25rem', marginBottom: '0.5rem' }}>{subject.name}</h1>
                    <p style={{ opacity: 0.9, fontSize: '1.125rem' }}>{subject.code || 'Semester 6'} • Section A</p>
                </div>

                {/* Tabs */}
                <div className="flex gap-6" style={{ borderBottom: '1px solid var(--border)', marginBottom: '2rem', padding: '0 1rem' }}>
                    {['materials', 'assignments', 'marks', 'attendance', 'quizzes', 'meetings', 'doubts', 'syllabus', 'people'].map(tab => (
                        <button key={tab} 
                            onClick={() => setActiveTab(tab)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: activeTab === tab ? 'var(--primary)' : 'var(--text-muted)',
                                padding: '1rem 0.5rem',
                                fontSize: '0.9rem',
                                fontWeight: 600,
                                borderRadius: 0,
                                borderBottom: activeTab === tab ? '3px solid var(--primary)' : '3px solid transparent',
                                transform: 'none',
                                boxShadow: 'none'
                            }}>
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="classroom-content">
                    {activeTab === 'materials' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ borderBottom: '2px solid var(--success)', paddingBottom: '0.5rem', color: 'var(--success)' }}>📚 Materials</h2>
                            <div className="grid grid-2 gap-4" style={{ marginTop: '0.5rem' }}>
                                {materials.map((m, i) => (
                                    <a href={m.file_url} target="_blank" rel="noreferrer" key={i} className="card flex items-center gap-4" style={{ padding: '1rem', textDecoration: 'none' }}>
                                        <div style={{ fontSize: '1.5rem' }}>🗂️</div>
                                        <div>
                                            <p style={{ fontWeight: 600, color: 'var(--text-main)', margin: '0 0 0.25rem' }}>{m.title}</p>
                                            <p className="text-xs text-muted" style={{ margin: 0 }}>{m.description || 'Reference Material'}</p>
                                        </div>
                                    </a>
                                ))}
                                {materials.length === 0 && <p className="text-muted">No materials shared yet.</p>}
                            </div>
                        </div>
                    )}

                    {activeTab === 'assignments' && (
                        <div className="flex flex-col gap-6">
                            <section>
                                <h2 style={{ borderBottom: '2px solid var(--primary)', paddingBottom: '0.5rem', color: 'var(--primary)' }}>Assignments</h2>
                                <div className="flex flex-col gap-2" style={{ marginTop: '1rem' }}>
                                    {assignments.map((a) => (
                                        <Link to={`/student/assignment/${a.id}`} key={a.id} className="card flex justify-between items-center hover-lift" style={{ padding: '1rem', cursor: 'pointer', textDecoration: 'none', color: 'inherit' }}>
                                            <div className="flex items-center gap-4">
                                                <div style={{ fontSize: '1.25rem' }}>📄</div>
                                                <div>
                                                    <p style={{ fontWeight: 600 }}>{a.title}</p>
                                                    <p className="text-xs text-muted">Due {new Date(a.due_date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</p>
                                                </div>
                                            </div>
                                            <span className="btn-secondary" style={{ fontSize: '0.75rem' }}>View Submission</span>
                                        </Link>
                                    ))}
                                    {assignments.length === 0 && <p className="text-muted">No assignments listed.</p>}
                                </div>
                            </section>
                        </div>
                    )}

                    {/* Quizzes Tab */}
                    {activeTab === 'quizzes' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ marginBottom: 0 }}>🧠 Quizzes</h2>

                            {/* Taking a quiz */}
                            {takingQuiz && !quizResult ? (
                                <div className="card" style={{ padding: '2rem' }}>
                                    <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '1.5rem' }}>
                                        <div>
                                            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>{takingQuiz.title}</h2>
                                            <p className="text-xs text-muted">{takingQuiz.questions.length} questions · {takingQuiz.total_marks} marks</p>
                                        </div>
                                        <button className="btn-secondary" onClick={() => { setTakingQuiz(null); setQuizAnswers({}); }} style={{ fontSize: '0.8rem' }}>Cancel</button>
                                    </div>

                                    {takingQuiz.questions.map((q, idx) => (
                                        <div key={q.id} className="card" style={{ padding: '1.25rem', marginBottom: '1rem', background: 'var(--bg-secondary)' }}>
                                            <p className="font-semibold" style={{ marginBottom: '0.75rem' }}>
                                                <span style={{ color: 'var(--primary)', marginRight: '0.5rem' }}>Q{idx + 1}.</span>
                                                {q.question_text}
                                                <span className="text-xs text-muted" style={{ marginLeft: '0.5rem' }}>({q.marks} mark{q.marks > 1 ? 's' : ''})</span>
                                            </p>
                                            {['a', 'b', 'c', 'd'].map(opt => (
                                                <label key={opt} style={{
                                                    display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.6rem 0.75rem',
                                                    borderRadius: '8px', marginBottom: '0.4rem', cursor: 'pointer',
                                                    background: quizAnswers[q.id] === opt ? 'var(--primary-light)' : 'transparent',
                                                    border: quizAnswers[q.id] === opt ? '2px solid var(--primary)' : '2px solid var(--border)',
                                                    transition: 'all 0.15s'
                                                }}>
                                                    <input type="radio" name={`q_${q.id}`} value={opt}
                                                        checked={quizAnswers[q.id] === opt}
                                                        onChange={() => setQuizAnswers({ ...quizAnswers, [q.id]: opt })}
                                                        style={{ margin: 0 }} />
                                                    <span className="font-semibold text-xs" style={{ color: 'var(--primary)', minWidth: 18 }}>{opt.toUpperCase()}</span>
                                                    <span className="text-sm">{q[`option_${opt}`]}</span>
                                                </label>
                                            ))}
                                        </div>
                                    ))}

                                    <button className="btn-primary" onClick={handleSubmitQuiz} disabled={quizSubmitting}
                                        style={{ width: '100%', marginTop: '1rem', fontSize: '1rem', padding: '0.75rem' }}>
                                        {quizSubmitting ? 'Submitting...' : '📤 Submit Quiz'}
                                    </button>
                                </div>
                            ) : quizResult ? (
                                /* Show result after submission */
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <div style={{ fontSize: '4rem', marginBottom: '0.75rem' }}>🎉</div>
                                    <h2 style={{ marginBottom: '0.5rem' }}>Quiz Submitted!</h2>
                                    <p className="text-muted" style={{ marginBottom: '1.5rem' }}>{takingQuiz.title}</p>
                                    <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--primary)', marginBottom: '0.25rem' }}>
                                        {quizResult.marks_obtained} / {quizResult.total_marks}
                                    </div>
                                    <p className="text-muted">{quizResult.percentage}%</p>
                                    <button className="btn-secondary" onClick={() => { setTakingQuiz(null); setQuizResult(null); }}
                                        style={{ marginTop: '1.5rem' }}>Back to Quizzes</button>
                                </div>
                            ) : (
                                /* Quiz list */
                                quizzes.length === 0 ? (
                                    <div className="card text-center" style={{ padding: '3rem' }}>
                                        <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>🧠</div>
                                        <p className="text-muted">No quizzes available for this subject.</p>
                                    </div>
                                ) : (
                                    <div className="flex flex-col gap-3">
                                        {quizzes.map(q => {
                                            const isActive = q.status === 'active';
                                            const isEnded = q.status === 'ended';
                                            const statusLabel = isActive ? '🟢 Active' : isEnded ? '⚫ Ended' : '🔵 Upcoming';
                                            const statusBg = isActive ? 'rgba(34,197,94,0.15)' : isEnded ? 'rgba(156,163,175,0.15)' : 'rgba(59,130,246,0.15)';
                                            const statusColor = isActive ? '#16a34a' : isEnded ? '#6b7280' : '#2563eb';
                                            return (
                                                <div key={q.id} className="card" style={{ padding: '1.25rem 1.5rem' }}>
                                                    <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
                                                        <div>
                                                            <h3 style={{ margin: 0, fontSize: '1rem' }}>{q.title}</h3>
                                                            <p className="text-xs text-muted" style={{ margin: '0.25rem 0 0' }}>
                                                                {q.question_count} question{q.question_count !== 1 ? 's' : ''} · {q.total_marks} marks
                                                            </p>
                                                            <p className="text-xs text-muted" style={{ margin: '0.25rem 0 0' }}>
                                                                {q.start_time ? new Date(q.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : ''}
                                                                {' → '}
                                                                {q.end_time ? new Date(q.end_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : ''}
                                                            </p>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <span className="badge" style={{ background: statusBg, color: statusColor, fontSize: '0.7rem', fontWeight: 700 }}>{statusLabel}</span>
                                                            {isActive && (
                                                                <button className="btn-primary" onClick={() => handleStartQuiz(q.id)}
                                                                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.9rem' }}>Take Quiz</button>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                )
                            )}
                        </div>
                    )}

                    {/* Meetings Tab */}
                    {activeTab === 'meetings' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ marginBottom: 0 }}>📹 Online Meetings</h2>
                            {meetings.length === 0 ? (
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>📹</div>
                                    <p className="text-muted">No meetings scheduled for this subject.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {meetings.map((m) => {
                                        const isEmergency = m.priority === 'emergency';
                                        return (
                                            <div key={m.id} className="card" style={{ padding: '1.25rem 1.5rem', borderLeft: isEmergency ? '4px solid #ef4444' : '4px solid var(--primary)' }}>
                                                <div className="flex items-start" style={{ justifyContent: 'space-between' }}>
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2" style={{ marginBottom: '0.25rem' }}>
                                                            <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{m.title}</h3>
                                                            {isEmergency && <span className="badge badge-danger" style={{ fontSize: '0.65rem' }}>🚨 Emergency</span>}
                                                        </div>
                                                        <p className="text-sm text-muted" style={{ margin: '0 0 0.5rem' }}>Scheduled for: {new Date(m.meeting_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</p>
                                                        {m.description && <p className="text-sm" style={{ margin: 0 }}>{m.description}</p>}
                                                    </div>
                                                    <div className="flex flex-col gap-2 items-end">
                                                        <a href={m.meeting_link} target="_blank" rel="noreferrer" className="btn-success" style={{ textDecoration: 'none', padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                                                            Join Meeting
                                                        </a>
                                                        <span className="text-xs text-muted">Created: {new Date(m.created_at).toLocaleDateString()}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Doubts Tab */}
                    {activeTab === 'doubts' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
                                <h2 style={{ margin: 0 }}>💬 Doubts Forum</h2>
                                <button className="btn-primary" style={{ fontSize: '0.85rem' }} onClick={() => setShowDoubtForm(!showDoubtForm)}>
                                    {showDoubtForm ? 'Cancel' : '+ Ask a Doubt'}
                                </button>
                            </div>

                            {showDoubtForm && (
                                <div className="card" style={{ padding: '1.25rem' }}>
                                    <input type="text" className="w-full" placeholder="Doubt title..." value={doubtForm.title}
                                        onChange={e => setDoubtForm({ ...doubtForm, title: e.target.value })}
                                        style={{ marginBottom: '0.5rem' }} />
                                    <textarea className="w-full" placeholder="Describe your doubt..." rows={3} value={doubtForm.content}
                                        onChange={e => setDoubtForm({ ...doubtForm, content: e.target.value })}
                                        style={{ marginBottom: '0.75rem', padding: '0.6rem', borderRadius: '6px', border: '1px solid var(--border)', resize: 'vertical' }} />
                                    <button className="btn-primary" style={{ fontSize: '0.85rem' }} onClick={async () => {
                                        if (!doubtForm.title.trim() || !doubtForm.content.trim()) { toast.error('Fill all fields'); return; }
                                        try {
                                            await api.post('/doubts/', { ...doubtForm, subject_id: parseInt(id) });
                                            toast.success('Doubt posted!');
                                            setDoubtForm({ title: '', content: '' });
                                            setShowDoubtForm(false);
                                            const res = await api.get(`/doubts/subject/${id}`); setDoubts(res.data);
                                        } catch { toast.error('Failed to post'); }
                                    }}>Post Doubt</button>
                                </div>
                            )}

                            {doubts.length === 0 ? (
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>💬</div>
                                    <p className="text-muted">No doubts yet. Be the first to ask!</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {doubts.map(d => (
                                        <div key={d.id} className="card" style={{ padding: '1.25rem 1.5rem', borderLeft: d.is_pinned ? '4px solid var(--primary)' : d.is_resolved ? '4px solid #22c55e' : '4px solid var(--border)' }}>
                                            <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                <h3 style={{ margin: 0, fontSize: '1rem' }}>
                                                    {d.is_pinned && '📌 '}{d.title}
                                                </h3>
                                                <span className="badge" style={{ fontSize: '0.65rem', background: d.is_resolved ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: d.is_resolved ? '#16a34a' : '#ef4444' }}>
                                                    {d.is_resolved ? '✅ Resolved' : '❌ Open'}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted" style={{ margin: '0 0 0.5rem' }}>by {d.student_name} · {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}</p>
                                            <p className="text-sm" style={{ lineHeight: 1.6 }}>{d.content}</p>

                                            {d.comments?.length > 0 && (
                                                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                                                    {d.comments.map(c => (
                                                        <div key={c.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                                            <span className="font-semibold text-xs">{c.user_name}</span>
                                                            <span className="badge" style={{ fontSize: '0.55rem', padding: '0.1rem 0.4rem', marginLeft: '0.5rem', background: c.user_role === 'lecturer' || c.user_role === 'both' ? 'rgba(59,130,246,0.15)' : 'rgba(156,163,175,0.15)', color: c.user_role === 'lecturer' || c.user_role === 'both' ? '#2563eb' : '#6b7280' }}>
                                                                {c.user_role === 'lecturer' || c.user_role === 'both' ? 'Faculty' : 'Student'}
                                                            </span>
                                                            <p className="text-sm" style={{ margin: '0.2rem 0 0' }}>{c.content}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            <div className="flex items-center gap-2" style={{ marginTop: '0.75rem' }}>
                                                <input type="text" value={newComment[d.id] || ''}
                                                    onChange={e => setNewComment({ ...newComment, [d.id]: e.target.value })}
                                                    placeholder="Reply..."
                                                    style={{ flex: 1, padding: '0.4rem 0.75rem', fontSize: '0.85rem', borderRadius: '6px', border: '1px solid var(--border)' }} />
                                                <button className="btn-primary" style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
                                                    onClick={async () => {
                                                        if (!newComment[d.id]?.trim()) return;
                                                        try {
                                                            await api.post(`/doubts/${d.id}/comments`, { content: newComment[d.id] });
                                                            setNewComment({ ...newComment, [d.id]: '' });
                                                            const res = await api.get(`/doubts/subject/${id}`); setDoubts(res.data);
                                                        } catch { toast.error('Failed'); }
                                                    }}>Reply</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Syllabus Tab */}
                    {activeTab === 'syllabus' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ margin: 0 }}>📚 Syllabus Progress</h2>
                            <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
                                <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                    <span className="font-semibold text-sm">Course Completion</span>
                                    <span className="font-semibold" style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>{syllabusData.percentage}%</span>
                                </div>
                                <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', height: '12px', overflow: 'hidden' }}>
                                    <div style={{ width: `${syllabusData.percentage}%`, height: '100%', background: 'var(--gradient-primary)', borderRadius: '8px', transition: 'width 0.4s ease' }} />
                                </div>
                                <p className="text-xs text-muted" style={{ marginTop: '0.5rem' }}>{syllabusData.completed} of {syllabusData.total} topics completed</p>
                            </div>
                            {syllabusData.topics.length === 0 ? (
                                <div className="card text-center" style={{ padding: '2rem' }}>
                                    <p className="text-muted">No syllabus topics added by the lecturer yet.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    {syllabusData.topics.map((t, idx) => (
                                        <div key={t.id} className="card flex items-center" style={{ padding: '0.75rem 1rem', gap: '0.75rem' }}>
                                            <span style={{ fontSize: '1.1rem' }}>{t.is_completed ? '✅' : '⬜'}</span>
                                            <span className="text-sm" style={{ textDecoration: t.is_completed ? 'line-through' : 'none', opacity: t.is_completed ? 0.6 : 1 }}>
                                                <span className="text-xs text-muted" style={{ marginRight: '0.5rem' }}>{idx + 1}.</span>
                                                {t.title}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ===== MARKS TAB (Student) ===== */}
                    {activeTab === 'marks' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ margin: 0 }}>📊 My Marks</h2>
                            {(() => {
                                const mid1 = myMarks.find(m => m.assessment_type === 'mid_1');
                                const mid2 = myMarks.find(m => m.assessment_type === 'mid_2');
                                const assign = myMarks.find(m => m.assessment_type === 'assignment');
                                const daily = myMarks.find(m => m.assessment_type === 'daily_assessment');
                                const mid1Score = mid1 ? mid1.score : null;
                                const mid2Score = mid2 ? mid2.score : null;
                                const assignScore = assign ? assign.score : 0;
                                const dailyScore = daily ? daily.score : 0;
                                let midAvg = null;
                                if (mid1Score !== null && mid2Score !== null) midAvg = (mid1Score + mid2Score) / 2;
                                else if (mid1Score !== null) midAvg = mid1Score;
                                else if (mid2Score !== null) midAvg = mid2Score;
                                const internalTotal = midAvg !== null ? Math.round(midAvg + assignScore + dailyScore) : null;

                                return (
                                    <>
                                        {/* Info card */}
                                        <div className="card" style={{ padding: '1rem 1.5rem', background: 'var(--primary-light)' }}>
                                            <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)' }}>
                                                📐 Internal (40) = Avg of Mid 1 & Mid 2 (30) + Assignment (5) + Daily Assessment (5)
                                            </p>
                                        </div>

                                        {/* Marks grid */}
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
                                            {[
                                                { label: 'Mid 1', score: mid1Score, total: 30, icon: '📝', color: '#3b82f6' },
                                                { label: 'Mid 2', score: mid2Score, total: 30, icon: '📝', color: '#8b5cf6' },
                                                { label: 'Assignment', score: assignScore, total: 5, icon: '📋', color: '#f59e0b' },
                                                { label: 'Daily Assessment', score: dailyScore, total: 5, icon: '🧠', color: '#22c55e' }
                                            ].map((item, i) => (
                                                <div key={i} className="card" style={{ padding: '1.25rem', borderLeft: `4px solid ${item.color}` }}>
                                                    <p className="text-xs text-muted" style={{ marginBottom: '0.25rem' }}>{item.icon} {item.label}</p>
                                                    <div style={{ fontSize: '1.75rem', fontWeight: 800, color: item.score !== null ? item.color : 'var(--text-muted)' }}>
                                                        {item.score !== null ? item.score : '—'}
                                                        <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)' }}> / {item.total}</span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>

                                        {/* Internal Total */}
                                        <div className="card" style={{ padding: '1.5rem', textAlign: 'center', background: 'var(--bg-secondary)' }}>
                                            <p className="text-xs text-muted" style={{ marginBottom: '0.5rem' }}>🎯 Internal Total</p>
                                            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: internalTotal !== null ? (internalTotal >= 16 ? '#22c55e' : '#ef4444') : 'var(--text-muted)' }}>
                                                {internalTotal !== null ? internalTotal : '—'}
                                                <span style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--text-muted)' }}> / 40</span>
                                            </div>
                                            {internalTotal !== null && (
                                                <span className="badge" style={{ marginTop: '0.5rem', fontSize: '0.75rem', background: internalTotal >= 16 ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: internalTotal >= 16 ? '#16a34a' : '#ef4444' }}>
                                                    {internalTotal >= 32 ? '🌟 Excellent' : internalTotal >= 24 ? '👍 Good' : internalTotal >= 16 ? '⚡ Average' : '⚠️ Needs Improvement'}
                                                </span>
                                            )}
                                        </div>
                                    </>
                                );
                            })()}
                        </div>
                    )}

                    {/* ===== ATTENDANCE TAB (Student) ===== */}
                    {activeTab === 'attendance' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
                                <h2 style={{ margin: 0 }}>📋 My Attendance</h2>
                                {(() => {
                                    const total = myAttendance.length;
                                    const present = myAttendance.filter(a => a.status).length;
                                    const pct = total > 0 ? Math.round((present / total) * 100) : 0;
                                    return (
                                        <span className="badge" style={{ fontSize: '0.85rem', fontWeight: 700, padding: '0.4rem 0.8rem', background: pct >= 75 ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: pct >= 75 ? '#16a34a' : '#ef4444' }}>
                                            {present}/{total} ({pct}%)
                                        </span>
                                    );
                                })()}
                            </div>

                            {myAttendance.length === 0 ? (
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <p className="text-muted">No attendance records yet.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    {[...myAttendance].sort((a, b) => new Date(b.date) - new Date(a.date)).map((a, i) => (
                                        <div key={i} className="card flex items-center" style={{ padding: '0.75rem 1rem', gap: '0.75rem' }}>
                                            <span style={{ fontSize: '1.2rem' }}>{a.status ? '✅' : '❌'}</span>
                                            <span className="flex-1 text-sm font-semibold">{new Date(a.date).toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}</span>
                                            <span className="badge" style={{ fontSize: '0.7rem', background: a.status ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: a.status ? '#16a34a' : '#ef4444' }}>
                                                {a.status ? 'Present' : 'Absent'}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'people' && (
                        <div className="flex flex-col gap-8">
                            <section>
                                <h2 style={{ borderBottom: '1px solid var(--primary)', paddingBottom: '0.5rem', color: 'var(--primary)', display: 'flex', justifyBetween: 'center', alignItems: 'center' }}>
                                    Teachers
                                </h2>
                                <div className="flex items-center gap-4" style={{ padding: '1rem 0', borderBottom: '1px solid var(--border)' }}>
                                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>L</div>
                                    <p style={{ fontWeight: 500 }}>Prof. Lecturer A</p>
                                </div>
                            </section>

                            <section>
                                <h2 style={{ borderBottom: '1px solid var(--primary)', paddingBottom: '0.5rem', color: 'var(--primary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    Classmates
                                    <span className="text-xs text-muted">3 students</span>
                                </h2>
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="flex items-center gap-4" style={{ padding: '1rem 0', borderBottom: '1px solid var(--border)' }}>
                                        <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--secondary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>S</div>
                                        <p style={{ fontWeight: 500 }}>Student {i}</p>
                                    </div>
                                ))}
                            </section>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default SubjectClassroom;
