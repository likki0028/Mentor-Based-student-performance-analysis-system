
import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import studentService from '../services/student.service';
import facultyService from '../services/faculty.service';
import analyticsService from '../services/analytics.service';
import Navbar from '../components/Navbar';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from 'recharts';
import toast, { Toaster } from 'react-hot-toast';

const COLORS = ['#6366f1', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6', '#06b6d4'];

const StudentDetail = () => {
    const { user } = useAuth();
    const [searchParams] = useSearchParams();
    const studentId = searchParams.get('id');
    const [analytics, setAnalytics] = useState(null);
    const [remarks, setRemarks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedSem, setSelectedSem] = useState(null);
    const [remarkText, setRemarkText] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [expandedSubject, setExpandedSubject] = useState(null);
    const [gpaPrediction, setGpaPrediction] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                let sid = studentId;

                if (!sid) {
                    // If no ID provided, fetch current student's profile
                    const profileRes = { data: await studentService.getProfile() };
                    sid = profileRes.data.id;
                }

                const [analyticsRes, remarksRes] = await Promise.all([
                    analyticsService.getStudentAnalytics(sid).then(data => ({ data })),
                    facultyService.getRemarks(sid).then(data => ({ data })).catch(() => ({ data: [] }))
                ]);

                setAnalytics(analyticsRes.data);
                setRemarks(remarksRes.data);
                
                // Default to current semester
                setSelectedSem(analyticsRes.data.current_semester);

                // Fetch GPA prediction
                try {
                    const gpaRes = await analyticsService.predictGPA(sid || analyticsRes.data.student_id);
                    setGpaPrediction(gpaRes);
                } catch (e) {
                    console.log('GPA prediction not available');
                }
            } catch (err) {
                console.error('Failed to fetch student data:', err);
                toast.error('Failed to load student details');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [studentId]);

    const handleAddRemark = async () => {
        if (!remarkText.trim() || !analytics) return;
        setSubmitting(true);
        try {
            await facultyService.addRemark({
                student_id: analytics.student_id,
                message: remarkText
            });
            toast.success('Remark added successfully');
            setRemarkText('');
            // Refresh remarks
            const res = { data: await facultyService.getRemarks(analytics.student_id) };
            setRemarks(res.data);
        } catch (err) {
            toast.error('Failed to add remark');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                
                <div className="container page-enter">
                    <div className="grid grid-3" style={{ marginTop: '2rem' }}>
                        {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                    <div className="grid grid-2" style={{ marginTop: '1.5rem' }}>
                        {[1, 2].map(i => <div key={i} className="skeleton" style={{ height: 250 }}></div>)}
                    </div>
                </div>
            </>
        );
    }

    if (!analytics) {
        return (
            <>
                <Navbar />
                <div className="container">
                    <div className="card empty-state">
                        <div className="emoji">😕</div>
                        <p>Student data not found.</p>
                        <Link to="/"><button style={{ marginTop: '1rem' }}>Go Back</button></Link>
                    </div>
                </div>
            </>
        );
    }

    const riskBadge = analytics.risk_status === 'Safe' ? 'badge-safe'
        : analytics.risk_status === 'Warning' ? 'badge-warning' : 'badge-danger';

    // Prepare chart data safely
    const subjectChartData = (analytics.subject_stats || []).map(s => ({
        name: s.subject_code || s?.subject_name?.substring(0, 8) || 'Unknown',
        attendance: s.attendance_percentage || 0,
        marks: s.average_marks || 0
    }));

    const pieData = [
        { name: 'Present', value: analytics.classes_attended || 0 },
        { name: 'Absent', value: Math.max(0, (analytics.total_classes || 0) - (analytics.classes_attended || 0)) }
    ];
    
    const gpaChartData = (analytics.semester_stats || [])
        .map(s => ({
            name: `Sem ${s.semester}`,
            gpa: s.sgpa,
            attendance: s.attendance_percentage
        }));

    const isFacultyOrAdmin = user?.role !== 'student';

    return (
        <>
            <Navbar />
            
            <div className="container page-enter">
                {/* Header */}
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 style={{ marginBottom: '0.25rem' }}>{analytics.name}</h1>
                            <span className={`badge ${riskBadge}`}>{analytics.risk_status}</span>
                        </div>
                        <p className="text-muted">
                            Roll No: {analytics.enrollment_number} &nbsp;•&nbsp; Semester {analytics.current_semester}
                        </p>
                    </div>
                    <Link to={user?.role === 'student' ? '/student' : '/mentor'}>
                        <button className="btn-secondary">← Back to Dashboard</button>
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                    <div className="stat-card">
                        <p className="label">Cumulative Historical Attendance</p>
                        <p style={{ fontSize: '2rem', fontWeight: 800, color: analytics.historical_attendance_percentage >= 75 ? '#22c55e' : '#ef4444' }}>
                            {analytics.historical_attendance_percentage}%
                        </p>
                        <div className="progress-bar" style={{ marginTop: '0.5rem' }}>
                            <div className={`progress-fill ${analytics.historical_attendance_percentage >= 75 ? 'success' : 'danger'}`}
                                style={{ width: `${Math.min(analytics.historical_attendance_percentage, 100)}%` }}></div>
                        </div>
                    </div>
                    <div className="stat-card accent">
                        <p className="label">Cumulative GPA</p>
                        <p style={{ fontSize: '2.4rem', fontWeight: 900, color: '#f59e0b' }}>
                            {analytics.cgpa || "0.00"}
                        </p>
                        <p className="text-xs text-muted">Across {analytics.semester_stats?.length || 0} completed semesters</p>
                    </div>
                </div>

                {/* GPA & Attendance Trend Chart */}
                {analytics.semester_stats?.length > 0 && (
                    <div className="card" style={{ marginBottom: '2rem' }}>
                        <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem' }}>
                            <h3 style={{ border: 'none', padding: 0, margin: 0 }}>📈 GPA & Attendance Trend</h3>
                            <div className="flex gap-4">
                                <span className="flex items-center gap-1 text-sm"><div style={{width: 12, height: 12, borderRadius: '50%', background: '#6366f1'}}></div> SGPA</span>
                                <span className="flex items-center gap-1 text-sm"><div style={{width: 12, height: 12, borderRadius: '50%', background: '#22c55e'}}></div> Attendance</span>
                            </div>
                        </div>
                        <ResponsiveContainer width="100%" height={260}>
                            <LineChart data={gpaChartData}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                <XAxis dataKey="name" axisLine={false} tickLine={false} dy={10} fontSize={12} />
                                <YAxis yAxisId="left" domain={[0, 10]} axisLine={false} tickLine={false} fontSize={12} />
                                <YAxis yAxisId="right" orientation="right" domain={[0, 100]} axisLine={false} tickLine={false} fontSize={12} unit="%" />
                                <Tooltip 
                                    contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                                />
                                <Line yAxisId="left" type="monotone" dataKey="gpa" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} name="SGPA" />
                                <Line yAxisId="right" type="monotone" dataKey="attendance" stroke="#22c55e" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Attendance" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Subject Competency Radar Chart + AI Insights */}
                {(analytics.current_semester_details?.subjects || []).length > 0 && (() => {
                    const subjectData = (analytics.current_semester_details?.subjects || []).map(s => {
                        return {
                            subject: s.subject_name || 'Unknown',
                            attendance: s.attendance_percentage || 0,
                            marks: s.overall_marks_percentage || 0,
                            fullName: s.subject_name
                        };
                    });

                    // Generate AI Insights from the data
                    const insights = [];
                    const avgAtt = subjectData.reduce((sum, s) => sum + s.attendance, 0) / subjectData.length;
                    const avgMarks = subjectData.reduce((sum, s) => sum + s.marks, 0) / subjectData.length;
                    const lowAttSubjects = subjectData.filter(s => s.attendance < 75);
                    const lowMarksSubjects = subjectData.filter(s => s.marks < 40);
                    const strongSubjects = subjectData.filter(s => s.marks >= 70 && s.attendance >= 80);
                    const highMarksLowAtt = subjectData.filter(s => s.marks >= 60 && s.attendance < 70);
                    const highAttLowMarks = subjectData.filter(s => s.attendance >= 80 && s.marks < 40);

                    if (lowAttSubjects.length > 0) {
                        insights.push({ type: 'danger', icon: '🚨', text: `Attendance below 75% in ${lowAttSubjects.map(s => s.fullName).join(', ')}. ${lowAttSubjects.length > 1 ? 'These subjects need' : 'This subject needs'} immediate intervention to avoid debarment.` });
                    }
                    if (lowMarksSubjects.length > 0) {
                        insights.push({ type: 'warning', icon: '📉', text: `Sessional marks below 40% in ${lowMarksSubjects.map(s => s.fullName).join(', ')}. Student may struggle in end-semester exams without focused revision.` });
                    }
                    if (highMarksLowAtt.length > 0) {
                        insights.push({ type: 'info', icon: '💡', text: `${highMarksLowAtt.map(s => s.fullName).join(', ')}: Good marks despite low attendance — student may be self-studying. Encourage consistent class participation.` });
                    }
                    if (highAttLowMarks.length > 0) {
                        insights.push({ type: 'warning', icon: '🔍', text: `${highAttLowMarks.map(s => s.fullName).join(', ')}: High attendance but poor marks — student may need additional academic support or tutoring.` });
                    }
                    if (strongSubjects.length > 0) {
                        insights.push({ type: 'success', icon: '⭐', text: `Excelling in ${strongSubjects.map(s => s.fullName).join(', ')} with strong marks and attendance. These are the student's key strengths.` });
                    }
                    if (avgAtt >= 80 && avgMarks >= 60) {
                        insights.push({ type: 'success', icon: '🎯', text: `Overall trajectory is positive. Average attendance is ${avgAtt.toFixed(0)}% and average marks are ${avgMarks.toFixed(0)}%. Student is on track.` });
                    } else if (avgAtt < 65 || avgMarks < 35) {
                        insights.push({ type: 'danger', icon: '⚠️', text: `Overall performance is concerning. Average attendance: ${avgAtt.toFixed(0)}%, Average marks: ${avgMarks.toFixed(0)}%. Recommend a 1-on-1 counseling session.` });
                    }

                    const insightColors = { danger: '#fef2f2', warning: '#fffbeb', info: '#eff6ff', success: '#f0fdf4' };
                    const insightBorders = { danger: '#fca5a5', warning: '#fcd34d', info: '#93c5fd', success: '#86efac' };

                    return (
                        <>
                            <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
                                <h3 style={{ border: 'none', padding: 0, margin: '0 0 0.25rem 0' }}>🕸️ Subject Competency Map</h3>
                                <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1rem' }}>Attendance vs. Marks across current semester subjects</p>
                                <ResponsiveContainer width="100%" height={320}>
                                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={subjectData}>
                                        <PolarGrid stroke="#e2e8f0" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#475569' }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
                                        <Radar name="Attendance" dataKey="attendance" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} strokeWidth={2} />
                                        <Radar name="Marks" dataKey="marks" stroke="#6366f1" fill="#6366f1" fillOpacity={0.4} strokeWidth={3} />
                                        <Tooltip contentStyle={{ borderRadius: 10, border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)', fontSize: '0.85rem' }} />
                                    </RadarChart>
                                </ResponsiveContainer>
                                <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '0.5rem', fontSize: '0.82rem' }}>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#22c55e' }}></div> Attendance</span>
                                    <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 12, height: 12, borderRadius: '50%', background: '#6366f1' }}></div> Marks</span>
                                </div>
                            </div>

                            {/* AI Insights Card */}
                            {insights.length > 0 && (
                                <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
                                    <h3 style={{ border: 'none', padding: 0, margin: '0 0 0.5rem 0' }}>🧠 AI Insights</h3>
                                    <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1rem' }}>Auto-generated observations from the competency map</p>
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                                        {insights.map((ins, i) => (
                                            <div key={i} style={{
                                                padding: '0.75rem 1rem', borderRadius: 10,
                                                background: insightColors[ins.type],
                                                border: `1px solid ${insightBorders[ins.type]}`,
                                                fontSize: '0.85rem', lineHeight: 1.5
                                            }}>
                                                <span style={{ marginRight: 6 }}>{ins.icon}</span>
                                                {ins.text}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </>
                    );
                })()}

                {/* 1. CURRENT SEMESTER DETAILS */}
                <div style={{ marginBottom: '3rem' }}>
                    <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{ fontSize: '1.5rem' }}>📚</span> Current Semester Details (Semester {analytics.current_semester})
                    </h2>
                    
                    <div className="grid grid-2" style={{ marginBottom: '1.5rem' }}>
                        <div className="card" style={{ padding: '1.5rem', background: 'linear-gradient(135deg, #ede9fe 0%, #f0f9ff 100%)', border: '1px solid #c4b5fd' }}>
                            <p className="label" style={{ color: '#7c3aed' }}>🤖 Predicted Semester GPA</p>
                            {gpaPrediction && gpaPrediction.predicted_sgpa ? (
                                <>
                                    <p style={{ fontSize: '1.75rem', fontWeight: 800, color: '#7c3aed' }}>
                                        {gpaPrediction.predicted_sgpa}
                                    </p>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.3rem' }}>
                                        <span style={{
                                            fontSize: '0.65rem', fontWeight: 700, padding: '2px 8px', borderRadius: 10,
                                            background: gpaPrediction.predicted_sgpa >= analytics.cgpa ? '#dcfce7' : '#fef2f2',
                                            color: gpaPrediction.predicted_sgpa >= analytics.cgpa ? '#166534' : '#991b1b'
                                        }}>
                                            {gpaPrediction.predicted_sgpa >= analytics.cgpa ? '↑' : '↓'} vs CGPA {analytics.cgpa}
                                        </span>
                                        <span style={{ fontSize: '0.55rem', color: '#7c3aed', background: '#ede9fe', padding: '2px 6px', borderRadius: 8 }}>
                                            {gpaPrediction.model_type}
                                        </span>
                                    </div>
                                </>
                            ) : (
                                <p style={{ fontSize: '1rem', color: '#94a3b8' }}>Calculating...</p>
                            )}
                        </div>
                        <div className="card" style={{ padding: '1.5rem', background: 'var(--success-light)', border: 'none' }}>
                            <p className="label" style={{ color: 'var(--success)' }}>Attendance</p>
                            <p style={{ fontSize: '1.75rem', fontWeight: 800 }}>{analytics.attendance_percentage || 0}%</p>
                        </div>
                    </div>

                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)', background: '#f8fafc' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem' }}>Active Subject Breakdown</h3>
                        </div>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ margin: 0 }}>
                                <thead>
                                    <tr>
                                        <th>Subject</th>
                                        <th>Credits</th>
                                        <th>Attendance</th>
                                        <th>Details</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {(analytics.current_semester_details?.subjects || []).map((sub, i) => {
                                        const attPct = sub.attendance_percentage || 0;
                                        const attColor = attPct >= 75 ? '#22c55e' : attPct >= 60 ? '#f59e0b' : '#ef4444';
                                        const isExpanded = expandedSubject === i;
                                        const subType = (sub.subject_type || '').toLowerCase();
                                        return (
                                            <React.Fragment key={i}>
                                                <tr style={{ cursor: 'pointer' }} onClick={() => setExpandedSubject(isExpanded ? null : i)}>
                                                    <td>
                                                        <div style={{ fontWeight: 600 }}>{sub.subject_name}</div>
                                                        <div className="text-xs text-muted">{sub.subject_code}</div>
                                                    </td>
                                                    <td>{sub.credits}</td>
                                                    <td>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                            <div style={{ flex: 1, height: 8, borderRadius: 4, background: '#f1f5f9', overflow: 'hidden', minWidth: 60 }}>
                                                                <div style={{ width: `${Math.min(attPct, 100)}%`, height: '100%', borderRadius: 4, background: attColor, transition: 'width 0.5s ease' }}></div>
                                                            </div>
                                                            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: attColor, minWidth: 36 }}>{attPct}%</span>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <button
                                                            onClick={(e) => { e.stopPropagation(); setExpandedSubject(isExpanded ? null : i); }}
                                                            style={{
                                                                fontSize: '0.75rem', padding: '0.3rem 0.8rem', borderRadius: 20,
                                                                background: isExpanded ? '#6366f1' : 'transparent',
                                                                color: isExpanded ? '#fff' : '#6366f1',
                                                                border: '1px solid #6366f1',
                                                                cursor: 'pointer', transition: 'all 0.2s'
                                                            }}
                                                        >
                                                            {isExpanded ? '✕ Hide' : '👁 View'}
                                                        </button>
                                                    </td>
                                                </tr>
                                                {isExpanded && (
                                                    <tr>
                                                        <td colSpan={4} style={{ padding: 0, background: '#f8fafc' }}>
                                                            <div style={{ padding: '1rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                                {/* Mid Marks - for theory and non-credit subjects */}
                                                                {(subType === 'theory' || subType === 'non_credit') && (
                                                                    <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                                                                        <div style={{ flex: 1, minWidth: 140, padding: '0.75rem 1rem', borderRadius: 10, background: '#fff', border: '1px solid #e2e8f0' }}>
                                                                            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Mid 1</div>
                                                                            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: sub.mid_1 ? '#6366f1' : '#94a3b8' }}>
                                                                                {sub.mid_1 || 'Not Yet Conducted'}
                                                                            </div>
                                                                        </div>
                                                                        <div style={{ flex: 1, minWidth: 140, padding: '0.75rem 1rem', borderRadius: 10, background: '#fff', border: '1px solid #e2e8f0' }}>
                                                                            <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Mid 2</div>
                                                                            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: sub.mid_2 ? '#6366f1' : '#94a3b8' }}>
                                                                                {sub.mid_2 || 'Not Yet Conducted'}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                )}

                                                                {/* Lab Internal */}
                                                                {subType === 'lab' && (
                                                                    <div style={{ padding: '0.75rem 1rem', borderRadius: 10, background: '#fff', border: '1px solid #e2e8f0' }}>
                                                                        <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 4 }}>Lab Internal Exam</div>
                                                                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: sub.lab_internal ? '#6366f1' : '#94a3b8' }}>
                                                                            {sub.lab_internal || 'Not Yet Conducted'}
                                                                        </div>
                                                                    </div>
                                                                )}


                                                                {/* NPTEL */}
                                                                {subType === 'nptel' && (
                                                                    <div style={{ padding: '0.75rem 1rem', borderRadius: 10, background: '#fffbeb', border: '1px solid #fcd34d' }}>
                                                                        <div style={{ fontSize: '0.85rem', color: '#92400e' }}>📌 NPTEL course — Evaluated through external NPTEL exam only</div>
                                                                    </div>
                                                                )}



                                                                {/* Assignments - for theory, NPTEL, and non-credit */}
                                                                {(subType === 'theory' || subType === 'nptel' || subType === 'non_credit') && (
                                                                <div style={{ padding: '0.75rem 1rem', borderRadius: 10, background: '#fff', border: '1px solid #e2e8f0' }}>
                                                                    <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8', fontWeight: 600, marginBottom: 6 }}>
                                                                        Assignments ({sub.assignments_submitted || 0}/{sub.assignment_count || 0} submitted)
                                                                    </div>
                                                                    {(sub.assignment_details || []).length > 0 ? (
                                                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                                                            {sub.assignment_details.map((a, ai) => (
                                                                                <div key={ai} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', padding: '0.3rem 0' }}>
                                                                                    <span>{a.title}</span>
                                                                                    <span style={{
                                                                                        padding: '2px 10px', borderRadius: 12, fontSize: '0.7rem', fontWeight: 600,
                                                                                        background: a.status === 'Submitted' ? '#dcfce7' : a.status === 'Missing' ? '#fef2f2' : '#fefce8',
                                                                                        color: a.status === 'Submitted' ? '#166534' : a.status === 'Missing' ? '#991b1b' : '#854d0e'
                                                                                    }}>
                                                                                        {a.status === 'Submitted' ? '✓ Submitted' : a.status === 'Missing' ? '✗ Missing' : '⏳ Pending'}
                                                                                    </span>
                                                                                </div>
                                                                            ))}
                                                                        </div>
                                                                    ) : (
                                                                        <div style={{ color: '#94a3b8', fontSize: '0.82rem' }}>No assignments assigned yet</div>
                                                                    )}
                                                                </div>
                                                                )}

                                                                {/* Attendance detail */}
                                                                <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                                                                    Classes: {sub.classes_attended || 0} attended out of {sub.total_classes || 0}
                                                                </div>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                )}
                                            </React.Fragment>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Previous Academic Records with toggle */}
                    {analytics.semester_stats?.length > 0 && (() => {
                        const sortedStats = [...analytics.semester_stats].sort((a, b) => b.semester - a.semester);
                        const activePrevSem = selectedSem ?? sortedStats[0]?.semester;
                        const activeSemData = sortedStats.find(s => s.semester === activePrevSem);

                        return (
                            <div style={{ marginTop: '2rem' }}>
                                <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
                                    <span>📋</span> Previous Academic Records
                                </h3>
                                <div className="flex gap-2" style={{ overflowX: 'auto', paddingBottom: '1rem' }}>
                                    {sortedStats.map(sem => (
                                        <button
                                            key={sem.semester}
                                            onClick={() => setSelectedSem(sem.semester)}
                                            className={activePrevSem === sem.semester ? 'btn-primary' : 'btn-secondary'}
                                            style={{
                                                whiteSpace: 'nowrap',
                                                borderRadius: '50px',
                                                padding: '0.4rem 1.2rem',
                                                fontSize: '0.85rem',
                                                border: activePrevSem === sem.semester ? 'none' : '1px solid var(--border)'
                                            }}
                                        >
                                            Sem {sem.semester}
                                        </button>
                                    ))}
                                </div>

                                {activeSemData && (
                                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                                        <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--border)', background: '#f8fafc', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Semester {activeSemData.semester}</span>
                                            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.82rem' }}>
                                                <span>Attendance: <strong>{activeSemData.attendance_percentage}%</strong></span>
                                                <span style={{ color: '#6366f1', fontWeight: 700 }}>SGPA: {activeSemData.sgpa}</span>
                                            </div>
                                        </div>
                                        <div style={{ overflowX: 'auto' }}>
                                            <table style={{ margin: 0 }}>
                                                <thead>
                                                    <tr>
                                                        <th style={{ fontSize: '0.75rem' }}>Subject</th>
                                                        <th style={{ fontSize: '0.75rem' }}>Credits</th>
                                                        <th style={{ fontSize: '0.75rem' }}>Attendance</th>
                                                        <th style={{ fontSize: '0.75rem' }}>Grade Point</th>

                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {(activeSemData.subject_stats || []).map((sub, i) => (
                                                        <tr key={i}>
                                                            <td>
                                                                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{sub.subject_name}</div>
                                                                <div className="text-xs text-muted">{sub.subject_code}</div>
                                                            </td>
                                                            <td style={{ fontSize: '0.85rem' }}>{sub.credits}</td>
                                                            <td style={{ fontSize: '0.85rem' }}>
                                                                <span style={{ color: sub.attendance_percentage < 75 ? '#ef4444' : 'inherit', fontWeight: sub.attendance_percentage < 75 ? 600 : 400 }}>
                                                                    {sub.attendance_percentage}%
                                                                </span>
                                                            </td>
                                                            <td style={{ fontWeight: 700, color: '#6366f1', fontSize: '0.85rem' }}>{sub.grade_point}</td>

                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })()}
                </div>

                {/* Duplicate section removed — toggle view above handles this */}


                {/* Charts and Tables removed as requested */}
            </div>
        </>
    );
};

export default StudentDetail;
