import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';

const FacultyClassroom = () => {
    const { subjectId, sectionId } = useParams();
    const navigate = useNavigate();
    const [subject, setSubject] = useState(null);
    const [section, setSection] = useState(null);
    const [students, setStudents] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('stream');

    // --- Attendance state ---
    const [attDate, setAttDate] = useState(new Date().toISOString().slice(0, 10));
    const [attStatus, setAttStatus] = useState({});
    const [attSubmitting, setAttSubmitting] = useState(false);
    const [attReport, setAttReport] = useState([]);
    const [attReportLoading, setAttReportLoading] = useState(false);
    const [attAlreadyTaken, setAttAlreadyTaken] = useState(false);
    const [attBlocked, setAttBlocked] = useState(null); // null or reason string
    const [attPeriods, setAttPeriods] = useState([]);  // period numbers for this subject on selected date
    const [attTakenPeriods, setAttTakenPeriods] = useState([]); // periods already marked

    // Festival holidays (YYYY-MM-DD format) — add more as needed
    const festivalHolidays = [
        '2026-01-01', // New Year
        '2026-01-26', // Republic Day
        '2026-03-14', // Holi
        '2026-03-30', // Eid ul-Fitr (approx)
        '2026-04-14', // Ambedkar Jayanti
        '2026-08-15', // Independence Day
        '2026-08-19', // Janmashtami (approx)
        '2026-09-18', // Milad un-Nabi (approx)
        '2026-10-02', // Gandhi Jayanti
        '2026-10-20', // Dussehra (approx)
        '2026-11-10', // Diwali (approx)
        '2026-11-12', // Diwali Holiday
        '2026-12-25', // Christmas
    ];

    const isHoliday = (dateStr) => {
        const d = new Date(dateStr);
        if (d.getDay() === 0) return 'Sunday';
        if (festivalHolidays.includes(dateStr)) return 'Festival Holiday';
        return null;
    };

    // --- Marks state ---
    const marksTypeConfig = {
        mid_1: { label: 'Mid 1', total: 30 },
        mid_2: { label: 'Mid 2', total: 30 },
        assignment: { label: 'Assignment', total: 5 },
        daily_assessment: { label: 'Daily Assessment', total: 5 }
    };
    const [marksType, setMarksType] = useState('mid_1');
    const [marksTotal, setMarksTotal] = useState(30);
    const [marksScores, setMarksScores] = useState({});
    const [marksSubmitting, setMarksSubmitting] = useState(false);
    const [marksOverview, setMarksOverview] = useState([]);
    const [marksOverviewLoading, setMarksOverviewLoading] = useState(false);
    const [asmValidationData, setAsmValidationData] = useState(null); // { assignments: [], submissionsMap: {} }
    const [actualAsmCount, setActualAsmCount] = useState(5); // real assignment count for summary header
    const [showMarksSummary, setShowMarksSummary] = useState(false);

    const handleMarksTypeChange = (type) => {
        setMarksType(type);
        setMarksTotal(marksTypeConfig[type]?.total || 30);
        setMarksScores({});
        if (type === 'assignment') { fetchAsmValidation(); }
        else { setAsmValidationData(null); }
    };

    const fetchAsmValidation = async () => {
        try {
            const asmRes = await api.get(`/assignments?subject_id=${subjectId}&section_id=${sectionId}`);
            const asmList = asmRes.data.sort((a, b) => new Date(a.due_date) - new Date(b.due_date)).slice(0, 5);
            const subsMap = {};
            for (const asm of asmList) {
                const subRes = await api.get(`/assignments/${asm.id}/submissions`);
                subsMap[asm.id] = subRes.data;
            }
            setAsmValidationData({ assignments: asmList, submissionsMap: subsMap });
        } catch {
            setAsmValidationData(null);
        }
    };

    // --- Quiz states ---
    const [quizzes, setQuizzes] = useState([]);
    const [quizLoading, setQuizLoading] = useState(false);
    const [showQuizModal, setShowQuizModal] = useState(false);
    const [quizForm, setQuizForm] = useState({ title: '', start_time: '', end_time: '' });
    const [quizQuestions, setQuizQuestions] = useState([{ question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'a', marks: 1 }]);
    const [quizSubmitting, setQuizSubmitting] = useState(false);
    const [quizRecommendations, setQuizRecommendations] = useState([]);
    const [expandedQuiz, setExpandedQuiz] = useState(null);
    const [quizResults, setQuizResults] = useState({});
    const [quizResultsLoading, setQuizResultsLoading] = useState(false);

    // --- Analytics, Doubts, Syllabus, Finalization states ---
    const [classAnalytics, setClassAnalytics] = useState(null);
    const [analyticsLoading, setAnalyticsLoading] = useState(false);
    const [doubts, setDoubts] = useState([]);
    const [doubtsLoading, setDoubtsLoading] = useState(false);
    const [newComment, setNewComment] = useState({});
    const [syllabusData, setSyllabusData] = useState({ topics: [], total: 0, completed: 0, percentage: 0 });
    const [syllabusLoading, setSyllabusLoading] = useState(false);
    const [newTopicTitle, setNewTopicTitle] = useState('');
    const [finalizationStatus, setFinalizationStatus] = useState([]);  // array of {assessment_type, finalized_at}

    const fetchAnalytics = async () => {
        setAnalyticsLoading(true);
        try {
            const res = await api.get(`/analytics/classroom/${subjectId}/${sectionId}`);
            setClassAnalytics(res.data);
        } catch { setClassAnalytics(null); }
        setAnalyticsLoading(false);
    };

    const fetchDoubts = async () => {
        setDoubtsLoading(true);
        try {
            const res = await api.get(`/doubts/subject/${subjectId}`);
            setDoubts(res.data);
        } catch { setDoubts([]); }
        setDoubtsLoading(false);
    };

    const fetchSyllabus = async () => {
        setSyllabusLoading(true);
        try {
            const res = await api.get(`/syllabus/subject/${subjectId}`);
            setSyllabusData(res.data);
        } catch { setSyllabusData({ topics: [], total: 0, completed: 0, percentage: 0 }); }
        setSyllabusLoading(false);
    };

    const fetchFinalization = async () => {
        try {
            const res = await api.get(`/marks/finalization/${subjectId}/${sectionId}`);
            setFinalizationStatus(res.data || []);
        } catch { setFinalizationStatus([]); }
    };

    const isMarksTypeLocked = (type) => {
        return finalizationStatus.some(f => f.assessment_type === type);
    };

    const fetchQuizzes = async () => {
        setQuizLoading(true);
        try {
            const res = await api.get(`/quizzes/?subject_id=${subjectId}&section_id=${sectionId}`);
            setQuizzes(res.data);
        } catch { setQuizzes([]); }
        setQuizLoading(false);
    };

    const fetchQuizRecommendations = async () => {
        try {
            const res = await api.get(`/quizzes/recommendations/daily?subject_id=${subjectId}`);
            setQuizRecommendations(res.data);
        } catch { setQuizRecommendations([]); }
    };

    const handleCreateQuiz = async (e) => {
        e.preventDefault();
        if (quizQuestions.some(q => !q.question_text.trim())) {
            toast.error('All questions must have text');
            return;
        }
        setQuizSubmitting(true);
        try {
            await api.post('/quizzes/', {
                title: quizForm.title,
                subject_id: parseInt(subjectId),
                section_id: parseInt(sectionId),
                start_time: quizForm.start_time,
                end_time: quizForm.end_time,
                questions: quizQuestions
            });
            toast.success('Quiz created!');
            setShowQuizModal(false);
            setQuizForm({ title: '', start_time: '', end_time: '' });
            setQuizQuestions([{ question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'a', marks: 1 }]);
            fetchQuizzes();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to create quiz');
        }
        setQuizSubmitting(false);
    };

    const handleDeleteQuiz = async (quizId) => {
        if (!window.confirm('Delete this quiz?')) return;
        try {
            await api.delete(`/quizzes/${quizId}`);
            toast.success('Quiz deleted');
            fetchQuizzes();
        } catch {
            toast.error('Failed to delete quiz');
        }
    };

    const addQuestion = () => {
        setQuizQuestions([...quizQuestions, { question_text: '', option_a: '', option_b: '', option_c: '', option_d: '', correct_option: 'a', marks: 1 }]);
    };

    const updateQuestion = (idx, field, value) => {
        const updated = [...quizQuestions];
        updated[idx] = { ...updated[idx], [field]: value };
        setQuizQuestions(updated);
    };

    const removeQuestion = (idx) => {
        if (quizQuestions.length <= 1) return;
        setQuizQuestions(quizQuestions.filter((_, i) => i !== idx));
    };

    const [showAssignModal, setShowAssignModal] = useState(false);
    const [assignForm, setAssignForm] = useState({ title: '', description: '', due_date: '', file: null });
    const [assignSubmitting, setAssignSubmitting] = useState(false);

    const [deleteTarget, setDeleteTarget] = useState(null);
    const [deleteLoading, setDeleteLoading] = useState(false);

    const [showMatModal, setShowMatModal] = useState(false);
    const [matForm, setMatForm] = useState({ title: '', description: '', file: null });
    const [matSubmitting, setMatSubmitting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Fetch basic details
                const [subRes, secRes, studentsRes, assignRes, matRes] = await Promise.all([
                    api.get(`/students/subjects/${subjectId}`),
                    api.get(`/faculty/sections/${sectionId}`),
                    api.get(`/faculty/my-students`, { params: { subject_id: subjectId, section_id: sectionId } }),
                    api.get(`/assignments/?subject_id=${subjectId}&section_id=${sectionId}`),
                    api.get(`/materials/subject/${subjectId}?section_id=${sectionId}`)
                ]);

                setSubject(subRes.data);
                setSection(secRes.data);
                setStudents(studentsRes.data);
                setAssignments(assignRes.data);
                setMaterials(matRes.data);
            } catch (err) {
                console.error('Failed to load classroom data', err);
                toast.error('Failed to load classroom');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [subjectId, sectionId]);

    // --- Attendance handlers ---
    const initAttendance = () => {
        const init = {};
        students.forEach(s => { init[s.id] = true; });
        setAttStatus(init);
    };

    const checkAttendance = async (dateVal, periods) => {
        try {
            const res = await api.get(`/attendance/check?subject_id=${subjectId}&date=${dateVal}`);
            const takenPeriods = res.data.taken_periods || [];
            setAttTakenPeriods(takenPeriods);
            // Check if ALL scheduled periods are taken
            const scheduledPeriods = periods || attPeriods;
            const allTaken = scheduledPeriods.length > 0 && scheduledPeriods.every(p => takenPeriods.includes(p));
            if (allTaken) {
                setAttAlreadyTaken(true);
                const statusMap = {};
                res.data.records.forEach(r => { statusMap[r.student_id] = r.status; });
                setAttStatus(statusMap);
            } else {
                setAttAlreadyTaken(false);
                initAttendance();
            }
        } catch {
            setAttAlreadyTaken(false);
            setAttTakenPeriods([]);
            initAttendance();
        }
    };

    const fetchAttReport = async () => {
        setAttReportLoading(true);
        try {
            const res = await api.get(`/attendance/report?subject_id=${subjectId}`);
            setAttReport(res.data);
        } catch { setAttReport([]); }
        setAttReportLoading(false);
    };

    const handleSubmitAttendance = async () => {
        setAttSubmitting(true);
        try {
            // Create records for each untaken period
            const periodsToMark = attPeriods.filter(p => !attTakenPeriods.includes(p));
            if (periodsToMark.length === 0) {
                toast.error('All periods already marked for this date');
                setAttSubmitting(false);
                return;
            }
            // For each period, create a record per student
            const allRecords = [];
            for (const period of periodsToMark) {
                for (const [sid, status] of Object.entries(attStatus)) {
                    allRecords.push({
                        student_id: parseInt(sid),
                        subject_id: parseInt(subjectId),
                        date: attDate,
                        status,
                        period
                    });
                }
            }
            // Send one batch per period (to pass the per-period duplicate check)
            for (const period of periodsToMark) {
                const periodRecords = allRecords.filter(r => r.period === period);
                await api.post('/attendance/mark', { records: periodRecords });
            }
            toast.success(`Attendance marked for ${periodsToMark.length} period(s) × ${students.length} students = ${allRecords.length} records`);
            setAttAlreadyTaken(true);
            setAttTakenPeriods([...attTakenPeriods, ...periodsToMark]);
        } catch (err) {
            const detail = err.response?.data?.detail || 'Failed to mark attendance';
            toast.error(detail);
        }
        setAttSubmitting(false);
    };

    const handleAttDateChange = async (newDate) => {
        setAttDate(newDate);
        setAttBlocked(null);
        setAttAlreadyTaken(false);
        setAttPeriods([]);
        setAttTakenPeriods([]);

        // Check holiday first
        const holiday = isHoliday(newDate);
        if (holiday) {
            setAttBlocked(holiday);
            setAttStatus({});
            return;
        }

        // Check timetable periods for this subject on this date
        try {
            const res = await api.get(`/attendance/timetable-periods?subject_id=${subjectId}&date=${newDate}`);
            const periods = res.data.periods || [];
            setAttPeriods(periods);

            if (res.data.is_training_day) {
                setAttBlocked('Friday (Training Day)');
                setAttStatus({});
                return;
            }

            if (periods.length === 0) {
                setAttBlocked(`No class scheduled for this subject on ${res.data.day || 'this day'}`);
                setAttStatus({});
                return;
            }

            if (students.length > 0) checkAttendance(newDate, periods);
        } catch {
            // Fallback: just check attendance normally
            setAttPeriods([1]);
            if (students.length > 0) checkAttendance(newDate, [1]);
        }
    };

    // --- Marks handlers ---
    const fetchMarksOverview = async () => {
        setMarksOverviewLoading(true);
        try {
            const allMarks = [];
            for (const s of students) {
                const res = await api.get(`/marks/${s.id}`);
                const subjectMarks = res.data.filter(m => m.subject_id === parseInt(subjectId));
                subjectMarks.forEach(m => allMarks.push({ ...m, student_name: s.name }));
            }

            // Also fetch real assignment submission data to override stale DB values
            try {
                const asmRes = await api.get(`/assignments?subject_id=${subjectId}&section_id=${sectionId}`);
                const asmList = asmRes.data || [];
                if (asmList.length > 0) {
                    const subsMap = {};
                    for (const asm of asmList) {
                        const subRes = await api.get(`/assignments/${asm.id}/submissions`);
                        subsMap[asm.id] = subRes.data;
                    }
                    // Compute real assignment scores per student
                    const realScores = {};
                    for (const s of students) {
                        let valid = 0;
                        for (const asm of asmList) {
                            const subs = subsMap[asm.id] || [];
                            const sub = subs.find(x => x.student_id === s.id);
                            if (sub && sub.validation_status === 'valid') valid++;
                        }
                        realScores[s.id] = { score: valid, total: asmList.length };
                    }
                    // Override assignment marks with real scores
                    const updatedMarks = allMarks.map(m => {
                        if (m.assessment_type === 'assignment' && realScores[m.student_id]) {
                            return { ...m, score: realScores[m.student_id].score, total: realScores[m.student_id].total };
                        }
                        return m;
                    });
                    setMarksOverview(updatedMarks);
                    setActualAsmCount(asmList.length);
                } else {
                    setMarksOverview(allMarks);
                }
            } catch {
                setMarksOverview(allMarks);
            }
        } catch { setMarksOverview([]); }
        setMarksOverviewLoading(false);
    };

    const handleSubmitMarks = async () => {
        if (isMarksTypeLocked(marksType)) {
            toast.error(`${marksTypeConfig[marksType]?.label || marksType} marks are finalized and cannot be modified.`);
            return;
        }
        const entries = Object.entries(marksScores).filter(([, v]) => v !== '' && v !== undefined);
        if (entries.length === 0) { toast.error('Enter at least one score'); return; }
        setMarksSubmitting(true);
        try {
            const marks = entries.map(([sid, score]) => ({
                student_id: parseInt(sid),
                subject_id: parseInt(subjectId),
                assessment_type: marksType,
                score: parseInt(score),
                total: parseInt(marksTotal)
            }));
            const res = await api.post('/marks/', { marks });
            const data = res.data;
            if (data.warning) {
                toast.error(data.warning);
            } else if (data.message && data.message.includes('skipped')) {
                toast(data.message, { icon: '⚠️' });
            } else {
                toast.success(data.message || `Marks saved for ${marks.length} students`);
            }
            setMarksScores({});
            fetchMarksOverview();
            fetchFinalization();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to save marks');
        }
        setMarksSubmitting(false);
    };

    const handleTabChange = (tab) => {
        setActiveTab(tab);
        if (tab === 'attendance') { checkAttendance(attDate); }
        if (tab === 'marks') { fetchMarksOverview(); fetchQuizRecommendations(); fetchFinalization(); }
        if (tab === 'quizzes') { fetchQuizzes(); }
        if (tab === 'analytics') { fetchAnalytics(); }
        if (tab === 'doubts') { fetchDoubts(); }
        if (tab === 'syllabus') { fetchSyllabus(); }
    };

    const handleCreateAssignment = async (e) => {
        e.preventDefault();
        setAssignSubmitting(true);
        try {
            // Step 1: Create assignment with JSON body
            const payload = {
                title: assignForm.title,
                description: assignForm.description,
                due_date: assignForm.due_date,
                subject_id: parseInt(subjectId),
            };
            if (sectionId && sectionId !== 'null' && sectionId !== 'undefined') {
                payload.section_id = parseInt(sectionId);
            }

            const res = await api.post('/assignments/', payload);
            const newAssignment = res.data;

            // Step 2: If file was selected, attach it separately
            if (assignForm.file && newAssignment.id) {
                const fileFormData = new FormData();
                fileFormData.append('file', assignForm.file);
                await api.post(`/assignments/${newAssignment.id}/attach-file`, fileFormData);
                // Re-fetch to get updated file_url
                const updated = await api.get(`/assignments/${newAssignment.id}`);
                setAssignments([updated.data, ...assignments]);
            } else {
                setAssignments([newAssignment, ...assignments]);
            }

            setShowAssignModal(false);
            setAssignForm({ title: '', description: '', due_date: '', file: null });
            toast.success('Assignment created');
        } catch (err) {
            console.error('Assignment creation error:', err.response?.data || err);
            let errMsg = 'Failed to create assignment';
            if (err.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    errMsg = err.response.data.detail.map(e => e.msg).join(', ');
                } else {
                    errMsg = err.response.data.detail;
                }
            }
            toast.error(errMsg);
        } finally {
            setAssignSubmitting(false);
        }
    };

    const handleAddMaterial = async (e) => {
        e.preventDefault();
        if (!matForm.file) {
            toast.error("Please select a file");
            return;
        }
        setMatSubmitting(true);
        try {
            const formData = new FormData();
            formData.append('title', matForm.title);
            if (matForm.description) formData.append('description', matForm.description);
            formData.append('subject_id', subjectId);
            if (sectionId && sectionId !== 'null' && sectionId !== 'undefined') {
                formData.append('section_id', sectionId);
            }
            formData.append('file', matForm.file);

            const res = await api.post('/materials/', formData);
            setMaterials([res.data, ...materials]);
            setShowMatModal(false);
            setMatForm({ title: '', description: '', file: null });
            toast.success('Material added');
        } catch (err) {
            console.error('Material addition error:', err.response?.data || err);
            let errMsg = 'Failed to add material';
            if (err.response?.data?.detail) {
                if (Array.isArray(err.response.data.detail)) {
                    errMsg = err.response.data.detail.map(e => e.msg).join(', ');
                } else {
                    errMsg = err.response.data.detail;
                }
            }
            toast.error(errMsg);
        } finally {
            setMatSubmitting(false);
        }
    };

    const handleDeleteAssignment = async () => {
        if (!deleteTarget) return;
        setDeleteLoading(true);
        try {
            await api.delete(`/assignments/${deleteTarget.id}`);
            setAssignments(assignments.filter(a => a.id !== deleteTarget.id));
            toast.success('Assignment deleted');
            setDeleteTarget(null);
        } catch (err) {
            toast.error('Failed to delete assignment');
        } finally {
            setDeleteLoading(false);
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="skeleton" style={{ height: 200, borderRadius: 8, marginBottom: '2rem' }}></div>
                    <div className="skeleton" style={{ height: 400 }}></div>
                </div>
            </>
        );
    }

    if (!subject) return <div className="text-center py-20"><h2>Classroom not found</h2></div>;

    return (
        <>
            <Navbar />
            <div className="container page-enter" style={{ maxWidth: 1000, position: 'relative' }}>
                {/* Banner */}
                <div className="classroom-banner" style={{
                    background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                    padding: '2.5rem',
                    borderRadius: '12px',
                    color: 'white',
                    marginBottom: '1.5rem',
                    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                }}>
                    <h1 style={{ color: 'white', fontSize: '2.5rem', marginBottom: '0.25rem' }}>{subject.name}</h1>
                    <div className="flex items-center gap-2" style={{ opacity: 0.9, fontSize: '1.1rem' }}>
                        <span>{subject.code}</span>
                        <span>•</span>
                        <span>{section?.name || 'Section'}</span>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex" style={{ gap: '2rem', borderBottom: '1px solid var(--border)', marginBottom: '2rem', padding: '0 1rem' }}>
                    {['stream', 'classwork', 'attendance', 'marks', 'quizzes', 'analytics', 'doubts', 'syllabus', 'people'].map(tab => (
                        <button key={tab} 
                            onClick={() => handleTabChange(tab)}
                            style={{
                                background: 'none',
                                border: 'none',
                                color: activeTab === tab ? 'var(--primary)' : 'var(--text-muted)',
                                padding: '1rem 0',
                                fontSize: '0.95rem',
                                fontWeight: 600,
                                borderRadius: 0,
                                borderBottom: activeTab === tab ? '3px solid var(--primary)' : '3px solid transparent',
                                boxShadow: 'none'
                            }}>
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Content Area */}
                <div className="classroom-content">
                    {activeTab === 'stream' && (
                        <div className="grid" style={{ gridTemplateColumns: '220px 1fr', gap: '1.5rem' }}>
                            <div className="card" style={{ padding: '1.25rem' }}>
                                <p style={{ fontWeight: 700, fontSize: '0.9rem', marginBottom: '0.75rem' }}>Quick Stats</p>
                                <div className="flex flex-col gap-2 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-muted">Students:</span>
                                        <span className="font-bold">{students.length}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-muted">Assignments:</span>
                                        <span className="font-bold">{assignments.length}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col gap-4">
                                <div className="card text-muted text-sm p-4 border-dashed" style={{ border: '2px dashed var(--border)', background: 'transparent' }}>
                                    Announcements feature coming soon...
                                </div>
                                
                                {assignments.map(asm => (
                                    <div key={asm.id} className="card flex items-center gap-4 p-4 hover-lift cursor-pointer" onClick={() => navigate(`/lecturer/assignment/${asm.id}`)}>
                                        <div style={{ padding: '0.75rem', background: 'var(--primary-light)', borderRadius: '50%', color: 'var(--primary)' }}>📝</div>
                                        <div className="flex-1">
                                            <p className="font-bold">{asm.title}</p>
                                            <p className="text-xs text-muted">Due {new Date(asm.due_date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</p>
                                        </div>
                                        <span className="text-xs" style={{ color: 'var(--primary)', fontWeight: 600 }}>View →</span>
                                    </div>
                                ))}
                                
                                {materials.map(mat => (
                                    <div key={mat.id} className="card flex items-center gap-4 p-4 hover-lift cursor-pointer" onClick={() => navigate(`/lecturer/material/${mat.id}`)}>
                                        <div style={{ padding: '0.75rem', background: 'var(--success-light)', borderRadius: '50%', color: 'var(--success)' }}>📁</div>
                                        <div className="flex-1">
                                            <p className="font-bold">{mat.title}</p>
                                            <p className="text-xs text-muted">{mat.description || 'Posted recently'}</p>
                                        </div>
                                        <span className="text-xs" style={{ color: 'var(--success)', fontWeight: 600 }}>View →</span>
                                    </div>
                                ))}

                                {assignments.length === 0 && materials.length === 0 && (
                                    <div className="text-center py-10 text-muted">
                                        <p>No posts yet. Go to Classwork to share materials.</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'classwork' && (
                        <div className="flex flex-col gap-8">
                            <div className="flex gap-3">
                                <button className="btn-primary" style={{ borderRadius: '24px', padding: '0.6rem 1.5rem' }} onClick={() => setShowAssignModal(true)}>
                                    + Create Assignment
                                </button>
                                <button className="btn-success" style={{ borderRadius: '24px', padding: '0.6rem 1.5rem' }} onClick={() => setShowMatModal(true)}>
                                    + Add Material
                                </button>
                            </div>

                            <section>
                                <h3 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>Assignments</h3>
                                <div className="flex flex-col gap-3">
                                    {assignments.map(a => (
                                        <div key={a.id} className="card flex justify-between items-center p-4 hover-lift cursor-pointer" onClick={() => navigate(`/lecturer/assignment/${a.id}`)}>
                                            <div className="flex items-center gap-3">
                                                <span>📄</span>
                                                <span className="font-semibold">{a.title}</span>
                                            </div>
                                            <div className="flex items-center gap-3">
                                                <span className="text-xs text-muted">Due: {new Date(a.due_date).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</span>
                                                <button className="btn-danger" style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem' }} onClick={(e) => { e.stopPropagation(); setDeleteTarget(a); }}>🗑️</button>
                                            </div>
                                        </div>
                                    ))}
                                    {assignments.length === 0 && <p className="text-muted text-sm">No assignments yet.</p>}
                                </div>
                            </section>

                            <section>
                                <h3 style={{ borderBottom: '1px solid var(--border)', paddingBottom: '0.5rem', marginBottom: '1rem' }}>Materials</h3>
                                <div className="grid grid-2 gap-4">
                                    {materials.map(m => (
                                        <div key={m.id} className="card flex items-center gap-3 p-4 hover-lift cursor-pointer" onClick={() => navigate(`/lecturer/material/${m.id}`)}>
                                            <span>📚</span>
                                            <span className="font-semibold flex-1">{m.title}</span>
                                            <span className="text-xs" style={{ color: 'var(--success)', fontWeight: 600 }}>View →</span>
                                        </div>
                                    ))}
                                    {materials.length === 0 && <p className="text-muted text-sm">No materials shared yet.</p>}
                                </div>
                            </section>
                        </div>
                    )}

                    {activeTab === 'people' && (
                        <div className="flex flex-col gap-10">
                            <section>
                                <h2 style={{ color: 'var(--primary)', borderBottom: '1px solid var(--primary)', paddingBottom: '0.5rem' }}>
                                    Teachers
                                </h2>
                                <div className="flex items-center gap-4 py-4 border-b border-gray-100">
                                    <div style={{ width: 40, height: 40, background: 'var(--primary)', borderRadius: '50%', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                                        {subject.name.charAt(0)}
                                    </div>
                                    <p className="font-semibold">Teaching Staff</p>
                                </div>
                            </section>

                            <section>
                                <div className="flex justify-between items-center" style={{ borderBottom: '1px solid var(--primary)', paddingBottom: '0.5rem' }}>
                                    <h2 style={{ color: 'var(--primary)', margin: 0 }}>Students</h2>
                                    <span className="text-muted font-bold">{students.length} students</span>
                                </div>
                                <div className="student-list" style={{ marginTop: '1rem' }}>
                                    {students.map(s => (
                                        <div key={s.id} className="flex items-center gap-4 py-3 border-b" style={{ borderColor: 'var(--border-light)' }}>
                                            <div style={{ width: 36, height: 36, background: 'var(--secondary-light)', borderRadius: '50%', color: 'var(--secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.8rem', fontWeight: 800 }}>
                                                {s.name.charAt(0)}
                                            </div>
                                            <div className="flex-1">
                                                <p className="font-semibold text-sm" style={{ margin: 0 }}>{s.name}</p>
                                                <p className="text-xs text-muted" style={{ margin: 0 }}>{s.enrollment_number}</p>
                                            </div>
                                            <div className="flex gap-3">
                                                <span className={`badge ${s.risk_status === 'Safe' ? 'badge-safe' : s.risk_status === 'Warning' ? 'badge-warning' : 'badge-danger'}`} style={{ fontSize: '0.7rem' }}>
                                                    {s.risk_status}
                                                </span>
                                                <Link to={`/student/detail?id=${s.id}`} style={{ fontSize: '0.7rem', fontWeight: 700 }}>View Profile →</Link>
                                            </div>
                                        </div>
                                    ))}
                                    {students.length === 0 && <p className="text-center py-10 text-muted">No students enrolled in this section.</p>}
                                </div>
                            </section>
                        </div>
                    )}

                    {/* ===== ATTENDANCE TAB ===== */}
                    {activeTab === 'attendance' && (
                        <div className="flex flex-col gap-6">
                            {/* Mark Attendance Card */}
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h2 style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '1.15rem' }}>📋 Mark Attendance</h2>
                                <div className="flex items-center gap-4" style={{ marginBottom: '1.25rem' }}>
                                    <label className="font-semibold text-sm">Date:</label>
                                    <input type="date" value={attDate} max={new Date().toISOString().slice(0, 10)}
                                        onChange={e => handleAttDateChange(e.target.value)}
                                        style={{ padding: '0.4rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.9rem' }} />
                                    {!attAlreadyTaken && !attBlocked && (
                                        <button className="btn-primary" onClick={handleSubmitAttendance} disabled={attSubmitting || students.length === 0}
                                            style={{ marginLeft: 'auto', fontSize: '0.85rem' }}>
                                            {attSubmitting ? 'Saving...' : '✅ Submit Attendance'}
                                        </button>
                                    )}
                                </div>

                                {/* Period Info Badge */}
                                {attPeriods.length > 0 && !attBlocked && (
                                    <div style={{ padding: '0.6rem 1rem', borderRadius: '8px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span>🕐</span>
                                        <span className="text-sm font-semibold" style={{ color: '#6366f1' }}>
                                            {attPeriods.length} period{attPeriods.length > 1 ? 's' : ''}: {attPeriods.map(p => `P${p}`).join(', ')}
                                        </span>
                                        {(() => {
                                            const relevantTaken = attTakenPeriods.filter(p => attPeriods.includes(p));
                                            if (relevantTaken.length > 0 && relevantTaken.length < attPeriods.length) {
                                                return (
                                                    <span className="text-xs" style={{ color: '#f59e0b', fontWeight: 600, marginLeft: 8 }}>
                                                        ({relevantTaken.map(p => `P${p}`).join(', ')} already marked)
                                                    </span>
                                                );
                                            }
                                            return null;
                                        })()}
                                    </div>
                                )}

                                {attBlocked && (
                                    <div style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span>🚫</span>
                                        <span className="text-sm font-semibold" style={{ color: '#dc2626' }}>{attBlocked}</span>
                                    </div>
                                )}

                                {attAlreadyTaken && (
                                    <div style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.3)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span>🔒</span>
                                        <span className="text-sm font-semibold" style={{ color: '#b45309' }}>
                                            Attendance already taken for all {attPeriods.length} period{attPeriods.length > 1 ? 's' : ''} ({attPeriods.map(p => `P${p}`).join(', ')}) on this date. Records are locked.
                                        </span>
                                    </div>
                                )}

                                {students.length === 0 ? (
                                    <p className="text-muted text-center" style={{ padding: '2rem' }}>No students enrolled.</p>
                                ) : (
                                    <div style={{ overflowX: 'auto' }}>
                                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                            <thead>
                                                <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                                    <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>#</th>
                                                    <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Student</th>
                                                    <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Enrollment</th>
                                                    <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {students.map((s, idx) => (
                                                    <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                        <td style={{ padding: '0.6rem 1rem', fontSize: '0.85rem' }}>{idx + 1}</td>
                                                        <td style={{ padding: '0.6rem 1rem' }}>
                                                            <span className="font-semibold text-sm">{s.name}</span>
                                                        </td>
                                                        <td style={{ padding: '0.6rem 1rem' }}>
                                                            <span className="text-xs text-muted">{s.enrollment_number}</span>
                                                        </td>
                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                                                            <div className="flex justify-center gap-2">
                                                                <button
                                                                    onClick={() => setAttStatus({ ...attStatus, [s.id]: true })}
                                                                    disabled={attAlreadyTaken}
                                                                    style={{
                                                                        padding: '0.35rem 1rem', borderRadius: '6px', border: 'none', cursor: attAlreadyTaken ? 'not-allowed' : 'pointer', fontWeight: 700, fontSize: '0.8rem',
                                                                        background: attStatus[s.id] === true ? '#22c55e' : 'var(--bg-secondary)',
                                                                        color: attStatus[s.id] === true ? 'white' : 'var(--text-muted)',
                                                                        opacity: attAlreadyTaken ? 0.7 : 1
                                                                    }}>Present</button>
                                                                <button
                                                                    onClick={() => setAttStatus({ ...attStatus, [s.id]: false })}
                                                                    disabled={attAlreadyTaken}
                                                                    style={{
                                                                        padding: '0.35rem 1rem', borderRadius: '6px', border: 'none', cursor: attAlreadyTaken ? 'not-allowed' : 'pointer', fontWeight: 700, fontSize: '0.8rem',
                                                                        background: attStatus[s.id] === false ? '#ef4444' : 'var(--bg-secondary)',
                                                                        color: attStatus[s.id] === false ? 'white' : 'var(--text-muted)',
                                                                        opacity: attAlreadyTaken ? 0.7 : 1
                                                                    }}>Absent</button>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* ===== MARKS TAB ===== */}
                    {activeTab === 'marks' && (
                        <div className="flex flex-col gap-6">
                            {/* Marks Breakdown Info */}
                            <div className="card" style={{ padding: '1rem 1.5rem', background: 'var(--primary-light)' }}>
                                <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 600, color: 'var(--primary)' }}>
                                    📊 Internal Marks (40) = Avg of Mid 1 & Mid 2 (30) + Assignment (5) + Daily Assessment (5)
                                </p>
                                <p className="text-xs text-muted" style={{ margin: '0.25rem 0 0' }}>External exam marks are managed by the college separately.</p>
                            </div>

                            {/* Export & Finalize Buttons */}
                            <div className="flex items-center gap-3">
                                <button className="btn-secondary" style={{ fontSize: '0.8rem' }}
                                    onClick={async () => {
                                        try {
                                            const res = await api.get(`/exports/marks/subject/${subjectId}/section/${sectionId}`, { responseType: 'blob' });
                                            const url = window.URL.createObjectURL(new Blob([res.data]));
                                            const a = document.createElement('a'); a.href = url; a.download = `marks_export.csv`; a.click();
                                        } catch { toast.error('Export failed'); }
                                    }}>
                                    📥 Export Marks CSV
                                </button>
                                <button className="btn-secondary" style={{ fontSize: '0.8rem' }}
                                    onClick={async () => {
                                        try {
                                            const res = await api.get(`/exports/attendance/subject/${subjectId}/section/${sectionId}`, { responseType: 'blob' });
                                            const url = window.URL.createObjectURL(new Blob([res.data]));
                                            const a = document.createElement('a'); a.href = url; a.download = `attendance_export.csv`; a.click();
                                        } catch { toast.error('Export failed'); }
                                    }}>
                                    📥 Export Attendance CSV
                                </button>
                                {finalizationStatus.length > 0 && (
                                    <span className="badge" style={{ background: 'rgba(34,197,94,0.15)', color: '#16a34a', fontSize: '0.75rem', fontWeight: 700, marginLeft: 'auto' }}>
                                        {finalizationStatus.map(f => `${marksTypeConfig[f.assessment_type]?.label || f.assessment_type}`).join(', ')} locked
                                    </span>
                                )}
                            </div>

                            {/* Collapsible Marks Summary */}
                            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                                <button
                                    onClick={() => setShowMarksSummary(!showMarksSummary)}
                                    style={{
                                        width: '100%', padding: '1rem 1.5rem', background: 'none', border: 'none',
                                        cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                        fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-primary)', textAlign: 'left'
                                    }}
                                >
                                    <span>📊 Marks Summary</span>
                                    <span style={{ fontSize: '0.9rem', transition: 'transform 0.2s', transform: showMarksSummary ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
                                </button>
                                {showMarksSummary && (
                                    <div style={{ padding: '0 1.5rem 1.5rem' }}>
                                        {marksOverviewLoading ? (
                                            <p className="text-muted">Loading marks...</p>
                                        ) : marksOverview.length === 0 ? (
                                            <p className="text-muted text-center" style={{ padding: '2rem' }}>No marks recorded yet for this subject.</p>
                                        ) : (() => {
                                            const studentMap = {};
                                            marksOverview.forEach(m => {
                                                if (!studentMap[m.student_name]) studentMap[m.student_name] = {};
                                                studentMap[m.student_name][m.assessment_type] = m.score;
                                            });
                                            return (
                                                <div style={{ overflowX: 'auto' }}>
                                                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                        <thead>
                                                            <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                                                <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Student</th>
                                                                <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Mid 1<br/><span style={{fontWeight:400}}>/30</span></th>
                                                                <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Mid 2<br/><span style={{fontWeight:400}}>/30</span></th>
                                                                <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Assign<br/><span style={{fontWeight:400}}>/{actualAsmCount}</span></th>
                                                                <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Daily<br/><span style={{fontWeight:400}}>/5</span></th>
                                                                <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--primary)', fontWeight: 800 }}>Internal<br/><span style={{fontWeight:400}}>/40</span></th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {Object.entries(studentMap).map(([name, marks], i) => {
                                                                const mid1 = marks['mid_1'] ?? null;
                                                                const mid2 = marks['mid_2'] ?? null;
                                                                const assign = marks['assignment'] ?? 0;
                                                                const daily = marks['daily_assessment'] ?? 0;
                                                                let midAvg = null;
                                                                if (mid1 !== null && mid2 !== null) midAvg = (mid1 + mid2) / 2;
                                                                else if (mid1 !== null) midAvg = mid1;
                                                                else if (mid2 !== null) midAvg = mid2;
                                                                const internal = midAvg !== null ? Math.round(midAvg + assign + daily) : null;
                                                                return (
                                                                    <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                                                        <td style={{ padding: '0.6rem 1rem' }} className="font-semibold text-sm">{name}</td>
                                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>{mid1 !== null ? mid1 : '—'}</td>
                                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>{mid2 !== null ? mid2 : '—'}</td>
                                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>{assign}</td>
                                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>{daily}</td>
                                                                        <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                                                                            {internal !== null ? (
                                                                                <span className={`badge ${internal >= 16 ? 'badge-safe' : 'badge-danger'}`} style={{ fontSize: '0.8rem', fontWeight: 800 }}>
                                                                                    {internal}
                                                                                </span>
                                                                            ) : '—'}
                                                                        </td>
                                                                    </tr>
                                                                );
                                                            })}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            );
                                        })()}
                                    </div>
                                )}
                            </div>

                            {/* Enter Marks Card */}
                            <div className="card" style={{ padding: '1.5rem' }}>
                                <h2 style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '1.15rem' }}>📝 Enter Marks</h2>
                                <div className="flex items-center gap-4" style={{ marginBottom: '1.25rem', flexWrap: 'wrap' }}>
                                    <div className="flex items-center gap-2">
                                        <label className="font-semibold text-sm">Assessment:</label>
                                        <select value={marksType} onChange={e => handleMarksTypeChange(e.target.value)}
                                            style={{ padding: '0.4rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.85rem' }}>
                                            <option value="mid_1">Mid 1 (out of 30) {isMarksTypeLocked('mid_1') ? '🔒' : ''}</option>
                                            <option value="mid_2">Mid 2 (out of 30) {isMarksTypeLocked('mid_2') ? '🔒' : ''}</option>
                                            <option value="assignment">Assignment (out of 5) {isMarksTypeLocked('assignment') ? '🔒' : ''}</option>
                                            <option value="daily_assessment">Daily Assessment (out of 5) {isMarksTypeLocked('daily_assessment') ? '🔒' : ''}</option>
                                        </select>
                                    </div>
                                    {marksType !== 'assignment' && (
                                        <>
                                            <div className="flex items-center gap-2">
                                                <label className="font-semibold text-sm">Total:</label>
                                                <span className="badge" style={{ fontSize: '0.85rem', background: 'var(--bg-secondary)', padding: '0.4rem 0.75rem' }}>{marksTotal}</span>
                                            </div>
                                            <button className="btn-primary" onClick={handleSubmitMarks} disabled={marksSubmitting || students.length === 0 || isMarksTypeLocked(marksType)}
                                                style={{ marginLeft: 'auto', fontSize: '0.85rem', opacity: isMarksTypeLocked(marksType) ? 0.5 : 1 }}>
                                                {isMarksTypeLocked(marksType) ? '🔒 Locked' : marksSubmitting ? 'Saving...' : 'Submit Marks'}
                                            </button>
                                        </>
                                    )}
                                </div>

                                {isMarksTypeLocked(marksType) && (
                                    <div style={{ padding: '0.75rem 1rem', borderRadius: '8px', background: 'rgba(234,179,8,0.12)', border: '1px solid rgba(234,179,8,0.3)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '1.1rem' }}>🔒</span>
                                        <span className="text-sm font-semibold" style={{ color: '#b45309' }}>
                                            {marksTypeConfig[marksType]?.label || marksType} marks have been finalized and cannot be modified. All entries for this assessment type are locked.
                                        </span>
                                    </div>
                                )}

                                {marksType === 'assignment' ? (
                                    /* === Assignment Validation View === */
                                    !asmValidationData ? (
                                        <p className="text-muted text-center" style={{ padding: '2rem' }}>Loading assignment data...</p>
                                    ) : asmValidationData.assignments.length === 0 ? (
                                        <p className="text-muted text-center" style={{ padding: '2rem' }}>No assignments created yet for this subject.</p>
                                    ) : (
                                        <div style={{ overflowX: 'auto' }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Student</th>
                                                        {asmValidationData.assignments.map((asm, i) => (
                                                            <th key={i} style={{ textAlign: 'center', padding: '0.75rem 0.5rem', fontSize: '0.7rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                                                                <span title={asm.title}>A{i+1}</span>
                                                            </th>
                                                        ))}
                                                        <th style={{ textAlign: 'center', padding: '0.75rem 0.5rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--primary)', fontWeight: 800 }}>Total<br/><span style={{fontWeight:400}}>/{asmValidationData.assignments.length}</span></th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {students.map((s, idx) => {
                                                        let totalValid = 0;
                                                        const cells = asmValidationData.assignments.map((asm, i) => {
                                                            const subs = asmValidationData.submissionsMap[asm.id] || [];
                                                            const studentSub = subs.find(sub => sub.student_id === s.id);
                                                            if (!studentSub) {
                                                                return <td key={i} style={{ textAlign: 'center', padding: '0.5rem', fontSize: '0.7rem', color: 'var(--text-muted)' }}>⏳ Not Submitted</td>;
                                                            }
                                                            if (studentSub.validation_status === 'valid') {
                                                                totalValid++;
                                                                return <td key={i} style={{ textAlign: 'center', padding: '0.5rem' }}><span className="badge badge-safe" style={{ fontSize: '0.7rem' }}>✅ 1</span></td>;
                                                            }
                                                            if (studentSub.validation_status === 'invalid') {
                                                                return <td key={i} style={{ textAlign: 'center', padding: '0.5rem' }}><span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>❌ 0</span></td>;
                                                            }
                                                            return <td key={i} style={{ textAlign: 'center', padding: '0.5rem' }}><span className="badge" style={{ fontSize: '0.7rem', background: 'rgba(234,179,8,0.15)', color: '#b45309' }}>⏳ Pending</span></td>;
                                                        });
                                                        return (
                                                            <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                                <td style={{ padding: '0.6rem 1rem' }}>
                                                                    <span className="font-semibold text-sm">{s.name}</span>
                                                                    <br/><span className="text-xs text-muted">{s.enrollment_number}</span>
                                                                </td>
                                                                {cells}
                                                                <td style={{ textAlign: 'center', padding: '0.5rem' }}>
                                                                    <span className="badge" style={{ fontSize: '0.8rem', fontWeight: 800, background: 'var(--primary-light)', color: 'var(--primary)' }}>{totalValid}</span>
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    )
                                ) : (
                                    /* === Normal Score Input for Mid/Daily === */
                                    students.length === 0 ? (
                                        <p className="text-muted text-center" style={{ padding: '2rem' }}>No students enrolled.</p>
                                    ) : (
                                        <div style={{ overflowX: 'auto' }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>#</th>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Student</th>
                                                        <th style={{ textAlign: 'left', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Enrollment</th>
                                                        {marksType === 'daily_assessment' && (
                                                            <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: '#b45309' }}>Recommended</th>
                                                        )}
                                                        <th style={{ textAlign: 'center', padding: '0.75rem 1rem', fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Score / {marksTotal}</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {students.map((s, idx) => {
                                                        const rec = marksType === 'daily_assessment'
                                                            ? quizRecommendations.find(r => r.student_id === s.id)
                                                            : null;
                                                        return (
                                                            <tr key={s.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                                <td style={{ padding: '0.6rem 1rem', fontSize: '0.85rem' }}>{idx + 1}</td>
                                                                <td style={{ padding: '0.6rem 1rem' }}>
                                                                    <span className="font-semibold text-sm">{s.name}</span>
                                                                </td>
                                                                <td style={{ padding: '0.6rem 1rem' }}>
                                                                    <span className="text-xs text-muted">{s.enrollment_number}</span>
                                                                </td>
                                                                {marksType === 'daily_assessment' && (
                                                                    <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                                                                        {rec ? (
                                                                            <span
                                                                                className="badge"
                                                                                onClick={() => setMarksScores({ ...marksScores, [s.id]: String(rec.recommended_marks) })}
                                                                                title={`Based on ${rec.quizzes_taken}/${rec.total_quizzes} quizzes. Click to auto-fill.`}
                                                                                style={{
                                                                                    fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
                                                                                    background: 'rgba(234,179,8,0.15)', color: '#b45309'
                                                                                }}
                                                                            >
                                                                                {rec.recommended_marks}
                                                                            </span>
                                                                        ) : (
                                                                            <span className="text-xs text-muted">—</span>
                                                                        )}
                                                                    </td>
                                                                )}
                                                                <td style={{ padding: '0.6rem 1rem', textAlign: 'center' }}>
                                                                    <input type="number" min="0" max={marksTotal}
                                                                        value={marksScores[s.id] ?? ''}
                                                                        onChange={e => setMarksScores({ ...marksScores, [s.id]: e.target.value })}
                                                                        placeholder="—"
                                                                        style={{ width: '70px', padding: '0.35rem 0.5rem', borderRadius: '6px', border: '1px solid var(--border)', textAlign: 'center', fontSize: '0.9rem' }} />
                                                                </td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                            </table>
                                        </div>
                                    )
                                )}
                            </div>

                        </div>
                    )}

                    {/* ===== QUIZZES TAB ===== */}
                    {activeTab === 'quizzes' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
                                <h2 style={{ margin: 0, fontSize: '1.2rem' }}>🧠 Quizzes</h2>
                                <button className="btn-primary" onClick={() => setShowQuizModal(true)} style={{ fontSize: '0.85rem' }}>+ Create Quiz</button>
                            </div>

                            {quizLoading ? (
                                <p className="text-muted">Loading quizzes...</p>
                            ) : quizzes.length === 0 ? (
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>🧠</div>
                                    <p className="text-muted">No quizzes created yet.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {quizzes.map(q => {
                                        const statusColors = { active: { bg: 'rgba(34,197,94,0.15)', color: '#16a34a', label: '🟢 Active' }, upcoming: { bg: 'rgba(59,130,246,0.15)', color: '#2563eb', label: '🔵 Upcoming' }, ended: { bg: 'rgba(156,163,175,0.15)', color: '#6b7280', label: '⚫ Ended' } };
                                        const sc = statusColors[q.status] || statusColors.upcoming;
                                        const isExpanded = expandedQuiz === q.id;
                                        const results = quizResults[q.id] || [];
                                        return (
                                            <div key={q.id} className="card" style={{ padding: '1.25rem 1.5rem' }}>
                                                <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                                    <div>
                                                        <h3 style={{ margin: 0, fontSize: '1.05rem' }}>{q.title}</h3>
                                                        <p className="text-xs text-muted" style={{ margin: '0.25rem 0 0' }}>{q.question_count} question{q.question_count !== 1 ? 's' : ''} · {q.total_marks} marks</p>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="badge" style={{ background: sc.bg, color: sc.color, fontSize: '0.7rem', fontWeight: 700 }}>{sc.label}</span>
                                                        <button onClick={() => handleDeleteQuiz(q.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem', opacity: 0.5 }}>🗑️</button>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                                                    <span>📅 Start: {q.start_time ? new Date(q.start_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—'}</span>
                                                    <span>📅 End: {q.end_time ? new Date(q.end_time).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—'}</span>
                                                </div>

                                                {/* View Results Toggle */}
                                                <button
                                                    onClick={async () => {
                                                        if (isExpanded) {
                                                            setExpandedQuiz(null);
                                                        } else {
                                                            setExpandedQuiz(q.id);
                                                            if (!quizResults[q.id]) {
                                                                setQuizResultsLoading(true);
                                                                try {
                                                                    const res = await api.get(`/quizzes/${q.id}/results`);
                                                                    setQuizResults(prev => ({ ...prev, [q.id]: res.data }));
                                                                } catch { toast.error('Failed to load results'); }
                                                                setQuizResultsLoading(false);
                                                            }
                                                        }
                                                    }}
                                                    style={{
                                                        background: 'none', border: '1px solid var(--border)', borderRadius: '8px',
                                                        padding: '0.4rem 1rem', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                                                        color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '0.4rem'
                                                    }}
                                                >
                                                    📊 {isExpanded ? 'Hide Results' : 'View Results'}
                                                    <span style={{ fontSize: '0.7rem' }}>{isExpanded ? '▲' : '▼'}</span>
                                                </button>

                                                {/* Results Table */}
                                                {isExpanded && (
                                                    <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
                                                        {quizResultsLoading && !quizResults[q.id] ? (
                                                            <p className="text-muted text-sm">Loading results...</p>
                                                        ) : results.length === 0 ? (
                                                            <div className="text-center" style={{ padding: '1.5rem' }}>
                                                                <div style={{ fontSize: '2rem', opacity: 0.3, marginBottom: '0.25rem' }}>📭</div>
                                                                <p className="text-muted text-sm">No submissions yet.</p>
                                                            </div>
                                                        ) : (
                                                            <>
                                                                <div className="flex items-center gap-4" style={{ marginBottom: '0.75rem' }}>
                                                                    <span className="text-sm font-semibold">📋 {results.length} Submission{results.length !== 1 ? 's' : ''}</span>
                                                                    <span className="text-xs text-muted">Avg: {(results.reduce((s, r) => s + r.percentage, 0) / results.length).toFixed(1)}%</span>
                                                                </div>
                                                                <div style={{ overflowX: 'auto' }}>
                                                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                                                                        <thead>
                                                                            <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left' }}>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>#</th>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Student</th>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Enrollment</th>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', textAlign: 'center' }}>Score</th>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', textAlign: 'center' }}>Percentage</th>
                                                                                <th style={{ padding: '0.6rem 0.75rem', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Submitted</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody>
                                                                            {results.map((r, i) => (
                                                                                <tr key={r.attempt_id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                                                    <td style={{ padding: '0.6rem 0.75rem', color: 'var(--text-muted)' }}>{i + 1}</td>
                                                                                    <td style={{ padding: '0.6rem 0.75rem' }}>
                                                                                        <div className="flex items-center gap-2">
                                                                                            <div style={{
                                                                                                width: 28, height: 28, borderRadius: '50%',
                                                                                                background: 'var(--primary-light)', color: 'var(--primary)',
                                                                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                                                                fontWeight: 700, fontSize: '0.7rem'
                                                                                            }}>{(r.student_name || '?').charAt(0).toUpperCase()}</div>
                                                                                            <span className="font-semibold">{r.student_name}</span>
                                                                                        </div>
                                                                                    </td>
                                                                                    <td style={{ padding: '0.6rem 0.75rem' }} className="text-muted">{r.enrollment_number}</td>
                                                                                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center', fontWeight: 700 }}>{r.marks_obtained}/{r.total_marks}</td>
                                                                                    <td style={{ padding: '0.6rem 0.75rem', textAlign: 'center' }}>
                                                                                        <span className={`badge ${r.percentage >= 60 ? 'badge-safe' : r.percentage >= 40 ? 'badge-warning' : 'badge-danger'}`} style={{ fontSize: '0.75rem', fontWeight: 700 }}>
                                                                                            {r.percentage}%
                                                                                        </span>
                                                                                    </td>
                                                                                    <td style={{ padding: '0.6rem 0.75rem' }} className="text-xs text-muted">
                                                                                        {r.submitted_at ? new Date(r.submitted_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                                                                                    </td>
                                                                                </tr>
                                                                            ))}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            </>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ===== ANALYTICS TAB ===== */}
                    {activeTab === 'analytics' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>📊 Classroom Analytics</h2>
                            {analyticsLoading ? (
                                <p className="text-muted">Loading analytics...</p>
                            ) : !classAnalytics ? (
                                <p className="text-muted">No data available yet.</p>
                            ) : (
                                <>
                                    {/* Stats row */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                                        <div className="card" style={{ padding: '1.25rem', textAlign: 'center' }}>
                                            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)' }}>{classAnalytics.student_count}</div>
                                            <p className="text-xs text-muted">Total Students</p>
                                        </div>
                                        <div className="card" style={{ padding: '1.25rem', textAlign: 'center' }}>
                                            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#16a34a' }}>{classAnalytics.quiz_performance?.length || 0}</div>
                                            <p className="text-xs text-muted">Quizzes Conducted</p>
                                        </div>
                                        <div className="card" style={{ padding: '1.25rem', textAlign: 'center' }}>
                                            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ef4444' }}>{classAnalytics.at_risk?.length || 0}</div>
                                            <p className="text-xs text-muted">At-Risk Students</p>
                                        </div>
                                    </div>

                                    {/* Charts row */}
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                                        {/* Attendance Chart */}
                                        <div className="card" style={{ padding: '1.5rem' }}>
                                            <h3 style={{ margin: '0 0 1rem', fontSize: '0.95rem' }}>📋 Attendance Distribution</h3>
                                            <ResponsiveContainer width="100%" height={220}>
                                                <BarChart data={classAnalytics.attendance_chart}>
                                                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                                                    <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                                                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                                                    <Tooltip />
                                                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                                        {classAnalytics.attendance_chart?.map((entry, i) => (
                                                            <Cell key={i} fill={['#22c55e','#3b82f6','#f59e0b','#ef4444'][i]} />
                                                        ))}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>

                                        {/* Quiz Performance Chart */}
                                        <div className="card" style={{ padding: '1.5rem' }}>
                                            <h3 style={{ margin: '0 0 1rem', fontSize: '0.95rem' }}>🧠 Quiz Averages</h3>
                                            {classAnalytics.quiz_performance?.length > 0 ? (
                                                <ResponsiveContainer width="100%" height={220}>
                                                    <BarChart data={classAnalytics.quiz_performance}>
                                                        <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                                                        <XAxis dataKey="quiz_title" tick={{ fontSize: 10 }} />
                                                        <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                                                        <Tooltip formatter={(v) => `${v}%`} />
                                                        <Bar dataKey="avg_percentage" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                                                    </BarChart>
                                                </ResponsiveContainer>
                                            ) : (
                                                <p className="text-muted text-center" style={{ padding: '3rem 0' }}>No quizzes yet</p>
                                            )}
                                        </div>
                                    </div>

                                    {/* At-risk students */}
                                    <div className="card" style={{ padding: '1.5rem' }}>
                                        <h3 style={{ margin: '0 0 1rem', fontSize: '0.95rem', color: '#ef4444' }}>⚠️ At-Risk Students</h3>
                                        {classAnalytics.at_risk?.length === 0 ? (
                                            <p className="text-muted text-center" style={{ padding: '1.5rem' }}>🎉 No at-risk students — great job!</p>
                                        ) : (
                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ borderBottom: '2px solid var(--border)' }}>
                                                        <th style={{ textAlign: 'left', padding: '0.5rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Student</th>
                                                        <th style={{ textAlign: 'center', padding: '0.5rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Attendance</th>
                                                        <th style={{ textAlign: 'center', padding: '0.5rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Quiz Avg</th>
                                                        <th style={{ textAlign: 'left', padding: '0.5rem 1rem', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Reasons</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {classAnalytics.at_risk?.map(s => (
                                                        <tr key={s.student_id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                            <td style={{ padding: '0.6rem 1rem' }}>
                                                                <span className="font-semibold text-sm">{s.name}</span>
                                                                <br /><span className="text-xs text-muted">{s.enrollment}</span>
                                                            </td>
                                                            <td style={{ textAlign: 'center', padding: '0.5rem' }}>
                                                                <span className="badge" style={{ background: s.attendance_pct < 75 ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)', color: s.attendance_pct < 75 ? '#ef4444' : '#16a34a', fontSize: '0.75rem' }}>{s.attendance_pct}%</span>
                                                            </td>
                                                            <td style={{ textAlign: 'center', padding: '0.5rem' }}>
                                                                <span className="badge" style={{ background: s.quiz_avg_pct < 50 ? 'rgba(239,68,68,0.15)' : 'rgba(34,197,94,0.15)', color: s.quiz_avg_pct < 50 ? '#ef4444' : '#16a34a', fontSize: '0.75rem' }}>{s.quiz_avg_pct}%</span>
                                                            </td>
                                                            <td style={{ padding: '0.5rem 1rem' }}>
                                                                {s.reasons?.map((r, i) => (
                                                                    <span key={i} className="badge" style={{ background: 'rgba(239,68,68,0.1)', color: '#b91c1c', fontSize: '0.65rem', marginRight: '0.3rem' }}>{r}</span>
                                                                ))}
                                                            </td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        )}
                                    </div>
                                </>
                            )}
                        </div>
                    )}

                    {/* ===== DOUBTS TAB ===== */}
                    {activeTab === 'doubts' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>💬 Discussion Forum</h2>
                            {doubtsLoading ? (
                                <p className="text-muted">Loading...</p>
                            ) : doubts.length === 0 ? (
                                <div className="card text-center" style={{ padding: '3rem' }}>
                                    <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>💬</div>
                                    <p className="text-muted">No doubts posted yet.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {doubts.map(d => (
                                        <div key={d.id} className="card" style={{ padding: '1.25rem 1.5rem', borderLeft: d.is_pinned ? '4px solid var(--primary)' : d.is_resolved ? '4px solid #22c55e' : '4px solid var(--border)' }}>
                                            <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                <div>
                                                    <h3 style={{ margin: 0, fontSize: '1rem' }}>
                                                        {d.is_pinned && <span title="Pinned">📌 </span>}
                                                        {d.title}
                                                    </h3>
                                                    <p className="text-xs text-muted" style={{ margin: '0.15rem 0 0' }}>by {d.student_name} · {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <button onClick={async () => { await api.patch(`/doubts/${d.id}/pin`); fetchDoubts(); }}
                                                        title={d.is_pinned ? 'Unpin' : 'Pin'}
                                                        style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.85rem', opacity: 0.6 }}>
                                                        {d.is_pinned ? '📌' : '📍'}
                                                    </button>
                                                    <button onClick={async () => { await api.patch(`/doubts/${d.id}/resolve`); fetchDoubts(); }}
                                                        className="badge"
                                                        style={{ cursor: 'pointer', fontSize: '0.7rem', fontWeight: 700, background: d.is_resolved ? 'rgba(34,197,94,0.15)' : 'rgba(239,68,68,0.15)', color: d.is_resolved ? '#16a34a' : '#ef4444', border: 'none' }}>
                                                        {d.is_resolved ? '✅ Resolved' : '❌ Unresolved'}
                                                    </button>
                                                </div>
                                            </div>
                                            <p className="text-sm" style={{ margin: '0.5rem 0', lineHeight: 1.6 }}>{d.content}</p>

                                            {/* Comments */}
                                            {d.comments?.length > 0 && (
                                                <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
                                                    {d.comments.map(c => (
                                                        <div key={c.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                                            <div className="flex items-center gap-2" style={{ marginBottom: '0.2rem' }}>
                                                                <span className="font-semibold text-xs">{c.user_name}</span>
                                                                <span className="badge" style={{ fontSize: '0.55rem', padding: '0.1rem 0.4rem', background: c.user_role === 'lecturer' || c.user_role === 'both' ? 'rgba(59,130,246,0.15)' : 'rgba(156,163,175,0.15)', color: c.user_role === 'lecturer' || c.user_role === 'both' ? '#2563eb' : '#6b7280' }}>
                                                                    {c.user_role === 'lecturer' || c.user_role === 'both' ? 'Faculty' : 'Student'}
                                                                </span>
                                                                <span className="text-xs text-muted">{c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</span>
                                                            </div>
                                                            <p className="text-sm" style={{ margin: 0 }}>{c.content}</p>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}

                                            {/* Add comment */}
                                            <div className="flex items-center gap-2" style={{ marginTop: '0.75rem' }}>
                                                <input
                                                    type="text"
                                                    value={newComment[d.id] || ''}
                                                    onChange={e => setNewComment({ ...newComment, [d.id]: e.target.value })}
                                                    placeholder="Reply..."
                                                    style={{ flex: 1, padding: '0.4rem 0.75rem', fontSize: '0.85rem', borderRadius: '6px', border: '1px solid var(--border)' }}
                                                />
                                                <button
                                                    className="btn-primary"
                                                    style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}
                                                    onClick={async () => {
                                                        if (!newComment[d.id]?.trim()) return;
                                                        try {
                                                            await api.post(`/doubts/${d.id}/comments`, { content: newComment[d.id] });
                                                            setNewComment({ ...newComment, [d.id]: '' });
                                                            fetchDoubts();
                                                        } catch { toast.error('Failed to add comment'); }
                                                    }}
                                                >Reply</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* ===== SYLLABUS TAB ===== */}
                    {activeTab === 'syllabus' && (
                        <div className="flex flex-col gap-6">
                            <h2 style={{ margin: 0, fontSize: '1.2rem' }}>📚 Syllabus Progress</h2>

                            {/* Progress bar */}
                            <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
                                <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                    <span className="font-semibold text-sm">Course Progress</span>
                                    <span className="font-semibold" style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>{syllabusData.percentage}%</span>
                                </div>
                                <div style={{ background: 'var(--bg-secondary)', borderRadius: '8px', height: '12px', overflow: 'hidden' }}>
                                    <div style={{ width: `${syllabusData.percentage}%`, height: '100%', background: 'var(--gradient-primary)', borderRadius: '8px', transition: 'width 0.4s ease' }} />
                                </div>
                                <p className="text-xs text-muted" style={{ marginTop: '0.5rem' }}>{syllabusData.completed} of {syllabusData.total} topics completed</p>
                            </div>

                            {/* Add topic */}
                            <div className="flex items-center gap-2">
                                <input
                                    type="text"
                                    value={newTopicTitle}
                                    onChange={e => setNewTopicTitle(e.target.value)}
                                    placeholder="Add a new topic..."
                                    onKeyDown={async (e) => {
                                        if (e.key === 'Enter' && newTopicTitle.trim()) {
                                            try {
                                                await api.post('/syllabus/', { title: newTopicTitle, subject_id: parseInt(subjectId) });
                                                setNewTopicTitle('');
                                                fetchSyllabus();
                                            } catch { toast.error('Failed to add topic'); }
                                        }
                                    }}
                                    style={{ flex: 1, padding: '0.6rem 1rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.9rem' }}
                                />
                                <button className="btn-primary" style={{ fontSize: '0.85rem' }} onClick={async () => {
                                    if (!newTopicTitle.trim()) return;
                                    try {
                                        await api.post('/syllabus/', { title: newTopicTitle, subject_id: parseInt(subjectId) });
                                        setNewTopicTitle('');
                                        fetchSyllabus();
                                    } catch { toast.error('Failed to add topic'); }
                                }}>+ Add</button>
                            </div>

                            {/* Topic list */}
                            {syllabusLoading ? (
                                <p className="text-muted">Loading...</p>
                            ) : syllabusData.topics.length === 0 ? (
                                <div className="card text-center" style={{ padding: '2rem' }}>
                                    <p className="text-muted">No topics added yet. Start adding your syllabus above.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-2">
                                    {syllabusData.topics.map((t, idx) => (
                                        <div key={t.id} className="card flex items-center" style={{ padding: '0.75rem 1rem', gap: '0.75rem' }}>
                                            <input
                                                type="checkbox"
                                                checked={t.is_completed}
                                                onChange={async () => {
                                                    try {
                                                        await api.patch(`/syllabus/${t.id}/toggle`);
                                                        fetchSyllabus();
                                                    } catch { toast.error('Failed to toggle'); }
                                                }}
                                                style={{ width: 18, height: 18, cursor: 'pointer' }}
                                            />
                                            <span className="flex-1 text-sm" style={{ textDecoration: t.is_completed ? 'line-through' : 'none', opacity: t.is_completed ? 0.6 : 1 }}>
                                                <span className="text-xs text-muted" style={{ marginRight: '0.5rem' }}>{idx + 1}.</span>
                                                {t.title}
                                            </span>
                                            <button onClick={async () => {
                                                if (!window.confirm('Delete this topic?')) return;
                                                try { await api.delete(`/syllabus/${t.id}`); fetchSyllabus(); } catch { toast.error('Failed'); }
                                            }} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.85rem', opacity: 0.4 }}>🗑️</button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* Modals */}
            {showAssignModal && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '500px', padding: '2rem' }}>
                        <h2 style={{ marginTop: 0 }}>Create Assignment</h2>
                        <form onSubmit={handleCreateAssignment} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1">Title</label>
                                <input className="w-full" type="text" required value={assignForm.title} onChange={e => setAssignForm({...assignForm, title: e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Description</label>
                                <textarea className="w-full" required rows="3" value={assignForm.description} onChange={e => setAssignForm({...assignForm, description: e.target.value})}></textarea>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Due Date & Time</label>
                                <input className="w-full" type="datetime-local" required value={assignForm.due_date} onChange={e => setAssignForm({...assignForm, due_date: e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Attach File (Optional)</label>
                                <input className="w-full" type="file" accept=".pdf,.doc,.docx,.ppt,.pptx" onChange={e => setAssignForm({...assignForm, file: e.target.files[0]})} />
                            </div>
                            <div className="flex justify-end gap-3 mt-4">
                                <button type="button" className="btn-secondary" onClick={() => setShowAssignModal(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={assignSubmitting}>
                                    {assignSubmitting ? 'Creating...' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {showMatModal && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '500px', padding: '2rem' }}>
                        <h2 style={{ marginTop: 0 }}>Add Material</h2>
                        <form onSubmit={handleAddMaterial} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1">Title</label>
                                <input className="w-full" type="text" required value={matForm.title} onChange={e => setMatForm({...matForm, title: e.target.value})} />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Description (Optional)</label>
                                <textarea className="w-full" rows="2" value={matForm.description} onChange={e => setMatForm({...matForm, description: e.target.value})}></textarea>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">File Upload</label>
                                <input className="w-full" type="file" required accept=".pdf,.doc,.docx,.ppt,.pptx" onChange={e => setMatForm({...matForm, file: e.target.files[0]})} />
                            </div>
                            <div className="flex justify-end gap-3 mt-4">
                                <button type="button" className="btn-secondary" onClick={() => setShowMatModal(false)}>Cancel</button>
                                <button type="submit" className="btn-success" disabled={matSubmitting}>
                                    {matSubmitting ? 'Uploading...' : 'Upload'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {deleteTarget && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '420px', padding: '2rem', textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🗑️</div>
                        <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Delete Assignment?</h2>
                        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                            Are you sure you want to delete <strong>"{deleteTarget.title}"</strong>? All student submissions will also be deleted. This cannot be undone.
                        </p>
                        <div className="flex justify-center gap-3">
                            <button className="btn-secondary" onClick={() => setDeleteTarget(null)} disabled={deleteLoading}>Cancel</button>
                            <button className="btn-danger" onClick={handleDeleteAssignment} disabled={deleteLoading}>
                                {deleteLoading ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
            {/* Quiz Creation Modal */}
            {showQuizModal && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '650px', padding: '2rem', maxHeight: '85vh', overflowY: 'auto' }}>
                        <h2 style={{ marginTop: 0 }}>🧠 Create Quiz</h2>
                        <form onSubmit={handleCreateQuiz} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1">Quiz Title</label>
                                <input className="w-full" type="text" required value={quizForm.title}
                                    onChange={e => setQuizForm({...quizForm, title: e.target.value})} placeholder="e.g. Unit 1 Quiz" />
                            </div>
                            <div className="flex gap-4">
                                <div style={{ flex: 1 }}>
                                    <label className="block text-sm font-semibold mb-1">Start Date & Time</label>
                                    <input className="w-full" type="datetime-local" required value={quizForm.start_time}
                                        onChange={e => setQuizForm({...quizForm, start_time: e.target.value})} />
                                </div>
                                <div style={{ flex: 1 }}>
                                    <label className="block text-sm font-semibold mb-1">End Date & Time</label>
                                    <input className="w-full" type="datetime-local" required value={quizForm.end_time}
                                        onChange={e => setQuizForm({...quizForm, end_time: e.target.value})} />
                                </div>
                            </div>

                            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
                                <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '1rem' }}>
                                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Questions ({quizQuestions.length})</h3>
                                    <button type="button" className="btn-secondary" onClick={addQuestion} style={{ fontSize: '0.8rem' }}>+ Add Question</button>
                                </div>

                                {quizQuestions.map((q, idx) => (
                                    <div key={idx} className="card" style={{ padding: '1rem', marginBottom: '1rem', background: 'var(--bg-secondary)' }}>
                                        <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                                            <span className="font-semibold text-sm">Q{idx + 1}</span>
                                            {quizQuestions.length > 1 && (
                                                <button type="button" onClick={() => removeQuestion(idx)}
                                                    style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.8rem' }}>✕ Remove</button>
                                            )}
                                        </div>
                                        <input className="w-full" type="text" required placeholder="Question text"
                                            value={q.question_text} onChange={e => updateQuestion(idx, 'question_text', e.target.value)}
                                            style={{ marginBottom: '0.5rem' }} />
                                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                            <input type="text" required placeholder="Option A" value={q.option_a} onChange={e => updateQuestion(idx, 'option_a', e.target.value)} />
                                            <input type="text" required placeholder="Option B" value={q.option_b} onChange={e => updateQuestion(idx, 'option_b', e.target.value)} />
                                            <input type="text" required placeholder="Option C" value={q.option_c} onChange={e => updateQuestion(idx, 'option_c', e.target.value)} />
                                            <input type="text" required placeholder="Option D" value={q.option_d} onChange={e => updateQuestion(idx, 'option_d', e.target.value)} />
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="flex items-center gap-2">
                                                <label className="text-xs font-semibold">Correct:</label>
                                                <select value={q.correct_option} onChange={e => updateQuestion(idx, 'correct_option', e.target.value)}
                                                    style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }}>
                                                    <option value="a">A</option>
                                                    <option value="b">B</option>
                                                    <option value="c">C</option>
                                                    <option value="d">D</option>
                                                </select>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <label className="text-xs font-semibold">Marks:</label>
                                                <input type="number" min="1" max="10" value={q.marks}
                                                    onChange={e => updateQuestion(idx, 'marks', parseInt(e.target.value) || 1)}
                                                    style={{ width: '50px', padding: '0.25rem 0.4rem', fontSize: '0.8rem', textAlign: 'center' }} />
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="flex justify-end gap-3">
                                <button type="button" className="btn-secondary" onClick={() => setShowQuizModal(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={quizSubmitting}>
                                    {quizSubmitting ? 'Creating...' : '🧠 Create Quiz'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </>
    );
};

export default FacultyClassroom;
