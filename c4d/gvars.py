from os.path import join
from pipeline.c4d import status

#JSON_DB_PATH = "Y:\\Workspace\\SCRIPTS\\pipeline\\database"
JSON_DB_PATH = "V:\\dev\\pipeline\\c4d"
status.warning("Database is pathed locally. SETTINGS ARE NOT GLOBAL.")
PRODUCTION_DB= join(JSON_DB_PATH, "productions_db.json")
#PRESETS_PATH = "Y:\\Workspace\\SCRIPTS\\pipeline\\c4d\\presets" 
PRESETS_PATH = "preset://espn.lib4d/{0}/{1}"
