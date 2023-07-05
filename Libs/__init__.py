from pathlib import Path
import math

ROOT = Path(__file__).parent.parent

BIN_PATH = ROOT / "Bin"
TEMPLATE_PATH = ROOT / "Template" 
HISTORY_PATH = ROOT / "Bin" / "projects.json"

POS_INF = math.inf
NEG_INF = math.inf*(-1)


project_structure_path = BIN_PATH / "project_structure.json"


ALLOWED_DECIMALS = 4
ORDINALS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th']
CHARS = [chr(i) for i in range(65, 65+26)]


FISH_KEY_FORMAT = "Fish {}"
SAVED_TRAJECTORY_FORMAT = "Fish {}.csv"