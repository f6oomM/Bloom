-- Bloom database schema (MySQL 8, InnoDB, utf8mb4)
-- Run:  mysql -u root -p < backend/database/schema.sql
-- Keep this file in sync with backend/app/models.py (SQLAlchemy).

CREATE DATABASE IF NOT EXISTS bloom CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bloom;

-- ---------------------------------------------------------------
-- Accounts (all three roles log in through this table)
-- ---------------------------------------------------------------
CREATE TABLE users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  email         VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,                 -- hashed, never plain text
  role          ENUM('student','organization','admin') NOT NULL,
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Student profile (replaces CV upload; also used for teammate search)
-- ---------------------------------------------------------------
CREATE TABLE student_profiles (
  user_id          INT PRIMARY KEY,
  full_name        VARCHAR(150) NOT NULL,
  university       VARCHAR(150),
  major            VARCHAR(100),
  year_level       TINYINT,
  city             VARCHAR(100),
  bio              TEXT,
  github_url       VARCHAR(255),
  linkedin_url     VARCHAR(255),
  looking_for_team BOOLEAN NOT NULL DEFAULT FALSE,     -- visible in hackathon teammate search
  updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_sp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_sp_looking (looking_for_team),
  INDEX idx_sp_city (city)
) ENGINE=InnoDB;

CREATE TABLE interests (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE skills (
  id   INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE student_interests (
  student_id  INT NOT NULL,
  interest_id INT NOT NULL,
  PRIMARY KEY (student_id, interest_id),
  CONSTRAINT fk_si_student  FOREIGN KEY (student_id)  REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_si_interest FOREIGN KEY (interest_id) REFERENCES interests(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE student_skills (
  student_id INT NOT NULL,
  skill_id   INT NOT NULL,
  PRIMARY KEY (student_id, skill_id),
  CONSTRAINT fk_ss_student FOREIGN KEY (student_id) REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_ss_skill   FOREIGN KEY (skill_id)   REFERENCES skills(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Organizations / companies (must be approved by an admin)
-- ---------------------------------------------------------------
CREATE TABLE organization_profiles (
  user_id          INT PRIMARY KEY,
  name             VARCHAR(150) NOT NULL,
  description      TEXT,
  website          VARCHAR(255),
  city             VARCHAR(100),
  logo_url         VARCHAR(255),
  approval_status  ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  reviewed_by      INT NULL,
  reviewed_at      DATETIME NULL,
  rejection_reason VARCHAR(255) NULL,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_op_user     FOREIGN KEY (user_id)     REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_op_reviewer FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
  INDEX idx_op_status (approval_status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Opportunities (hackathons, internships, co-ops, volunteering, workshops)
-- ---------------------------------------------------------------
CREATE TABLE opportunities (
  id                   INT AUTO_INCREMENT PRIMARY KEY,
  organization_id      INT NOT NULL,
  title                VARCHAR(200) NOT NULL,
  description          TEXT NOT NULL,
  type                 ENUM('hackathon','internship','coop','volunteer','workshop','seminar') NOT NULL,
  city                 VARCHAR(100),
  is_online            BOOLEAN NOT NULL DEFAULT FALSE,
  start_date           DATETIME NULL,
  end_date             DATETIME NULL,
  application_deadline DATETIME NULL,
  requires_application BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE for open events (workshops)
  max_team_size        TINYINT NULL,                   -- used by hackathons
  status               ENUM('pending','approved','rejected') NOT NULL DEFAULT 'pending',
  reviewed_by          INT NULL,
  reviewed_at          DATETIME NULL,
  rejection_reason     VARCHAR(255) NULL,
  created_at           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_opp_org      FOREIGN KEY (organization_id) REFERENCES organization_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_opp_reviewer FOREIGN KEY (reviewed_by)     REFERENCES users(id) ON DELETE SET NULL,
  -- indexes for the search / filter feature (location, type, dates)
  INDEX idx_opp_status_type (status, type),
  INDEX idx_opp_city (city),
  INDEX idx_opp_start (start_date),
  INDEX idx_opp_deadline (application_deadline),
  INDEX idx_opp_org (organization_id)
) ENGINE=InnoDB;

CREATE TABLE opportunity_interests (
  opportunity_id INT NOT NULL,
  interest_id    INT NOT NULL,
  PRIMARY KEY (opportunity_id, interest_id),
  CONSTRAINT fk_oi_opp      FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  CONSTRAINT fk_oi_interest FOREIGN KEY (interest_id)    REFERENCES interests(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Student actions
-- ---------------------------------------------------------------
CREATE TABLE applications (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  opportunity_id    INT NOT NULL,
  student_id        INT NOT NULL,
  message           TEXT,
  status            ENUM('submitted','under_review','accepted','rejected','withdrawn') NOT NULL DEFAULT 'submitted',
  applied_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  status_updated_at DATETIME NULL,
  CONSTRAINT fk_app_opp     FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  CONSTRAINT fk_app_student FOREIGN KEY (student_id)     REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT uq_app UNIQUE (opportunity_id, student_id),  -- one application per student per opportunity
  INDEX idx_app_student (student_id),
  INDEX idx_app_status (status)
) ENGINE=InnoDB;

-- Personal calendar: events a student saved
CREATE TABLE saved_events (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  student_id     INT NOT NULL,
  opportunity_id INT NOT NULL,
  remind_at      DATETIME NULL,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_se_student FOREIGN KEY (student_id)     REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_se_opp     FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  CONSTRAINT uq_se UNIQUE (student_id, opportunity_id),
  INDEX idx_se_remind (remind_at)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- Team formation (hackathons and group projects)
-- ---------------------------------------------------------------
CREATE TABLE teams (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  opportunity_id INT NOT NULL,
  name           VARCHAR(120) NOT NULL,
  description    TEXT,
  leader_id      INT NOT NULL,
  max_members    TINYINT NOT NULL DEFAULT 4,
  is_open        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_team_opp    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE CASCADE,
  CONSTRAINT fk_team_leader FOREIGN KEY (leader_id)      REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  INDEX idx_team_opp (opportunity_id)
) ENGINE=InnoDB;

CREATE TABLE team_members (
  team_id    INT NOT NULL,
  student_id INT NOT NULL,
  role       ENUM('leader','member') NOT NULL DEFAULT 'member',
  joined_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (team_id, student_id),
  CONSTRAINT fk_tm_team    FOREIGN KEY (team_id)    REFERENCES teams(id) ON DELETE CASCADE,
  CONSTRAINT fk_tm_student FOREIGN KEY (student_id) REFERENCES student_profiles(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE team_join_requests (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  team_id    INT NOT NULL,
  student_id INT NOT NULL,
  message    VARCHAR(500),
  status     ENUM('pending','accepted','declined') NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_tjr_team    FOREIGN KEY (team_id)    REFERENCES teams(id) ON DELETE CASCADE,
  CONSTRAINT fk_tjr_student FOREIGN KEY (student_id) REFERENCES student_profiles(user_id) ON DELETE CASCADE,
  CONSTRAINT uq_tjr UNIQUE (team_id, student_id),
  INDEX idx_tjr_status (status)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------
-- In-app notifications
-- ---------------------------------------------------------------
CREATE TABLE notifications (
  id             INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL,
  type           ENUM('application_update','event_reminder','team_request','team_update','approval_update') NOT NULL,
  message        VARCHAR(500) NOT NULL,
  opportunity_id INT NULL,
  is_read        BOOLEAN NOT NULL DEFAULT FALSE,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_n_user FOREIGN KEY (user_id)        REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_n_opp  FOREIGN KEY (opportunity_id) REFERENCES opportunities(id) ON DELETE SET NULL,
  INDEX idx_n_user_read (user_id, is_read)
) ENGINE=InnoDB;
