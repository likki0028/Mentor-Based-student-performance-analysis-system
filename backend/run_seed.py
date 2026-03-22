import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout.detach())
sys.stderr = codecs.getwriter('utf8')(sys.stderr.detach())

from scripts.seed_data import seed_data
seed_data()
