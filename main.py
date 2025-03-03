import requests
import sqlite3
import time
import json
from bs4 import BeautifulSoup

def extract_data(reg_no):
    """
    Fetch and parse the result page for a given registration number,
    extracting key data using BeautifulSoup (targeting specific element IDs).
    Returns a dictionary of the extracted data, or None if extraction fails.
    """
    url = f"https://results.beup.ac.in/ResultsBTech1stSem2023_B2023Pub.aspx?Sem=I&RegNo={reg_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        print(f"Error fetching {reg_no}: {e}")
        return None

    if response.status_code != 200:
        print(f"Error for {reg_no}: Status code {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Check for the existence of key element (Registration No span) to confirm valid result page
    reg_span = soup.find("span", id="ContentPlaceHolder1_DataList1_RegistrationNoLabel_0")
    if not reg_span:
        print(f"No content found for {reg_no}")
        return None

    data = {}
    # --- Student Information ---
    data["Registration_No"] = reg_span.get_text(strip=True)
    
    student_name = soup.find("span", id="ContentPlaceHolder1_DataList1_StudentNameLabel_0")
    data["Student_Name"] = student_name.get_text(strip=True) if student_name else None

    father_name = soup.find("span", id="ContentPlaceHolder1_DataList1_FatherNameLabel_0")
    data["Father_Name"] = father_name.get_text(strip=True) if father_name else None

    mother_name = soup.find("span", id="ContentPlaceHolder1_DataList1_MotherNameLabel_0")
    data["Mother_Name"] = mother_name.get_text(strip=True) if mother_name else None

    college_name = soup.find("span", id="ContentPlaceHolder1_DataList1_CollegeNameLabel_0")
    data["College_Name"] = college_name.get_text(strip=True) if college_name else None

    course_name = soup.find("span", id="ContentPlaceHolder1_DataList1_CourseLabel_0")
    data["Course_Name"] = course_name.get_text(strip=True) if course_name else None

    # --- Exam Details (Semester and Examination Month/Year) ---
    exam_details = {}
    exam_table = soup.find("table", id="ContentPlaceHolder1_DataList2")
    if exam_table:
        tds = exam_table.find_all("td")
        for td in tds:
            text = td.get_text(strip=True)
            if "Semester" in text:
                exam_details["Semester"] = text.split(":", 1)[-1].strip()
            elif "Examination(Month/Year)" in text:
                exam_details["Exam_Month_Year"] = text.split(":", 1)[-1].strip()
    data["Exam_Details"] = exam_details

    # --- THEORY Marks ---
    theory_data = []
    theory_table = soup.find("table", id="ContentPlaceHolder1_GridView1")
    if theory_table:
        rows = theory_table.find_all("tr")
        if len(rows) > 1:
            headers_list = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
            for row in rows[1:]:
                cells = row.find_all("td")
                if cells:
                    values = [cell.get_text(strip=True) for cell in cells]
                    theory_data.append(dict(zip(headers_list, values)))
    data["THEORY_Marks"] = theory_data

    # --- PRACTICAL Marks ---
    practical_data = []
    practical_table = soup.find("table", id="ContentPlaceHolder1_GridView2")
    if practical_table:
        rows = practical_table.find_all("tr")
        if len(rows) > 1:
            headers_list = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
            for row in rows[1:]:
                cells = row.find_all("td")
                if cells:
                    values = [cell.get_text(strip=True) for cell in cells]
                    practical_data.append(dict(zip(headers_list, values)))
    data["PRACTICAL_Marks"] = practical_data

    # --- SGPA ---
    sgpa_span = soup.find("span", id="ContentPlaceHolder1_DataList5_GROSSTHEORYTOTALLabel_0")
    data["SGPA"] = sgpa_span.get_text(strip=True) if sgpa_span else None

    # --- Semester-wise Results ---
    sem_wise = {}
    sem_table = soup.find("table", id="ContentPlaceHolder1_GridView3")
    if sem_table:
        rows = sem_table.find_all("tr")
        if len(rows) > 1:
            headers_list = [cell.get_text(strip=True) for cell in rows[0].find_all("th")]
            values = [cell.get_text(strip=True) for cell in rows[1].find_all("td")]
            sem_wise = dict(zip(headers_list, values))
    data["Semester_wise_Results"] = sem_wise

    # --- Remarks and Publish Date ---
    remarks = ""
    publish_date = ""
    remarks_table = soup.find("table", id="ContentPlaceHolder1_DataList3")
    if remarks_table:
        remark_span = remarks_table.find("span", id="ContentPlaceHolder1_DataList3_remarkLabel_0")
        if remark_span:
            remarks = remark_span.get_text(strip=True)
        for td in remarks_table.find_all("td"):
            text = td.get_text(strip=True)
            if "Publish Date" in text:
                publish_date = text.split(":", 1)[-1].strip()
    data["Remarks"] = remarks
    data["Publish_Date"] = publish_date

    # --- Notes ---
    notes = []
    notes_ul = soup.find("ul", id="ContentPlaceHolder1_BulletedList1")
    if notes_ul:
        for li in notes_ul.find_all("li"):
            notes.append(li.get_text(strip=True))
    data["Notes"] = notes

    return data

# --- Setup SQLite Database ---
conn = sqlite3.connect("results.db")
cursor = conn.cursor()

# Drop the existing table if it exists (to ensure the correct schema)
cursor.execute("DROP TABLE IF EXISTS results")
conn.commit()

cursor.execute("""
CREATE TABLE results (
    registration_no TEXT PRIMARY KEY,
    student_name TEXT,
    father_name TEXT,
    mother_name TEXT,
    college_name TEXT,
    course_name TEXT,
    semester TEXT,
    exam_month_year TEXT,
    sgpa REAL,
    publish_date TEXT,
    theory_marks TEXT,       -- Stored as JSON string
    practical_marks TEXT,    -- Stored as JSON string
    sem_wise_results TEXT,   -- Stored as JSON string
    remarks TEXT,
    notes TEXT               -- Stored as JSON string
)
""")
conn.commit()

# --- Loop through registration numbers and save data in the database ---
for i in range(1, 56):
    reg_no = f"23106107{str(i).zfill(3)}"
    print(f"Processing reg no: {reg_no}")
    data = extract_data(reg_no)
    if data:
        registration_no = data.get("Registration_No")
        student_name = data.get("Student_Name")
        father_name = data.get("Father_Name")
        mother_name = data.get("Mother_Name")
        college_name = data.get("College_Name")
        course_name = data.get("Course_Name")
        exam_details = data.get("Exam_Details", {})
        semester = exam_details.get("Semester")
        exam_month_year = exam_details.get("Exam_Month_Year")
        try:
            sgpa = float(data.get("SGPA")) if data.get("SGPA") else None
        except:
            sgpa = None
        publish_date = data.get("Publish_Date")
        theory_marks_json = json.dumps(data.get("THEORY_Marks"))
        practical_marks_json = json.dumps(data.get("PRACTICAL_Marks"))
        sem_wise_results_json = json.dumps(data.get("Semester_wise_Results"))
        remarks = data.get("Remarks")
        notes_json = json.dumps(data.get("Notes"))
        
        try:
            cursor.execute("""
                INSERT INTO results (
                    registration_no, student_name, father_name, mother_name,
                    college_name, course_name, semester, exam_month_year, sgpa,
                    publish_date, theory_marks, practical_marks, sem_wise_results,
                    remarks, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                registration_no, student_name, father_name, mother_name,
                college_name, course_name, semester, exam_month_year, sgpa,
                publish_date, theory_marks_json, practical_marks_json,
                sem_wise_results_json, remarks, notes_json
            ))
            conn.commit()
            print(f"Saved data for reg no: {reg_no}")
        except Exception as e:
            print(f"Error saving data for {reg_no}: {e}")
    else:
        print(f"Data extraction failed for reg no: {reg_no}")
    
    # Pause between requests to be polite to the server
    time.sleep(1)

conn.close()
print("All records processed and saved to the database.")
