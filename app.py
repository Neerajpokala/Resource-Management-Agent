import streamlit as st
import json
import re
from datetime import datetime, date
import os
import pandas as pd
import plotly.express as px
import google.generativeai as genai
from langchain_experimental.agents.agent_toolkits.pandas.base import create_pandas_dataframe_agent
from langchain.agents import AgentExecutor, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI

# --- Common Functions and Data ---

# Page configuration
st.set_page_config(
    page_title="Employee Data Entry System",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="auto"
)

# Skills mapping based on job roles
ROLE_SKILLS = {
    "Backend Developer": ["JavaScript", "Node.js", "Python", "Java", "C#", "PHP", "Go", "Ruby", "Rust", "Scala", "Kotlin", "Express.js", "Django", "Flask", "FastAPI", "Spring Boot", "ASP.NET Core", "Laravel", "Gin", "Echo", "Nest.js", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "Oracle Database", "SQL Server", "Neo4j", "REST API Design", "GraphQL", "gRPC", "WebSocket", "Microservices Architecture", "API Gateway", "OAuth/JWT", "Swagger/OpenAPI", "Message Queues", "Event-Driven Architecture"],
    "Frontend Developer": ["JavaScript (ES6+)", "TypeScript", "HTML5", "CSS3", "Sass/SCSS", "Less", "JSX", "WebAssembly", "React.js", "Vue.js", "Angular", "Next.js", "Nuxt.js", "Svelte/SvelteKit", "Ember.js", "Alpine.js", "Lit", "Stencil", "Material-UI (MUI)", "Ant Design", "Chakra UI", "Bootstrap", "Tailwind CSS", "Styled Components", "Emotion", "Framer Motion", "GSAP", "Three.js", "Redux/Redux Toolkit", "Vuex/Pinia", "MobX", "Zustand", "Recoil", "Context API", "Webpack", "Vite", "Parcel", "Jest", "Cypress", "Testing Library", "Storybook", "ESLint/Prettier"],
    "AI/ML/Data Scientist": ["Python", "R", "SQL", "Scala", "Java", "Julia", "MATLAB", "C++", "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "XGBoost", "LightGBM", "CatBoost", "Statsmodels", "MLflow", "Weights & Biases", "Convolutional Neural Networks (CNN)", "Recurrent Neural Networks (RNN/LSTM)", "Transformers", "BERT/GPT Models", "GANs", "Reinforcement Learning", "Transfer Learning", "Computer Vision", "Natural Language Processing", "Speech Recognition", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly", "Apache Spark", "Hadoop", "Kafka", "Apache Airflow", "Dask", "AWS SageMaker", "Google Cloud AI", "Azure Machine Learning", "Kubeflow", "Docker", "Kubernetes", "MLOps", "Model Deployment", "A/B Testing", "Feature Engineering", "LangChain", "Hugging Face", "OpenAI API"],
    "DevOps Engineer": ["Amazon Web Services (AWS)", "Microsoft Azure", "Google Cloud Platform (GCP)", "DigitalOcean", "IBM Cloud", "Oracle Cloud", "Alibaba Cloud", "Multi-cloud Strategy", "Docker", "Kubernetes", "Docker Compose", "Helm", "OpenShift", "Rancher", "Istio", "Linkerd", "Terraform", "AWS CloudFormation", "Azure Resource Manager", "Google Cloud Deployment Manager", "Pulumi", "Ansible", "Chef", "Puppet", "SaltStack", "Jenkins", "GitLab CI/CD", "GitHub Actions", "Azure DevOps", "CircleCI", "Travis CI", "Bamboo", "TeamCity", "ArgoCD", "Spinnaker", "Prometheus", "Grafana", "ELK Stack", "Datadog", "New Relic", "Splunk", "Jaeger", "Zipkin"]
}

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header { text-align: center; color: #2E86AB; font-size: 2.5rem; font-weight: bold; margin-bottom: 2rem; }
    .form-container { background-color: #f8f9fa; padding: 2rem; border-radius: 10px; border: 1px solid #dee2e6; margin: 1rem 0; }
    .success-message { background-color: #d4edda; color: #155724; padding: 1rem; border-radius: 5px; border: 1px solid #c3e6cb; margin: 1rem 0; }
    .error-message { background-color: #f8d7da; color: #721c24; padding: 1rem; border-radius: 5px; border: 1px solid #f5c6cb; margin: 1rem 0; }
    .field-label { font-weight: bold; color: #495057; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

def validate_employee_id(employee_id):
    return bool(re.match(r'^TM\d{5}$', employee_id))

def validate_email(email):
    return email.endswith('@gmail.com') and '@' in email

def validate_phone(phone):
    return bool(re.match(r'^\d{10}$', phone))

def validate_date(selected_date):
    return selected_date <= date.today()

def load_existing_data():
    if os.path.exists('employees_data.json'):
        try:
            with open('employees_data.json', 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_employee_data(employee_data):
    try:
        existing_data = load_existing_data()
        existing_data.append(employee_data)
        with open('employees_data.json', 'w') as f:
            json.dump(existing_data, f, indent=4, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def check_duplicate_employee_id(employee_id):
    existing_data = load_existing_data()
    return any(emp.get('employee_id') == employee_id for emp in existing_data)

def load_project_allocations():
    if os.path.exists('project_allocations.json'):
        try:
            with open('project_allocations.json', 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_project_allocation(allocation_data):
    try:
        existing_data = load_project_allocations()
        existing_data.append(allocation_data)
        with open('project_allocations.json', 'w') as f:
            json.dump(existing_data, f, indent=4, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving allocation data: {str(e)}")
        return False

def save_bulk_project_allocations(allocations_list):
    try:
        existing_data = load_project_allocations()
        existing_data.extend(allocations_list)
        with open('project_allocations.json', 'w') as f:
            json.dump(existing_data, f, indent=4, default=str)
        return True
    except Exception as e:
        st.error(f"Error saving bulk allocation data: {str(e)}")
        return False

def get_employee_total_allocation(employee_id):
    allocations = load_project_allocations()
    total = 0
    for alloc in allocations:
        if alloc.get('employee_id') == employee_id:
            total += alloc.get('allocation', 0)
    return total

def make_pandas_gemini_agent(
    json_path: str,
    gemini_model: str = "gemini-1.5-flash",
    temperature: float = 0.0,
    verbose: bool = True
):
    # 1. Load your JSON data into a DataFrame
    df = pd.read_json(json_path)
    # 2. Setup Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model=gemini_model,
        google_api_key=st.secrets["GEMINI_API_KEY"],
        temperature=temperature,
    )
    # 3. Create pandas agent (no extra kwargs here!)
    pandas_agent = create_pandas_dataframe_agent(
        llm=llm,
        df=df,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        include_df_in_prompt=True,
        number_of_head_rows=5,
        allow_dangerous_code=True,  # executes arbitrary code!
    )
    # 4. Wrap in AgentExecutor so we can handle parsing errors
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=pandas_agent.agent,
        tools=pandas_agent.tools,
        verbose=verbose,
        handle_parsing_errors=True,  #
        max_iterations=10,
        return_intermediate_steps=True,
    )
    return agent_executor

# --- Page Functions ---

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.session_state.page = "admin"
            st.rerun()
        elif username == "employee" and password == "employee":
            st.session_state.logged_in = True
            st.session_state.role = "employee"
            st.session_state.page = "employee"
            st.rerun()
        else:
            st.error("Invalid username or password")

def employee_page():
    st.header("Add New Employee")
    with st.container():
        # st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("### 📝 Enter Employee Details")
        st.markdown("*All fields are required")
        col1, col2 = st.columns(2)
        with col1:
            employee_id = st.text_input("Employee ID *", placeholder="TM01418", help="Format: TM followed by 5 digits", key="emp_id")
            name = st.text_input("Full Name *", placeholder="John Doe", key="emp_name")
            email = st.text_input("Email Address *", placeholder="john.doe@gmail.com", key="emp_email")
            phone = st.text_input("Phone Number *", placeholder="9876543210", help="10-digit Indian phone number", key="emp_phone")
            date_of_joining = st.date_input("Date of Joining *", max_value=date.today(), help="Cannot be in the future", key="emp_date")
        with col2:
            designation = st.selectbox("Designation *", options=["", "Backend Developer", "Frontend Developer", "AI/ML/Data Scientist", "DevOps Engineer"], help="Select employee's technical role", key="emp_designation")
            department = st.selectbox("Department *", options=["", "Software Engineering", "FinOps", "AI & Gen AI Solutions"], help="Select employee's department", key="emp_department")
            if designation and designation in ROLE_SKILLS:
                available_skills = ROLE_SKILLS[designation]
                selected_skills = st.multiselect(f"Skills * ({len(available_skills)} available)", options=available_skills, help=f"Select skills for {designation}", placeholder="Search and select skills...", key="emp_skills")
                if selected_skills:
                    st.caption(f"✅ {len(selected_skills)} skills selected")
            else:
                if designation == "":
                    selected_skills = st.multiselect("Skills *", options=[], help="Please select designation first", placeholder="Select designation first...", disabled=True, key="emp_skills_disabled")
                    st.caption("⚠️ Select designation to see skills")
                else:
                    selected_skills = st.multiselect("Skills *", options=[], help="No skills available for this designation", placeholder="No skills available", disabled=True, key="emp_skills_error")
                    st.caption("❌ No skills for this designation")
            location = st.selectbox("Location *", options=["", "Hyderabad", "Kolkata", "Hubli", "Gurgaon"], help="Select work location", key="emp_location")
            experience_years = st.number_input("Years of Experience *", min_value=0.0, max_value=50.0, step=0.5, help="Total years of professional experience", key="emp_experience")
        if st.button("💾 Save Employee Data", type="primary", use_container_width=True):
            errors = []
            if not employee_id: errors.append("Employee ID is required")
            elif not validate_employee_id(employee_id): errors.append("Employee ID must be in format 'TM' followed by 5 digits (e.g., TM01418)")
            elif check_duplicate_employee_id(employee_id): errors.append("Employee ID already exists")
            if not name.strip(): errors.append("Name is required")
            if not email: errors.append("Email is required")
            elif not validate_email(email): errors.append("Email must end with @gmail.com")
            if not phone: errors.append("Phone number is required")
            elif not validate_phone(phone): errors.append("Phone number must be exactly 10 digits")
            if not designation: errors.append("Designation is required")
            if not department: errors.append("Department is required")
            if not location: errors.append("Location is required")
            if not validate_date(date_of_joining): errors.append("Date of joining cannot be in the future")
            if experience_years <= 0: errors.append("Experience years must be greater than 0")
            if not selected_skills or len(selected_skills) == 0: errors.append("At least one skill must be selected")
            elif len(selected_skills) > 20: errors.append("Maximum 20 skills can be selected")
            if errors:
                st.markdown('<div class="error-message">', unsafe_allow_html=True)
                st.error("❌ Please fix the following errors:")
                for error in errors:
                    st.write(f"• {error}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                employee_data = { "employee_id": employee_id, "name": name.strip(), "email": email.lower(), "phone": phone, "designation": designation, "department": department, "date_of_joining": date_of_joining.isoformat(), "location": location, "experience_years": experience_years, "skills": selected_skills, "skills_count": len(selected_skills), "created_at": datetime.now().isoformat() }
                if save_employee_data(employee_data):
                    st.markdown('<div class="success-message">', unsafe_allow_html=True)
                    st.success(f"✅ Employee data for **{employee_data['name']}** (`{employee_id}`) saved successfully!")
                else:
                    st.error("❌ Failed to save employee data")
        st.markdown('</div>', unsafe_allow_html=True)


def admin_page():
    st.header("Admin Dashboard")
    
    existing_data = load_existing_data()
    
    if not existing_data:
        st.info("No employee data to display yet.")
        return

    df = pd.DataFrame(existing_data)

    # --- Project Allocation ---
    # st.subheader("Project Allocation")
    with st.container():
        # st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("### Allocate Project to Employee")
        
        employee_list = [f"{emp['name']} ({emp['employee_id']})" for emp in existing_data]
        selected_employee_str = st.selectbox("Search Employee by Name or ID", options=[""] + employee_list)
        
        if selected_employee_str:
            employee_id = selected_employee_str.split('(')[-1].replace(')','')
            project_name = st.text_input("Project Name")
            project_start_date = st.date_input("Project Start Date", max_value=date.today())
            project_end_date = st.date_input("Project End Date", min_value=project_start_date)
            allocation = st.number_input("Allocation Percentage", min_value=1, max_value=100, step=1)

            if st.button("💾 Save Allocation", type="primary", use_container_width=True):
                if not project_name.strip():
                    st.error("Project name is required")
                else:
                    current_allocation = get_employee_total_allocation(employee_id)
                    if current_allocation + allocation > 100:
                        st.error(f"Cannot allocate. Employee {employee_id} is already allocated {current_allocation}%. This allocation would exceed 100%.")
                    else:
                        employee_details = next((emp for emp in existing_data if emp['employee_id'] == employee_id), None)
                        if employee_details:
                            allocation_data = employee_details.copy()
                            allocation_data.update({
                                "project_name": project_name.strip(),
                                "start_date": project_start_date.isoformat(),
                                "end_date": project_end_date.isoformat(),
                                "allocation": allocation,
                                "allocated_at": datetime.now().isoformat()
                            })
                            if save_project_allocation(allocation_data):
                                st.success(f"Project '{project_name}' allocated to {selected_employee_str}")
                            else:
                                st.error("Failed to save project allocation")
                        else:
                            st.error("Could not find employee details to save.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Bulk Project Allocation ---
    st.subheader("Bulk Project Allocation")
    with st.container():
        # st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("### Upload a CSV for Bulk Allocation")

        template_df = pd.DataFrame({
            'project_name': ['Example Project'],
            'start_date': [date.today().isoformat()],
            'end_date': [date.today().isoformat()],
            'allocation': [50],
            'employee_id': ['TM00001']
        })
        template_csv = template_df.to_csv(index=False)
        st.download_button("📥 Download Template CSV", template_csv, "allocation_template.csv", "text/csv")

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            try:
                upload_df = pd.read_csv(uploaded_file)
                required_columns = ['project_name', 'start_date', 'end_date', 'allocation', 'employee_id']
                if not all(col in upload_df.columns for col in required_columns):
                    st.error(f"CSV must contain the following columns: {required_columns}")
                else:
                    new_allocations = []
                    errors = []
                    # Keep track of allocations within the uploaded file to handle multiple entries for the same employee
                    in_file_allocations = {}

                    for index, row in upload_df.iterrows():
                        employee_id = row['employee_id']
                        allocation_value = row['allocation']

                        # Get allocation already in the file for this employee
                        in_file_total = in_file_allocations.get(employee_id, 0)
                        # Get allocation from the saved data
                        existing_total = get_employee_total_allocation(employee_id)

                        if existing_total + in_file_total + allocation_value > 100:
                            errors.append(f"Row {index+2}: Cannot allocate {allocation_value}% to employee {employee_id}. Total allocation would exceed 100%.")
                            continue

                        employee_details = next((emp for emp in existing_data if emp['employee_id'] == employee_id), None)
                        if employee_details:
                            allocation_data = employee_details.copy()
                            allocation_data.update({
                                "project_name": row['project_name'],
                                "start_date": row['start_date'],
                                "end_date": row['end_date'],
                                "allocation": allocation_value,
                                "allocated_at": datetime.now().isoformat()
                            })
                            new_allocations.append(allocation_data)
                            # Update the in-file allocation total for this employee
                            in_file_allocations[employee_id] = in_file_total + allocation_value
                        else:
                            errors.append(f"Row {index+2}: Employee with ID '{employee_id}' not found.")
                    
                    if errors:
                        st.error("Errors found in the uploaded file:")
                        for error in errors:
                            st.write(error)
                    
                    if new_allocations:
                        if save_bulk_project_allocations(new_allocations):
                            st.success(f"Successfully allocated {len(new_allocations)} projects.")
                        else:
                            st.error("Failed to save bulk allocations.")

            except Exception as e:
                st.error(f"An error occurred while processing the file: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- View Project Allocations ---
    with st.expander("📂 View Project Allocations", expanded=False):
        project_allocations = load_project_allocations()
        if not project_allocations:
            st.info("No project allocations to display yet.")
        else:
            st.markdown(f"**Total Allocations: {len(project_allocations)}**")
            allocations_df = pd.DataFrame(project_allocations)
            st.dataframe(allocations_df, use_container_width=True)

    # --- Employee Data Table ---
    with st.expander("📊 View All Employees", expanded=False):
        st.markdown(f"**Total Employees: {len(existing_data)}**")
        df_data = []
        for emp in existing_data:
            skills_display = ""
            if emp.get("skills"):
                skills_count = len(emp["skills"])
                if skills_count <= 3:
                    skills_display = ", ".join(emp["skills"])
                else:
                    skills_display = f"{', '.join(emp['skills'][:2])}... (+{skills_count-2} more)"
            df_data.append({ "Employee ID": emp.get("employee_id", ""), "Name": emp.get("name", ""), "Designation": emp.get("designation", ""), "Department": emp.get("department", ""), "Location": emp.get("location", ""), "Experience": f"{emp.get('experience_years', 0)} years", "Skills": skills_display, "Skills Count": len(emp.get("skills", [])) })
        if df_data:
            df_display = pd.DataFrame(df_data)
            st.dataframe(df_display, use_container_width=True)
            json_str = json.dumps(existing_data, indent=2, default=str)
            st.download_button(label="📥 Download Employee Data (JSON)", data=json_str, file_name=f"employees_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", mime="application/json")

    st.markdown("---")

    # --- Natural Language Project Allocation ---
    st.subheader("Natural Language Project Allocation")
    with st.container():
        # st.markdown('<div class="form-container">', unsafe_allow_html=True)
        st.markdown("### Allocate Project using Natural Language")
        st.info("Example: 'allocate Abhinandan to Wellora project from 2025-09-17 to 2025-09-20 with 50% allocation'")

        nl_allocation_query = st.text_input("Enter your allocation request:", key="nl_allocation_query")

        if st.button("Allocate Project (NLP)", key="nl_allocate_button"):
            if not nl_allocation_query:
                st.warning("Please enter an allocation request.")
                return

            with st.spinner('Processing natural language allocation...'):
                response_json = get_gemini_response(nl_allocation_query)

                if not response_json:
                    return

                intent = response_json.get("intent")
                entities = response_json.get("entities") or {}

                st.subheader("Allocation Result")

                if intent == "allocate_project":
                    employee_name_query = entities.get("employee_name")
                    project_name = entities.get("project_name")
                    start_date_str = entities.get("start_date")
                    end_date_str = entities.get("end_date")
                    allocation_val = entities.get("allocation")

                    errors = []
                    if not employee_name_query: errors.append("Employee name is missing.")
                    if not project_name: errors.append("Project name is missing.")
                    if not start_date_str: errors.append("Start date is missing.")
                    if not end_date_str: errors.append("End date is missing.")
                    if allocation_val is None: errors.append("Allocation percentage is missing.")

                    found_employee = None
                    if employee_name_query:
                        all_employees = load_existing_data()
                        for emp in all_employees:
                            if emp['name'].lower() in employee_name_query.lower() or employee_name_query.lower() in emp['name'].lower():
                                found_employee = emp
                                break
                        if not found_employee:
                            errors.append(f"Employee matching '{employee_name_query}' not found.")

                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        errors.append("Start date format is invalid. Please use YYYY-MM-DD.")
                        start_date = None
                    
                    try:
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except (ValueError, TypeError):
                        errors.append("End date format is invalid. Please use YYYY-MM-DD.")
                        end_date = None

                    if start_date and end_date and start_date > end_date:
                        errors.append("Start date cannot be after end date.")
                    
                    if allocation_val is not None and (not isinstance(allocation_val, (int, float)) or not (1 <= allocation_val <= 100)):
                        errors.append("Allocation percentage must be a number between 1 and 100.")
                    
                    if not errors and found_employee:
                        current_allocation = get_employee_total_allocation(found_employee['employee_id'])
                        if current_allocation + allocation_val > 100:
                            errors.append(f"Cannot allocate. {found_employee['name']} is already allocated {current_allocation}%. This allocation would exceed 100%.")

                    if errors:
                        st.error("Could not allocate project due to the following issues:")
                        for err in errors:
                            st.write(f"- {err}")
                    else:
                        allocation_data = found_employee.copy()
                        allocation_data.update({
                            "project_name": project_name,
                            "start_date": start_date.isoformat(),
                            "end_date": end_date.isoformat(),
                            "allocation": allocation_val,
                            "allocated_at": datetime.now().isoformat()
                        })
                        if save_project_allocation(allocation_data):
                            st.success(f"Successfully allocated **{project_name}** to **{found_employee['name']}** with **{allocation_val}%** allocation.")
                        else:
                            st.error("Failed to save project allocation.")
                elif intent == "other":
                    st.error("Sorry, I could not understand your request as an allocation command. Please try phrasing it differently.")
                else:
                    st.error("Sorry, I could not understand your request as an allocation command. Please try phrasing it differently.")

                # --- Display LLM Interpretation for Transparency ---
                with st.expander("Show LLM Interpretation"): 
                    st.write(f"**Recognized Intent:** `{intent}`")
                    st.write("**Raw LLM Response:**")
                    st.json(response_json)
        st.markdown('</div>', unsafe_allow_html=True)

def get_gemini_response(query):
    try:
        # It's recommended to use st.secrets for API keys
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        meta_prompt = f"""You are an expert query-parsing assistant for an employee management system. Your task is to analyze the user's prompt and convert it into a structured JSON object.

Your response MUST be only the JSON object and nothing else.

Here are the possible user intents and the entities you must extract for each:

1.  **Intent: `search_candidate`**
    *   Triggered when the user is looking for an employee to hire or allocate. Examples: "Find me a developer", "I need a devops engineer with AWS for 50%"
    *   **Entities to extract:** `designation` (string, must be one of ["Backend Developer", "Frontend Developer", "AI/ML/Data Scientist", "DevOps Engineer"]), `skills` (array of strings), `allocation_needed` (integer).

2.  **Intent: `find_employee_projects`**
    *   Triggered when the user wants to know which projects an employee is on. Examples: "what projects is X working on?", "show me X's projects"
    *   **Entities to extract:** `employee_name` (string).

3.  **Intent: `get_employee_allocation`**
    *   Triggered when the user asks for the total allocation of an employee. Examples: "what is X's allocation?", "how much is X allocated?"
    *   **Entities to extract:** `employee_name` (string).

4.  **Intent: `get_employee_skills`**
    *   Triggered when the user asks for an employee's skills. Examples: "what are X's skills?", "show me the skills for X"
    *   **Entities to extract:** `employee_name` (string).

5.  **Intent: `get_employee_phone`**
    *   Triggered when the user asks for an employee's phone number. Examples: "what is X's phone number?", "find the phone for X"
    *   **Entities to extract:** `employee_name` (string).

6.  **Intent: `get_employee_department`**
    *   Triggered when the user asks for an employee's department. Examples: "which department is X in?", "what is X's department?"
    *   **Entities to extract:** `employee_name` (string).

7.  **Intent: `get_employee_designation`**
    *   Triggered when the user asks for an employee's designation. Examples: "what is X's designation?", "what is X's role?"
    *   **Entities to extract:** `employee_name` (string).

8.  **Intent: `get_employee_id`**
    *   Triggered when the user asks for an employee's ID. Examples: "what is X's employee ID?", "employee id for X"
    *   **Entities to extract:** `employee_name` (string).

9.  **Intent: `get_employee_experience`**
    *   Triggered when the user asks for an employee's experience. Examples: "how much experience does X have?", "what is X's experience?"
    *   **Entities to extract:** `employee_name` (string).

10. **Intent: `get_employee_email`**
    *   Triggered when the user asks for an employee's email. Examples: "what is the email for X?", "email address of X", "find X's email"
    *   **Entities to extract:** `employee_name` (string).

11. **Intent: `get_employee_doj`**
    *   Triggered when the user asks for an employee's date of joining. Examples: "when did X join?", "what is the joining date for X?"
    *   **Entities to extract:** `employee_name` (string).

12. **Intent: `get_employee_location`**
    *   Triggered when the user asks for an employee's location. Examples: "where is X located?", "X's location", "location of X"
    *   **Entities to extract:** `employee_name` (string).

13. **Intent: `allocate_project`**
    *   Triggered when the user wants to allocate an employee to a project. Examples: "allocate X to Project Alpha from YYYY-MM-DD to YYYY-MM-DD with Z% allocation", "assign X to project Beta, start 2025-01-01 end 2025-06-30, 50%"
    *   **Entities to extract:** `employee_name` (string), `project_name` (string), `start_date` (string, YYYY-MM-DD format), `end_date` (string, YYYY-MM-DD format), `allocation` (integer).

14. **Intent: `get_employee_details`**
    *   Triggered when the user asks for all details of an employee. Examples: "give me the details of X", "information about X", "show me everything for X"
    *   **Entities to extract:** `employee_name` (string).

15. **Intent: `other`**
    *   Triggered when the user's query does not match any of the other intents. Examples: "hello", "how are you", "what is the weather today?"
    *   **Entities to extract:** None.

---
**User's Prompt:** "{query}"
---

**Your JSON Response:**"""

        response = model.generate_content(meta_prompt)
        # Clean up the response to get a valid JSON string
        json_response_str = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_response_str)

    except Exception as e:
        st.error(f"An error occurred while contacting the AI model: {e}")
        st.info("Please ensure your Gemini API key is configured correctly in .streamlit/secrets.toml")
        return None

def intent_based_search_page():
    st.header("Intent-Based Search")
    st.info("Ask questions like: 'Find a DevOps engineer with AWS and 50% allocation' or 'What projects is Jane Doe working on?'")

    query = st.text_input("Your question:", key="nlp_query")

    if st.button("Search", key="nlp_search_button"):
        if not query:
            st.warning("Please enter a question.")
            return

        with st.spinner('Searching and processing...'):
            response_json = get_gemini_response(query)

            if not response_json:
                return

            intent = response_json.get("intent")
            entities = response_json.get("entities") or {}

            st.subheader("Results")

            # Define intents that require looking up a specific employee
            employee_lookup_intents = [
                "get_employee_allocation", "find_employee_projects", "get_employee_skills",
                "get_employee_phone", "get_employee_department", "get_employee_designation",
                "get_employee_id", "get_employee_experience", "get_employee_email",
                "get_employee_doj", "get_employee_location", "get_employee_details"
            ]

            if intent in employee_lookup_intents:
                employee_name_query = entities.get("employee_name")
                if not employee_name_query:
                    st.error("Could not identify an employee name in your query for this type of question.")
                    return

                all_employees = load_existing_data()
                found_employee = None
                for emp in all_employees:
                    if emp['name'].lower() in employee_name_query.lower() or employee_name_query.lower() in emp['name'].lower():
                        found_employee = emp
                        break
                
                if not found_employee:
                    st.error(f"Employee matching '{employee_name_query}' not found.")
                    return

                # --- Execute the specific lookup intent ---
                if intent == "get_employee_allocation":
                    total_allocation = get_employee_total_allocation(found_employee['employee_id'])
                    st.success(f"**{found_employee['name']}** has a total allocation of **{total_allocation}%**.")

                elif intent == "find_employee_projects":
                    project_allocations = load_project_allocations()
                    employee_projects = [alloc for alloc in project_allocations if alloc['employee_id'] == found_employee['employee_id']]
                    if not employee_projects:
                        st.success(f"**{found_employee['name']}** is not currently allocated to any projects.")
                    else:
                        st.success(f"**{found_employee['name']}** is working on the following projects:")
                        for proj in employee_projects:
                            st.write(f"- **{proj['project_name']}** (Allocation: {proj['allocation']}%)")

                elif intent == "get_employee_skills":
                    skills = found_employee.get('skills', [])
                    if skills:
                        st.success(f"**{found_employee['name']}** has the following skills:")
                        st.write(", ".join(skills))
                    else:
                        st.info(f"No skills are listed for **{found_employee['name']}**.")

                elif intent == "get_employee_phone":
                    st.success(f"The phone number for **{found_employee['name']}** is **{found_employee.get('phone')}**.")

                elif intent == "get_employee_department":
                    st.success(f"**{found_employee['name']}** works in the **{found_employee.get('department')}** department.")

                elif intent == "get_employee_designation":
                    st.success(f"The designation of **{found_employee['name']}** is **{found_employee.get('designation')}**.")

                elif intent == "get_employee_id":
                    st.success(f"The Employee ID for **{found_employee['name']}** is **{found_employee.get('employee_id')}**.")

                elif intent == "get_employee_experience":
                    experience = found_employee.get('experience_years', 0)
                    st.success(f"**{found_employee['name']}** has **{experience}** years of experience.")

                elif intent == "get_employee_email":
                    st.success(f"The email for **{found_employee['name']}** is **{found_employee.get('email')}**.")

                elif intent == "get_employee_doj":
                    st.success(f"**{found_employee['name']}** joined on **{found_employee.get('date_of_joining')}**.")

                elif intent == "get_employee_location":
                    location = found_employee.get('location')
                    st.success(f"**{found_employee['name']}** is located in **{location}**.")

                elif intent == "get_employee_details":
                    st.success(f"Showing all details for **{found_employee['name']}**:")
                    
                    # Display employee details in a tabular format
                    st.subheader("Employee Information")
                    employee_df = pd.DataFrame([found_employee])
                    st.dataframe(employee_df)

                    # Display project allocations
                    project_allocations = load_project_allocations()
                    employee_projects = [alloc for alloc in project_allocations if alloc['employee_id'] == found_employee['employee_id']]
                    
                    if not employee_projects:
                        st.info(f"**{found_employee['name']}** is not currently allocated to any projects.")
                    else:
                        st.subheader("Project Allocations")
                        st.dataframe(pd.DataFrame(employee_projects))

            elif intent == "search_candidate":
                designation = entities.get("designation")
                required_skills = set(entities.get("skills", []))
                allocation_needed = entities.get("allocation_needed", 0)

                if not designation:
                    st.error("Please specify a designation for the candidate search.")
                    return

                all_employees = load_existing_data()
                candidates = [emp for emp in all_employees if emp['designation'] == designation]

                if not candidates:
                    st.warning(f"No employees found with the designation: {designation}")
                    return

                ranked_candidates = []
                for cand in candidates:
                    available_allocation = 100 - get_employee_total_allocation(cand['employee_id'])
                    if available_allocation >= allocation_needed:
                        skill_match_score = len(set(cand.get('skills', [])) & required_skills)
                        if not required_skills or skill_match_score > 0:
                            ranked_candidates.append({
                                "Name": cand['name'],
                                "ID": cand['employee_id'],
                                "Skill Match": f"{skill_match_score} / {len(required_skills)}",
                                "Available Allocation": f"{available_allocation}%",
                                "score": skill_match_score
                            })
                
                if not ranked_candidates:
                    st.info("No candidates found matching all criteria (designation, skills, and required allocation).")
                    return

                sorted_candidates = sorted(ranked_candidates, key=lambda x: x['score'], reverse=True)
                
                for cand in sorted_candidates:
                    del cand['score']

                st.dataframe(pd.DataFrame(sorted_candidates))

            # --- Display LLM Interpretation for Transparency ---
            with st.expander("Show LLM Interpretation"): # Moved outside the else block
                st.write(f"**Recognized Intent:** `{intent}`")
                st.write("**Raw LLM Response:**")
                st.json(response_json)

            # The final else block for unhandled intents
            if intent == "other" or (intent not in employee_lookup_intents and intent != "search_candidate"):
                st.error("Sorry, I could not understand your request. Please try phrasing it differently.")
                # st.info("Here is the raw response from the AI model for debugging:")
                # st.json(response_json)

def agentic_search_page():
    st.header("Agentic Search")
    st.info("Ask questions about your data. For example: 'what is the total allocation for the wellora?'")
    st.warning("**Warning:** This feature uses an agent that can execute arbitrary code. Use with caution.")

    query = st.text_input("Your question:", key="agentic_query")

    if st.button("Search", key="agentic_search_button"):
        if not query:
            st.warning("Please enter a question.")
            return

        with st.spinner('Searching and processing...'):
            try:
                agent = make_pandas_gemini_agent("project_allocations.json")
                result = agent.invoke({"input": query})
                st.write(result.get("output"))
                with st.expander("Show Agentic Response"):
                    st.write(result.get("intermediate_steps"))
            except Exception as e:
                st.error(f"An error occurred: {e}")


# --- Main App Logic ---

def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.page = "login"

    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.role == "admin":
            st.sidebar.title(f"Welcome, {st.session_state.role}")
            page = st.sidebar.radio("Go to", ["Employee", "Admin", "Intent-Based Search", "Agentic Search"])

            # Display Key Metrics in the sidebar
            sidebar_data = load_existing_data()
            if sidebar_data:
                sidebar_df = pd.DataFrame(sidebar_data)
                st.sidebar.markdown("---")
                st.sidebar.subheader("Key Metrics")
                st.sidebar.metric("Total Employees", len(sidebar_df))
                st.sidebar.metric("Number of Departments", sidebar_df['department'].nunique())
                st.sidebar.metric("Number of Designations", sidebar_df['designation'].nunique())

            if page == "Employee":
                employee_page()
            elif page == "Admin":
                admin_page()
            elif page == "Intent-Based Search":
                intent_based_search_page()
            elif page == "Agentic Search":
                agentic_search_page()

            if st.sidebar.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.page = "login"
                st.rerun()
        elif st.session_state.role == "employee":
            st.sidebar.title(f"Welcome, {st.session_state.role}")
            employee_page()
            if st.sidebar.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.page = "login"
                st.rerun()

if __name__ == "__main__":
    main()
