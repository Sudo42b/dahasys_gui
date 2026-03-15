import sqlite3

conn = sqlite3.connect("minias.db")
cursor = conn.cursor()
cursor.execute("DELETE FROM TEST_RESULTS;")
cursor.execute("DELETE FROM TEST_AXIS_RESULTS;")
cursor.execute("DELETE FROM TEST_SAMPLES;")
cursor.execute("DELETE FROM MEASURES;")
# Do not clear CODES, OPERATORS, SETUP, LIMITS
conn.commit()
conn.close()
print("Cleared test results from DB.")
