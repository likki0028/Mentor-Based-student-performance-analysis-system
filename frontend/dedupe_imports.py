import os
import glob

# The lines we accidentally injected unnecessarily because they already existed
bad_lines = [
    "import React, { useEffect, useState, useRef } from 'react';\n",
    "import { useAuth } from '../context/AuthContext';\n",
    "import React, { useEffect, useState } from 'react';\n",
    "import { useSearchParams, Link } from 'react-router-dom';\n",
    "import { useParams } from 'react-router-dom';\n"
]

pages_dir = r'h:\mini project\vibe\frontend\src\pages'

def try_remove_duplicates(lines):
    seen = set()
    new_lines = []
    
    # Simple rule: if it's an import React or useAuth, and we've already seen it, drop it.
    for line in lines:
        is_import = line.strip().startswith('import React') or line.strip().startswith('import { useAuth }') or line.strip().startswith('import { useSearchParams') or line.strip().startswith('import { useParams')
        
        # also handle case where "from 'react'" varies slightly
        if line.strip().startswith('import React'):
            key = 'import React'
        elif line.strip().startswith('import { useAuth }'):
            key = 'import useAuth'
        elif line.strip().startswith('import { useSearchParams'):
            key = 'import useSearchParams'
        elif line.strip().startswith('import { useParams'):
            key = 'import useParams'
        else:
            key = line
            
        if is_import:
            if key in seen:
                # Duplicate! Skip it
                # Wait, if there's "import React, {useState} from 'react'" and then "import React, {useState, useRef} from 'react'", we MUST keep the one with useRef.
                # So we shouldn't just drop the second one. We should actually replace them both with a merged one, or just do manual string replacements.
                pass
                
    # Better approach: Just do explicit replacements for the exact blocks my previous script injected!
    return None

import re
for file in glob.glob(os.path.join(pages_dir, '*.jsx')):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    original = content
        
    # StudentDashboard
    content = content.replace("import React, { useEffect, useState } from 'react';\nimport { Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';\nimport analyticsService from '../services/analytics.service';\nimport React, { useEffect, useState, useRef } from 'react';\nimport { useAuth } from '../context/AuthContext';", 
                              "import React, { useEffect, useState, useRef } from 'react';\nimport { Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';\nimport analyticsService from '../services/analytics.service';")
    
    # LecturerDashboard
    content = content.replace("import React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';\nimport facultyService from '../services/faculty.service';\nimport analyticsService from '../services/analytics.service';\nimport academicService from '../services/academic.service';\nimport React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';",
                              "import React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';\nimport facultyService from '../services/faculty.service';\nimport analyticsService from '../services/analytics.service';\nimport academicService from '../services/academic.service';")
                              
    # StudentDetail
    content = content.replace("import React, { useEffect, useState } from 'react';\nimport { useSearchParams, Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport React, { useEffect, useState } from 'react';\nimport { useSearchParams, Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';",
                              "import React, { useEffect, useState } from 'react';\nimport { useSearchParams, Link } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';")
                              
    # SubjectClassroom
    content = content.replace("import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';",
                              "import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport { useAuth } from '../context/AuthContext';\nimport studentService from '../services/student.service';")
                              
    # FacultyClassroom
    content = content.replace("import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport facultyService from '../services/faculty.service';\nimport academicService from '../services/academic.service';\nimport React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport facultyService from '../services/faculty.service';",
                              "import React, { useEffect, useState, useRef } from 'react';\nimport { useParams } from 'react-router-dom';\nimport facultyService from '../services/faculty.service';\nimport academicService from '../services/academic.service';")
                              
    # AdminDashboard
    content = content.replace("import React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';\nimport React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';\nimport authService from '../services/auth.service';",
                              "import React, { useEffect, useState } from 'react';\nimport { useAuth } from '../context/AuthContext';\nimport authService from '../services/auth.service';")
                              
    if original != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Deduped imports for {os.path.basename(file)}")

print("Deduplication complete.")
