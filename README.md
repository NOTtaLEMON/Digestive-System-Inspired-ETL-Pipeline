# healthcare-data-wrangling
Data cleaning project for messy healthcare records
# 🏥 Healthcare Data Wrangling Project

This project focuses purely on **data wrangling** cleaning, organizing, and preparing a messy healthcare dataset for analysis. No modeling or visualizations are included. The goal is to demonstrate strong data preparation skills, crucial for any data-related role.

---

## 📁 Dataset Overview

The dataset contains synthetic health records with the following fields:

- `patientid`: Unique patient identifier
- `name`: Full name (uncleaned format originally)
- `gender`: Gender of the patient (inconsistent and messy in raw data)
- `age`: Age in years
- `height(cm)` / `weight(kg)`: Patient height and weight
- `bmi`: Calculated Body Mass Index
- `bloodpressure`: Systolic/Diastolic values (in various formats originally)
- `diabetes`: Diabetes status
- `smoker`: Smoking status
- `dateofvisit`: Date the patient visited (in inconsistent formats originally)
- `diagnosis`: Primary diagnosis (some missing or inconsistent)
- `height(m)`: Height converted to meters
- `yearofvisit`: Extracted year from visit date

---

## 🔧 Cleaning & Wrangling Tasks

### ✅ Performed

- Renamed columns to lowercase and consistent formats.
- Fixed inconsistent gender, smoker, and diabetes entries.
- Converted mixed date formats into proper datetime.
- Removed duplicates and unnecessary index columns.
- Handled missing values with appropriate strategies.
- Extracted `yearofvisit` from `dateofvisit`.
- Calculated BMI using:  
  \[
  BMI = weight (kg)/(\(height (m)^2)
  \]
- Standardized blood pressure format.
- Verified data types and corrected as needed.

---

## 📊 Final Dataset Quality

- 100% non-null values
- Clean, analysis-ready format
- Consistent data types
- Fully reproducible pipeline

---

## 📁 Files

- `messy_health_data.csv`: Original raw synthetic data 
- `cleaned_health_data.csv`: Final cleaned dataset
- `notebook.ipynb`: Full cleaning workflow in Python 

---

## ✍️ Author

**John Agu Michael**  
www.linkedin.com/in/michael-john-agu-9974361a5
---

## 🧠 Future Work

- Add exploratory data analysis (EDA)
- Visualize BMI and diagnosis trends
- Build predictive models (e.g., diabetes risk)

---

## 💡 Inspiration

Inspired by real-world hospital data challenges where cleaning is often 80% of the work.

