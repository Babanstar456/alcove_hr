CREATE DATABASE Fms_hr_recruitment_annex1;
USE Fms_hr_recruitment_annex1;

-- =============================
-- MASTER TABLES
-- =============================

CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL
);

CREATE TABLE employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_name VARCHAR(255) NOT NULL,
    designation VARCHAR(255),
    status ENUM('ACTIVE','INACTIVE') DEFAULT 'ACTIVE'
);

CREATE TABLE locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL
);

CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL
);

CREATE TABLE directors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    director_name VARCHAR(255) NOT NULL
);

CREATE TABLE hr_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    role ENUM('HR_MANAGER','HR_EXECUTIVE','SITE_HR_EXECUTIVE','ADMIN'),
    email VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================
-- RECRUITMENT REQUEST FORM
-- =============================

CREATE TABLE recruitment_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,

    project_id INT NOT NULL,
    job_designation VARCHAR(255) NOT NULL,
    job_responsibilities TEXT NOT NULL,

    attachment_path VARCHAR(500),

    location_id INT NOT NULL,

    reporting_authority_id INT NOT NULL,

    position_type ENUM('NEW','REPLACEMENT') NOT NULL,

    replacement_employee_id INT,

    educational_qualification TEXT NOT NULL,

    experience_required VARCHAR(10) NOT NULL,

    gender_preference ENUM('MALE','FEMALE','ANY'),

    age INT,

    monthly_gross_salary DECIMAL(10,2),

    number_of_positions INT,

    additional_note TEXT,

    approved_by INT,

    approved_date DATE,

    status ENUM('OPEN','CANCELLED','CLOSED') DEFAULT 'OPEN',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    FOREIGN KEY (reporting_authority_id) REFERENCES employees(id),
    FOREIGN KEY (replacement_employee_id) REFERENCES employees(id),
    FOREIGN KEY (approved_by) REFERENCES directors(id)
);

-- =============================
-- ATTACHMENTS TABLE
-- =============================

CREATE TABLE recruitment_attachments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recruitment_id INT,
    file_path VARCHAR(500),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (recruitment_id) REFERENCES recruitment_requests(id)
);

-- =============================
-- PRE JOINING FORM
-- =============================

CREATE TABLE pre_joining_forms (
    id INT AUTO_INCREMENT PRIMARY KEY,

    recruitment_id INT NOT NULL,

    job_designation VARCHAR(255) NOT NULL,

    replacement_name VARCHAR(255),

    company_id INT NOT NULL,

    joining_date DATE NOT NULL,

    system_type ENUM('DESKTOP','LAPTOP','NA'),

    erp_access BOOLEAN DEFAULT FALSE,

    sim_required BOOLEAN DEFAULT FALSE,

    mobile_required BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (recruitment_id) REFERENCES recruitment_requests(id),
    FOREIGN KEY (company_id) REFERENCES companies(id)
);