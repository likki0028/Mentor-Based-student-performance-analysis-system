import os
import glob

replacements = {
    'StudentDashboard.jsx': [
        ("import api from '../services/api';", "import studentService from '../services/student.service';\nimport analyticsService from '../services/analytics.service';\nimport React, { useEffect, useState, useRef } from 'react';\nimport { useAuth } from '../context/AuthContext';"),
        ("await api.post(`/assignments/upload/${selectedAssignmentId}`, formData, {\n                headers: { 'Content-Type': 'multipart/form-data' }\n            });", "await studentService.uploadAssignment(selectedAssignmentId, formData);")
    ],
    'LecturerDashboard.jsx': [
        ("import api from '../services/api';", "import facultyService from '../services/faculty.service';\nimport analyticsService from '../services/analytics.service';\nimport academicService from '../services/academic.service';\nimport React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';"),
        ("const res = await api.get(`/faculty/my-students?section_id=${secId}&subject_id=${subId}`);", "const res = { data: await facultyService.getMyStudents({ section_id: secId, subject_id: subId }) };")
    ],
    'StudentDetail.jsx': [
        ("import api from '../services/api';", "import React, { useEffect, useState } from 'react';\nimport { useSearchParams, Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';\nimport facultyService from '../services/faculty.service';\nimport analyticsService from '../services/analytics.service';"),
        ("const profileRes = await api.get('/students/me');", "const profileRes = { data: await studentService.getProfile() };"),
        ("api.get(`/analytics/student/${sid}`)", "analyticsService.getStudentAnalytics(sid).then(data => ({ data }))"),
        ("api.get(`/faculty/remarks/${sid}`).catch(() => ({ data: [] }))", "facultyService.getRemarks(sid).then(data => ({ data })).catch(() => ({ data: [] }))"),
        ("await api.post('/faculty/remarks', {\n                student_id: analytics.student_id,\n                message: remarkText\n            });", "await facultyService.addRemark({\n                student_id: analytics.student_id,\n                message: remarkText\n            });"),
        ("const res = await api.get(`/faculty/remarks/${analytics.student_id}`);", "const res = { data: await facultyService.getRemarks(analytics.student_id) };")
    ],
    'SubjectClassroom.jsx': [
        ("import api from '../services/api';", "import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';\nimport analyticsService from '../services/analytics.service';")
    ],
    'FacultyClassroom.jsx': [
        ("import api from '../services/api';", "import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport facultyService from '../services/faculty.service';\nimport academicService from '../services/academic.service';")
    ]
}

pages_dir = r'h:\mini project\vibe\frontend\src\pages'
for file in glob.glob(os.path.join(pages_dir, '*.jsx')):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print(f"Processing {os.path.basename(file)}...")
    
    # Global replacement
    if '<Toaster position="top-right" />' in content:
        content = content.replace('<Toaster position="top-right" />', '')
        print("  - Removed Toaster")
        
    # Extra fix: AdminDashboard has different spacing sometimes, so let's hit it broadly 
    # if it exists with weird spaces.
    content = content.replace('<Toaster position="top-right"/>', '')
    
    # File-specific replacements
    basename = os.path.basename(file)
    if basename in replacements:
        for old_str, new_str in replacements[basename]:
            if old_str in content:
                content = content.replace(old_str, new_str)
                print(f"  - Replaced target in {basename}")
            else:
                pass
                
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print("Fixes applied successfully.")
