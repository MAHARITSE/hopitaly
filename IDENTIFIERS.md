# Hopitaly Database Identifiers

This document lists the key identifiers (primary keys) from the JSON database (`db.json`).

## Users (`auth_user`)

| ID | Username | Email | Role | First Name | Last Name |
|----|----------|-------|------|------------|-----------|
| 1 | admin | (empty) | Superuser | - | - |
| 2 | admina@test.com | (empty) | Admin | - | - |
| 3 | doctora@test.com | doctora@test.com | Doctor | - | - |
| 4 | doctorb@test.com | doctorb@test.com | Doctor | - | - |
| 5 | nursea@test.com | nursea@test.com | Nurse | - | - |
| 6 | patientb@test.com | patientb@test.com | Patient | - | - |
| 7 | patientc@test.com | patientc@test.com | Patient | - | - |
| 8 | patienta@test.com | patienta@test.com | Patient | - | - |

## Profiles (`healthnet_profile`)

| ID | First Name | Last Name | Sex | Birthday | Phone | Insurance | User ID |
|----|------------|-----------|-----|----------|-------|-----------|---------|
| 1 | Kenn | Martinez | M | 1975-04-19 | 4565768 | 24324 | 2 |
| 2 | Joe | Cumbo | - | 1000-01-01 | - | - | 3 |
| 3 | Daniel | Roach | - | 1000-01-01 | - | - | 4 |
| 4 | Kaiwen | Zheng | M | 1000-01-01 | - | 43525235 | 5 |
| 5 | He | Zheng | - | 1000-01-01 | - | 45325 | 6 |
| 6 | Arshdeep | Khalsa | - | 1000-01-01 | - | 452RTERG | 7 |
| 7 | John | Wadach | - | 1000-01-01 | - | 452545 | 8 |

## Accounts (`healthnet_account`)

| ID | Role | Profile ID | User ID |
|----|------|------------|---------|
| 1 | 40 (Admin) | 1 | 2 |
| 2 | 30 (Doctor) | 2 | 3 |
| 3 | 30 (Doctor) | 3 | 4 |
| 4 | 20 (Nurse) | 4 | 5 |
| 5 | 10 (Patient) | 5 | 6 |
| 6 | 10 (Patient) | 6 | 7 |
| 7 | 10 (Patient) | 7 | 8 |

**Role Codes:**
- 40 = Admin
- 30 = Doctor
- 20 = Nurse
- 10 = Patient

## Locations (`healthnet_location`)

| ID | Address | City | State | ZIP | Country |
|----|---------|------|-------|-----|---------|
| 1 | 1 Hope Street | Rochester | NY | 123123 | USA |
| 2 | 2 Rule Road | Rochester | NY | 123123 | USA |

## Hospitals (`healthnet_hospital`)

| ID | Name | Phone | Location ID |
|----|------|-------|-------------|
| 1 | Strong | 45353 | 1 |
| 2 | Highland | 3441 | 2 |

## Medical Info (`healthnet_medicalinfo`)

| ID | Patient ID | Blood Type | Allergy | Asthma | Alzheimer | Diabetes | Stroke |
|----|------------|------------|---------|--------|-----------|----------|--------|
| 1 | 6 | O- | Healthnet | 1 | 0 | 0 | 0 |
| 2 | 7 | A+ | (empty) | 0 | 0 | 0 | 0 |
| 3 | 8 | AB+ | Python | 0 | 0 | 0 | 0 |

## Messages (`healthnet_message`)

| ID | Sender ID | Target ID | Header | Body | Read | Timestamp |
|----|-----------|-----------|--------|------|------|-----------|
| 1 | 2 | 2 | Hey | You're pretty cool | 1 | 2015-04-20 03:42:49.232000 |

## Actions (`healthnet_action`)

| ID | Type | User ID | Description | Time Performed |
|----|------|---------|-------------|----------------|
| 1 | 1 | 1 | Account logout | 2015-04-19 18:44:45.757039 |
| 2 | 1 | 2 | Account login | 2015-04-19 18:44:53.832018 |
| 3 | 3 | 2 | Admin registered doctora@test.com | 2015-04-19 18:48:24.387544 |
| 4 | 3 | 2 | Admin registered doctorb@test.com | 2015-04-19 18:48:43.685350 |
| 5 | 3 | 2 | Admin registered nursea@test.com | 2015-04-19 18:48:59.045361 |
| ... | ... | ... | ... | ... |

**Action Types:**
- 1 = Login/Logout/Registration
- 3 = Admin registered user
- 8 = Medical info updated
- 9 = Message sent/read

## Content Types (`django_content_type`)

| ID | App Label | Model | Name |
|----|-----------|-------|------|
| 1 | admin | logentry | log entry |
| 2 | auth | permission | permission |
| 3 | auth | group | group |
| 4 | auth | user | user |
| 5 | contenttypes | contenttype | content type |
| 6 | sessions | session | session |
| 7 | healthnet | location | location |
| 8 | healthnet | hospital | hospital |
| 9 | healthnet | profile | profile |
| 10 | healthnet | account | account |
| 11 | healthnet | action | action |
| 12 | healthnet | appointment | appointment |
| 13 | healthnet | message | message |
| 14 | healthnet | notification | notification |
| 15 | healthnet | admission | admission |
| 16 | healthnet | prescription | prescription |
| 17 | healthnet | medicalinfo | medical info |
| 18 | healthnet | medicaltest | medical test |
| 19 | healthnet | statistics | statistics |

## Permissions (`auth_permission`)

Key permissions (ID → Codename):
- 1-3: Log entry (add/change/delete)
- 4-6: Permission (add/change/delete)
- 7-9: Group (add/change/delete)
- 10-12: User (add/change/delete)
- 13-15: Content type (add/change/delete)
- 16-18: Session (add/change/delete)
- 19-21: Location (add/change/delete)
- 22-24: Hospital (add/change/delete)
- 25-27: Profile (add/change/delete)
- 28-30: Account (add/change/delete)
- 31-33: Action (add/change/delete)
- 34-36: Appointment (add/change/delete)
- 37-39: Message (add/change/delete)
- 40-42: Notification (add/change/delete)
- 43-45: Admission (add/change/delete)
- 46-48: Prescription (add/change/delete)
- 49-51: Medical Info (add/change/delete)
- 52-54: Medical Test (add/change/delete)
- 55-57: Statistics (add/change/delete)

## Empty Tables

The following tables have no data:
- `auth_group`
- `auth_group_permissions`
- `auth_user_groups`
- `auth_user_user_permissions`
- `healthnet_appointment`
- `healthnet_notification`
- `healthnet_admission`
- `healthnet_prescription`
- `healthnet_medicaltest`
- `healthnet_statistics`

---

*Generated from `db.json` - JSON database backend for Django 1.6.5*