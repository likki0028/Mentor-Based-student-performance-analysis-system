import os
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
sys.stderr = codecs.getwriter('utf8')(sys.stderr.detach())
os.environ["DATABASE_URL"] = "postgresql://neondb_owner:npg_5BixMZNfKFO6@ep-muddy-base-a15u2npb-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Import ALL models FIRST to ensure configure_mappers works
from app.models import user, student, faculty, subject, section  # noqa
from app.models import remark, material, marks, attendance  # noqa
from app.models import assignment, submission, alert, quiz, quiz_attempt, quiz_question, quiz_response, assignment_file, material_file  # noqa
from app.models import doubt, doubt_comment, syllabus_topic, mark_finalization  # noqa
from app.models import notification  # noqa

# Now run seed
from scripts.seed_data import seed_data
seed_data()
