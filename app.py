# ============================================Modules needed============================================================
from flask import Flask, render_template, request, redirect, flash, url_for, session, jsonify
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from MySQLdb.cursors import DictCursor
import os
from datetime import datetime, timedelta
# ================================== Connection to Flask app and Data base =============================================

app = Flask(__name__)
app.secret_key = "secret_key_here"

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Alcove@123'
app.config['MYSQL_DB'] = 'fms_hr_recruitment_annex1'

app.config['PROFILE_PHOTO_FOLDER'] = 'static/uploads/profile_photos'

mysql = MySQL(app)

# ================================= HR Recruitment Whitelisted Employees =================================
WORKFLOW_POWERS = {
    "P1": {"role": "HR_MANAGER", "action": "approve"},
    "P2": {"role": "HR_EXECUTIVE", "action": "groupd"},
    "P3": {"role": "HR_EXECUTIVE", "action": "approve"},
    "P4": {"role": "HR_EXECUTIVE", "action": "approve"},
    "P5": {"role": "HR_EXECUTIVE", "action": "approve"},
    "P6": {"role": "HOD", "action": "shortlist"},
    "P7": {"role": "HR_EXECUTIVE", "action": "approve"},
    "P8": {"role": "HOD", "action": "candidate"},
    "P9": {"role": "HR_MANAGER", "action": "approve_loi"},
    "P10": {"role": "HR_EXECUTIVE", "action": "send_it"},
    "P11": {"role": "SITE_HR", "action": "approve_cv"},
    "P12": {"role": "SITE_HR", "action": "interview_done"},
    "P13": {"role": "HOD", "action": "final_approve"},
    "P14": {"role": "SITE_HR", "action": "salary_confirm"}
}

WORKFLOW_HELP = {

"P1":{
"who":"HR Manager",
"time":"4 Hours",
"how":"Approve recruitment request in portal"
},

"P2":{
"who":"HR Executive",
"time":"2 Hours",
"how":"Check if job belongs to Group-D"
},

"P3":{
"who":"HR Executive",
"time":"2 Hours",
"how":"Confirm JD with HOD using AI sheet"
},

"P4":{
"who":"HR Executive",
"time":"2 Days",
"how":"Receive CV via email"
},

"P5":{
"who":"HR Executive",
"time":"2 Hours",
"how":"Send CV to HOD"
},

"P6":{
"who":"HOD",
"time":"1 Day",
"how":"Shortlist CV"
},

"P7":{
"who":"HR Executive",
"time":"1 Day",
"how":"Schedule interview"
},

"P8":{
"who":"HOD",
"time":"3 Days",
"how":"Interview assessment"
},

"P9":{
"who":"HR Manager",
"time":"2 Days",
"how":"Verify documents and issue LOI"
},

"P10":{
"who":"HR Executive",
"time":"1 Day",
"how":"Share candidate details with IT"
},

"P11":{
"who":"Site HR",
"time":"2 Days",
"how":"Receive CV"
},

"P12":{
"who":"Site HR",
"time":"3 Days",
"how":"Schedule interview"
},

"P13":{
"who":"HOD",
"time":"2 Days",
"how":"Final selection"
},

"P14":{
"who":"Site HR",
"time":"1 Day",
"how":"Confirm salary"
}
}
HR_MANAGER_IDS = {
    "AR000004"
}

HR_EXECUTIVE_IDS = {
    "AR000003"
}

SITE_HR_EXECUTIVE_IDS = {
    "AR000003"
}

HOD_IDS = {
    "AR000011"
}

HR_ALL_ACCESS = HR_MANAGER_IDS | HR_EXECUTIVE_IDS | SITE_HR_EXECUTIVE_IDS
RECRUITMENT_ACCESS_IDS = (
        HR_MANAGER_IDS |
        HR_EXECUTIVE_IDS |
        SITE_HR_EXECUTIVE_IDS |
        HOD_IDS
)
STAGE_TIME_LIMITS = {

"P1":4*60*60,
"P2":2*60*60,
"P3":2*60*60,
"P4":2*24*60*60,
"P5":2*60*60,
"P6":24*60*60,
"P7":24*60*60,
"P8":3*24*60*60,
"P9":2*24*60*60,
"P10":24*60*60,
"P11":2*24*60*60,
"P12":3*24*60*60,
"P13":2*24*60*60,
"P14":24*60*60
}

# ================================= Helpers ===============================================================

def get_default_photo(photo_link):
    return photo_link if photo_link else "images/placeholder-user.png"

def allowed_file(filename):
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in {'png','jpg','jpeg','webp'}
    )


def can_access_stage(emp_code, stage):

    if stage == "P0":
        return emp_code in HR_MANAGER_IDS

    if stage in ["P2","P3","P4","P5","P7","P10"]:
        return emp_code in HR_EXECUTIVE_IDS

    if stage in ["P11","P12","P14"]:
        return emp_code in SITE_HR_EXECUTIVE_IDS

    if stage == "P9":
        return emp_code in HR_MANAGER_IDS

    return False


# ================================= Login ==================================================

@app.route('/', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        emp_code = request.form['emp_code']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute("""
        SELECT Emp_Code,password,Designation,Department,
        Admin,Photo_Link,Email_ID_Official,Contact_number,
        user_Access,Person_Accountable,Reporting_DOER
        FROM Employee_Master
        WHERE Emp_Code=%s AND STATUS='ACTIVE'
        """,(emp_code,))

        user = cur.fetchone()
        cur.close()

        if user and user[1] == password:

            session['emp_code'] = user[0]
            session['designation'] = user[2]
            session['department'] = user[3]
            session['admin'] = user[4]
            session['photo'] = get_default_photo(user[5])
            session['email'] = user[6]
            session['contact'] = user[7]
            session['user_Access'] = user[8]
            session['person_Accountable'] = user[9]
            session['Reporting_DOER'] = user[10]

            return redirect(url_for('dashboard'))

        flash('Invalid Credentials','danger')

    return render_template('login.html')


# ================================= Upload Photo ===========================================

@app.route('/upload_photo', methods=['POST'])
def upload_photo():

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    file = request.files.get('photo')

    if not file or file.filename == '':
        flash('No file selected','danger')
        return redirect(url_for('dashboard'))

    if not allowed_file(file.filename):
        flash('Invalid file type','danger')
        return redirect(url_for('dashboard'))

    ext = file.filename.rsplit('.',1)[1].lower()
    filename = secure_filename(f"{session['emp_code']}.{ext}")

    upload_folder = app.config['PROFILE_PHOTO_FOLDER']
    os.makedirs(upload_folder,exist_ok=True)

    file_path = os.path.join(upload_folder,filename)
    file.save(file_path)

    db_path = f"uploads/profile_photos/{filename}"

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE Employee_Master
    SET Photo_Link=%s
    WHERE Emp_Code=%s
    """,(db_path,session['emp_code']))

    mysql.connection.commit()
    cur.close()

    flash('Profile photo updated','success')

    return redirect(url_for('dashboard'))


# ================================= Dashboard ===============================================

@app.route('/dashboard')
def dashboard():

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    fixed_menus = {}

    # Only show HR recruitment to whitelisted employees
    if emp_code in HR_ALL_ACCESS|HOD_IDS:

        fixed_menus["HR Recruitment"] = [
            ("Recruitment Panel", url_for('fms_hr_recruitment_panel'))
        ]
    return render_template(
        "dashboard.html",
        fixed_menus=fixed_menus,
        person_Accountable=session["person_Accountable"],
        emp_code=session["emp_code"],
        photo=session["photo"]
    )

    # ================= Sidebar Menu =================

    fixed_menus = {}

    if emp_code in HR_ALL_ACCESS:

        fixed_menus["HR Recruitment"] = [
             ("Recruitment Dashboard", url_for('dashboard'))
        ]

    return render_template(
        'dashboard.html',
        fixed_menus=fixed_menus,
        person_Accountable=session['person_Accountable'],
        emp_code=session['emp_code'],
        photo=session['photo'],
        pending_tasks=pending
    )


# ================================= Forgot Password ========================================

@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():

    emp_code = session.get('emp_code','')
    is_logged_in = 'readonly' if emp_code else ''

    if request.method == 'POST':

        emp_code = request.form['emp_code']
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        cur = mysql.connection.cursor()

        cur.execute("""
        SELECT password
        FROM Employee_Master
        WHERE Emp_Code=%s
        """,(emp_code,))

        user = cur.fetchone()

        if not user:
            flash('Employee ID not found!','danger')
            return redirect(url_for('forgot_password'))

        if user[0] != old_password:
            flash('Old password incorrect!','danger')
            return redirect(url_for('forgot_password'))

        cur.execute("""
        UPDATE Employee_Master
        SET password=%s
        WHERE Emp_Code=%s
        """,(new_password,emp_code))

        cur.execute("""
        INSERT INTO Password_Records
        (Emp_Code,New_Password)
        VALUES(%s,%s)
        """,(emp_code,new_password))

        mysql.connection.commit()
        cur.close()

        flash('Password reset successfully','success')

        return redirect(url_for('login'))

    return render_template('forgot_password.html',emp_code=emp_code,is_logged_in=is_logged_in)


# ================================= Logout ==================================================

@app.route('/logout')
def logout():

    session.clear()
    return redirect(url_for('login'))


# ================================= Recruitment APIs =======================================

@app.route('/recruitment/<int:task_id>/next', methods=['POST'])
def fms_hr_recruitment_next_stage(task_id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
    SELECT workflow_stage
    FROM recruitment_requests
    WHERE id=%s
    """,(task_id,))

    r = cur.fetchone()

    stage = r["workflow_stage"]

    next_stage = "P"+str(int(stage[1:])+1)

    deadline_seconds = STAGE_TIME_LIMITS.get(next_stage,0)

    deadline = datetime.now() + timedelta(seconds=deadline_seconds)

    cur.execute("""
    UPDATE recruitment_requests
    SET workflow_stage=%s,
        stage_started_at=NOW(),
        deadline_at=%s
    WHERE id=%s
    """,(next_stage,deadline,task_id))

    mysql.connection.commit()

    return jsonify({"stage":next_stage})
# ================================= Cancel Recruitment ======================================

@app.route('/recruitment/<int:task_id>/cancel', methods=['POST'])
def fms_hr_recruitment_cancel(task_id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in HR_MANAGER_IDS:
        return jsonify({"error":"Only HR Manager can cancel"}),403

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE recruitment_requests
    SET status='CANCELLED'
    WHERE id=%s
    """,(task_id,))

    mysql.connection.commit()

    return jsonify({"message":"Task Cancelled"})
@app.route('/recruitment')
def fms_hr_recruitment_panel():

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor(DictCursor)

    # FETCH PROJECTS
    cur.execute("""
        SELECT id, project_name
        FROM projects
        ORDER BY project_name
    """)

    projects = cur.fetchall()

    # FETCH LOCATIONS
    cur.execute("""
        SELECT id, location_name
        FROM locations
        ORDER BY location_name
    """)

    locations = cur.fetchall()

    # FETCH EMPLOYEES
    cur.execute("""
        SELECT Emp_Code, Person_Accountable
        FROM Employee_Master
        WHERE STATUS='ACTIVE'
    """)

    employees = cur.fetchall()

    # FETCH RECRUITMENT TASKS
    cur.execute("""
                SELECT *
                FROM recruitment_requests
                WHERE status = 'OPEN'
                ORDER BY id DESC
                """)

    all_tasks = cur.fetchall()

    tasks = []

    for t in all_tasks:

        if fms_hr_recruitment_can_view_task(session['emp_code'], t["workflow_stage"]):
            tasks.append(t)

    return render_template(
        "recruitment.html",
        powers=WORKFLOW_POWERS,
        projects=projects,

        locations=locations,
        employees=employees,
        tasks=tasks,
        now=datetime.now(),
        help_data=WORKFLOW_HELP,
        person_Accountable=session["person_Accountable"],
        emp_code=session["emp_code"],
        photo=session["photo"],
        can_create=session["emp_code"] in HOD_IDS,
        is_hr_manager=session["emp_code"] in HR_MANAGER_IDS,
        is_hod = session["emp_code"] in HOD_IDS

    )
@app.route('/locations/<int:project_id>')
def fms_hr_recruitment_get_locations(project_id):

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
        SELECT id, location_name
        FROM locations
        WHERE project_id=%s
        ORDER BY location_name
    """,(project_id,))

    locations = cur.fetchall()

    cur.close()

    return jsonify(locations)
@app.route('/recruitment/create', methods=['POST'])
def fms_hr_recruitment_create():

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    project_id = request.form['project_id']
    job_designation = request.form['job_designation']
    job_responsibilities = request.form['job_responsibilities']
    location_id = request.form['location_id']
    reporting_authority_id = request.form['reporting_authority_id']
    position_type = request.form['position_type']
    replacement_employee_id = request.form.get('replacement_employee_id')
    educational_qualification = request.form['educational_qualification']
    experience_required = request.form['experience_required']
    gender_preference = request.form['gender_preference']
    age = request.form['age']
    monthly_gross_salary = request.form['monthly_gross_salary']
    number_of_positions = request.form['number_of_positions']
    additional_note = request.form['additional_note']

    attachment = request.files.get('attachment')
    attachment_path = None

    if attachment and attachment.filename != "":
        filename = secure_filename(attachment.filename)
        folder = "static/uploads/recruitment"
        os.makedirs(folder, exist_ok=True)
        attachment.save(os.path.join(folder, filename))
        attachment_path = f"uploads/recruitment/{filename}"

    deadline = datetime.now() + timedelta(seconds=STAGE_TIME_LIMITS["P1"])

    cur = mysql.connection.cursor()

    cur.execute("""
    INSERT INTO recruitment_requests(
        project_id,
        job_designation,
        job_responsibilities,
        attachment_path,
        location_id,
        reporting_authority_id,
        position_type,
        replacement_employee_id,
        educational_qualification,
        experience_required,
        gender_preference,
        age,
        monthly_gross_salary,
        number_of_positions,
        additional_note,
        workflow_stage,
        stage_started_at,
        deadline_at
    )
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'P1',NOW(),%s)
    """,
    (
        project_id,
        job_designation,
        job_responsibilities,
        attachment_path,
        location_id,
        reporting_authority_id,
        position_type,
        replacement_employee_id,
        educational_qualification,
        experience_required,
        gender_preference,
        age,
        monthly_gross_salary,
        number_of_positions,
        additional_note,
        deadline
    ))

    mysql.connection.commit()
    cur.close()

    flash("Recruitment request created successfully","success")

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/approve', methods=['POST'])
def fms_hr_recruitment_approve(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in HR_MANAGER_IDS:
        return jsonify({"error":"Unauthorized"}), 403

    decision = request.form['decision']
    remarks = request.form['remarks']

    cur = mysql.connection.cursor()

    if decision == "YES":
        cur.execute("""
        UPDATE recruitment_requests
        SET workflow_stage='P2',
            hr_manager_remarks=%s,
            hr_manager_approved_by=%s,
            hr_manager_approved_at=NOW()
        WHERE id=%s
        """,(remarks, emp_code, id))

    else:
        cur.execute("""
        UPDATE recruitment_requests
        SET status='CLOSED',
            hr_manager_remarks=%s,
            hr_manager_approved_by=%s,
            hr_manager_approved_at=NOW()
        WHERE id=%s
        """,(remarks, emp_code, id))

    mysql.connection.commit()
    cur.close()

    flash("Recruitment request updated successfully", "success")
    return redirect(url_for('fms_hr_recruitment_panel'))
def fms_hr_recruitment_can_view_task(emp_code, stage):

    # HR Manager can see all stages
    if emp_code in HR_MANAGER_IDS:
        return True

    if stage == "P0":
        return emp_code in HOD_IDS

    if stage in ["P2","P3","P4","P5","P7"]:
        return emp_code in HR_EXECUTIVE_IDS

    if stage in ["P6","P8","P13"]:
        return emp_code in HOD_IDS

    if stage == "P10":
        return emp_code in HR_EXECUTIVE_IDS

    if stage in ["P11","P12","P14"]:
        return emp_code in SITE_HR_EXECUTIVE_IDS

    return False
@app.route('/recruitment/<int:id>/groupd', methods=['POST'])
def fms_hr_recruitment_groupd_check(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in HR_EXECUTIVE_IDS:
        return jsonify({"error":"Unauthorized"}),403

    decision = request.form['groupd_decision']

    if decision == "YES":
        next_stage = "P11"
    else:
        next_stage = "P4"

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE recruitment_requests
    SET workflow_stage=%s
    WHERE id=%s
    """,(next_stage,id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/sitehr_approve', methods=['POST'])
def fms_hr_recruitment_sitehr_approve(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in SITE_HR_EXECUTIVE_IDS:
        return jsonify({"error":"Unauthorized"}),403

    remarks = request.form['remarks']

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
    SELECT workflow_stage
    FROM recruitment_requests
    WHERE id=%s
    """,(id,))

    task = cur.fetchone()

    stage = task["workflow_stage"]

    if stage == "P11":
        next_stage = "P12"

    elif stage == "P12":
        next_stage = "P13"

    else:
        return jsonify({"error":"Invalid stage"}),400

    cur.execute("""
    UPDATE recruitment_requests
    SET workflow_stage=%s,
        site_hr_remarks=%s
    WHERE id=%s
    """,(next_stage,remarks,id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/hod_final_approve', methods=['POST'])
def fms_hr_recruitment_hod_final_approve(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in HOD_IDS:
        return jsonify({"error":"Only HOD can approve"}),403

    remarks = request.form['remarks']
    file = request.files.get("attachment")

    attachment_path = None

    if file and file.filename:

        filename = secure_filename(file.filename)

        upload_folder = "static/uploads/hod_final"

        os.makedirs(upload_folder, exist_ok=True)

        path = os.path.join(upload_folder, filename)

        file.save(path)

        attachment_path = f"uploads/hod_final/{filename}"

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE recruitment_requests
    SET workflow_stage='P14',
        hod_final_remarks=%s,
        hod_final_attachment=%s,
        hod_final_approved_by=%s,
        hod_final_approved_at=NOW()
    WHERE id=%s
    """,(remarks,attachment_path,emp_code,id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/salary_confirm', methods=['POST'])
def fms_hr_recruitment_salary_confirm(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in SITE_HR_EXECUTIVE_IDS:
        return jsonify({"error":"Unauthorized"}),403

    remarks = request.form['remarks']
    file = request.files.get("attachment")

    attachment_path = None

    if file and file.filename:

        filename = secure_filename(file.filename)

        upload_folder = "static/uploads/salary_confirmation"

        os.makedirs(upload_folder, exist_ok=True)

        path = os.path.join(upload_folder, filename)

        file.save(path)

        attachment_path = f"uploads/salary_confirmation/{filename}"

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE recruitment_requests
    SET status='CLOSED',
        salary_confirmation_remarks=%s,
        salary_confirmation_attachment=%s,
        salary_confirmed_by=%s,
        salary_confirmed_at=NOW()
    WHERE id=%s
    """,(remarks,attachment_path,emp_code,id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/stage_approve', methods=['POST'])
def fms_hr_recruitment_stage_approve(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
    SELECT workflow_stage
    FROM recruitment_requests
    WHERE id=%s
    """,(id,))

    task = cur.fetchone()
    stage = task["workflow_stage"]

    remarks = request.form['remarks']
    file = request.files.get("attachment")

    attachment_path = None

    if file and file.filename:
        filename = secure_filename(file.filename)
        folder = "static/uploads/workflow"
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        file.save(path)
        attachment_path = f"uploads/workflow/{filename}"

    if stage == "P10":
        cur.execute("""
        UPDATE recruitment_requests
        SET status='CLOSED',
            workflow_stage='P10',
            workflow_remarks=%s,
            workflow_attachment=%s,
            workflow_updated_by=%s,
            workflow_updated_at=NOW()
        WHERE id=%s
        """,(remarks, attachment_path, emp_code, id))

    else:
        next_stage = "P" + str(int(stage[1:]) + 1)
        deadline_seconds = STAGE_TIME_LIMITS.get(next_stage, 0)
        deadline = datetime.now() + timedelta(seconds=deadline_seconds)

        cur.execute("""
        UPDATE recruitment_requests
        SET workflow_stage=%s,
            workflow_remarks=%s,
            workflow_attachment=%s,
            workflow_updated_by=%s,
            workflow_updated_at=NOW(),
            stage_started_at=NOW(),
            deadline_at=%s
        WHERE id=%s
        """,(next_stage, remarks, attachment_path, emp_code, deadline, id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/candidate_decision', methods=['POST'])
def fms_hr_recruitment_candidate_decision(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    if emp_code not in HOD_IDS:
        return jsonify({"error":"Only HOD can make this decision"}),403

    decision = request.form['decision']
    remarks = request.form['remarks']

    file = request.files.get("attachment")

    attachment_path = None

    if file and file.filename:

        filename = secure_filename(file.filename)

        folder = "static/uploads/candidate_decision"

        os.makedirs(folder, exist_ok=True)

        path = os.path.join(folder, filename)

        file.save(path)

        attachment_path = f"uploads/candidate_decision/{filename}"

    if decision == "YES":
        next_stage = "P9"
    else:
        next_stage = "P4"

    cur = mysql.connection.cursor()

    cur.execute("""
    UPDATE recruitment_requests
    SET workflow_stage=%s,
        candidate_decision=%s,
        candidate_decision_remarks=%s,
        candidate_decision_attachment=%s,
        candidate_decided_by=%s,
        candidate_decided_at=NOW()
    WHERE id=%s
    """,(next_stage,decision,remarks,attachment_path,emp_code,id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))
@app.route('/recruitment/<int:id>/loi_process', methods=['POST'])
def fms_hr_recruitment_loi_process(id):

    if 'emp_code' not in session:
        return redirect(url_for('login'))

    emp_code = session['emp_code']

    remarks = request.form['remarks']
    file = request.files.get("attachment")

    attachment_path = None

    if file and file.filename:
        filename = secure_filename(file.filename)
        folder = "static/uploads/loi_process"
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        file.save(path)
        attachment_path = f"uploads/loi_process/{filename}"

    cur = mysql.connection.cursor(DictCursor)

    cur.execute("""
    SELECT workflow_stage
    FROM recruitment_requests
    WHERE id=%s
    """,(id,))

    task = cur.fetchone()
    stage = task["workflow_stage"]

    if stage == "P9" and emp_code not in HR_MANAGER_IDS:
        return jsonify({"error":"Only HR Manager allowed"}),403

    if stage == "P10" and emp_code not in HR_EXECUTIVE_IDS:
        return jsonify({"error":"Only HR Executive allowed"}),403

    if stage == "P10":
        cur.execute("""
        UPDATE recruitment_requests
        SET status='CLOSED',
            workflow_stage='P10',
            loi_process_remarks=%s,
            loi_process_attachment=%s,
            loi_processed_by=%s,
            loi_processed_at=NOW()
        WHERE id=%s
        """,(remarks, attachment_path, emp_code, id))

    else:
        next_stage = "P" + str(int(stage[1:]) + 1)
        cur.execute("""
        UPDATE recruitment_requests
        SET workflow_stage=%s,
            loi_process_remarks=%s,
            loi_process_attachment=%s,
            loi_processed_by=%s,
            loi_processed_at=NOW()
        WHERE id=%s
        """,(next_stage, remarks, attachment_path, emp_code, id))

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('fms_hr_recruitment_panel'))

# ================================= Run Server ==============================================

if __name__ == "__main__":
    app.run(debug=True, port=5001)