from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import HTMLResponse
import docx
import PyPDF2
import io

app = FastAPI()

# --- 1. RESUME SCREENER LOGIC (From your .ipynb) ---
domain_keywords = {
    "Data Science": {
        "great": ["machine learning", "deep learning", "data analysis", "python", "ai", "statistics", "data visualization"],
        "good": ["pandas", "numpy", "matplotlib", "sql", "data cleaning", "presentation"],
        "medium": ["communication", "excel", "reporting"]
    },
    "Software Development": {
        "great": ["java", "python", "c++", "software architecture", "api", "debugging", "version control"],
        "good": ["git", "frontend", "backend", "database", "rest api", "teamwork"],
        "medium": ["html", "css", "basic", "communication"]
    },
    "Marketing": {
        "great": ["campaign management", "seo", "branding", "digital marketing", "analytics", "social media"],
        "good": ["content creation", "market research", "advertising", "presentation"],
        "medium": ["communication", "teamwork", "reporting"]
    },
    "Finance": {
        "great": ["financial analysis", "budgeting", "investment", "forecasting", "risk management", "excel modeling"],
        "good": ["data analysis", "presentation", "accounting", "reports"],
        "medium": ["communication", "teamwork", "documentation"]
    }
}

def analyze_resume(text, domain):
    text = text.lower()
    keywords = domain_keywords.get(domain, {})
    score = 0
    matched = {'great': [], 'good': [], 'medium': []}

    for level in ["great", "good", "medium"]:
        for word in keywords.get(level, []):
            if word in text:
                score += {"great": 3, "good": 2, "medium": 1}[level]
                matched[level].append(word)

    if score >= 20: category = "Great"
    elif score >= 14: category = "Good"
    elif score >= 8: category = "Medium"
    elif score >= 4: category = "Average"
    else: category = "Below Average"

    feedback = generate_feedback(category, matched, domain)
    return category, feedback

def generate_feedback(category, matched, domain):
    base_feedback = {
        "Great": "Excellent work! You have strong domain expertise and technical skills.",
        "Good": "Good resume! Strengthen it with measurable results and specific project examples.",
        "Medium": "Your resume is decent, but consider adding more domain-relevant projects and tools.",
        "Average": "Your resume lacks sufficient domain depth. Highlight your projects and use keywords.",
        "Below Average": "Your resume seems generic. Focus on adding domain-specific skills and achievements."
    }
    
    domain_advice = {
        "Data Science": "Include metrics (e.g., accuracy, F1-score) and showcase projects on Kaggle or GitHub.",
        "Software Development": "Showcase code samples, GitHub links, or contributions to real-world applications.",
        "Marketing": "Add results (e.g., campaign ROI, engagement rates) and examples of brand impact.",
        "Finance": "Include certifications (CFA, CPA), tools (Excel, Power BI), and quantitative results."
    }

    feedback = base_feedback.get(category, "") + " " + domain_advice.get(domain, "")
    keyword_summary = (
        f"<br><br><b>Matched Keywords:</b><br>"
        f"🟢 Great: {', '.join(matched['great']) or 'None'}<br>"
        f"🟡 Good: {', '.join(matched['good']) or 'None'}<br>"
        f"⚪ Medium: {', '.join(matched['medium']) or 'None'}"
    )
    return feedback + keyword_summary

# --- 2. FRONTEND HTML/CSS ---
html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Resume Screener</title>
    <style>
        body {
            /* Dark purple sky background */
            background: linear-gradient(to bottom, #1a0b2e, #4b1d52);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: rgba(0, 0, 0, 0.4);
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            text-align: center;
            width: 400px;
        }
        h1 { margin-top: 0; margin-bottom: 20px; font-weight: 300; letter-spacing: 2px;}
        select, input[type="file"] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: none;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        button {
            /* Blue evaluate button */
            background-color: #007bff;
            color: white;
            border: none;
            padding: 12px 20px;
            width: 100%;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 15px;
            transition: background-color 0.3s;
        }
        button:hover { background-color: #0056b3; }
        #resultBox {
            margin-top: 25px;
            padding: 15px;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            text-align: left;
            display: none;
        }
        .grade { font-size: 1.2em; font-weight: bold; color: #00d2ff; }
    </style>
</head>
<body>

<div class="container">
    <h1>Resume Screener</h1>
    
    <select id="domainSelector">
        <option value="" disabled selected>Select Target Domain</option>
        <option value="Data Science">Data Science</option>
        <option value="Software Development">Software Development</option>
        <option value="Marketing">Marketing</option>
        <option value="Finance">Finance</option>
    </select>

    <select id="fileTypeSelector">
        <option value="None">None</option>
        <option value="Word">Word (.docx)</option>
        <option value="PDF">PDF (.pdf)</option>
    </select>

    <input type="file" id="resumeFile" accept=".docx,.pdf">
    
    <button onclick="evaluateResume()">Evaluate</button>

    <div id="resultBox">
        <div class="grade" id="gradeOutput"></div>
        <div id="commentsOutput" style="margin-top: 10px;"></div>
    </div>
</div>

<script>
    async function evaluateResume() {
        const domain = document.getElementById('domainSelector').value;
        const fileType = document.getElementById('fileTypeSelector').value;
        const fileInput = document.getElementById('resumeFile').files[0];
        const resultBox = document.getElementById('resultBox');
        const gradeOutput = document.getElementById('gradeOutput');
        const commentsOutput = document.getElementById('commentsOutput');

        if (!domain) {
            alert("Please select a target domain!");
            return;
        }
        if (fileType === "None" || !fileInput) {
            alert("Please select a file type and upload a file!");
            return;
        }

        const formData = new FormData();
        formData.append("domain", domain);
        formData.append("fileType", fileType);
        formData.append("file", fileInput);

        gradeOutput.innerHTML = "Processing...";
        commentsOutput.innerHTML = "";
        resultBox.style.display = "block";

        try {
            const response = await fetch("/evaluate", {
                method: "POST",
                body: formData
            });
            const data = await response.json();
            
            if(data.error) {
                gradeOutput.innerHTML = "Error";
                commentsOutput.innerHTML = data.error;
            } else {
                gradeOutput.innerHTML = "Grade: " + data.grade;
                commentsOutput.innerHTML = data.comments;
            }
        } catch (error) {
            gradeOutput.innerHTML = "Error";
            commentsOutput.innerHTML = "Failed to connect to the server.";
        }
    }
</script>

</body>
</html>
"""

# --- 3. API ENDPOINTS ---
@app.get("/", response_class=HTMLResponse)
async def get_frontend():
    return html_content

@app.post("/evaluate")
async def evaluate_endpoint(
    domain: str = Form(...), 
    fileType: str = Form(...), 
    file: UploadFile = File(...)
):
    try:
        content = await file.read()
        text = ""

        # Extract text based on file type
        if fileType == "Word" or file.filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([para.text for para in doc.paragraphs])
        elif fileType == "PDF" or file.filename.endswith('.pdf'):
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            return {"error": "Unsupported file format. Please upload Word or PDF."}

        # Run your logic
        category, feedback = analyze_resume(text, domain)
        return {"grade": category, "comments": feedback}
        
    except Exception as e:
        return {"error": str(e)}