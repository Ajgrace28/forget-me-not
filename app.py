## Main streamlit web app
import streamlit as st
import database.db as db
import datetime
import time
from PIL import Image
import ai_logic.ai_service as ai
#img = Image.open("pageicon.png") ## Page icon for the web app (not working)

st.set_page_config(page_title="Forget Me Not",layout="wide")
st.markdown( ## CSS to reduce padding while keeping collapse button visible
    "<style>.stSidebar [data-testid='stSidebarUserContent'] { padding-top: 0; }</style>",
    unsafe_allow_html=True
)
## Header ##
col1, col2 = st.columns([2, 0.5])
with col2:
    st.image("pageicon.png", width=100)  # Larger logo in main area
with col1:
    st.title("Forget Me Not - Your AI Academic Student Assistant")
    st.caption("Organize your study schedule, track tasks, and get AI-powered insights to boost your academic productivity.")
    
st.markdown("Get started by adding a new task to your dashboard. "
    "Create a new task and manage your schedules effectively")
st.badge("Powered by Gemini AI", color="primary")
st.divider()

##Task Priority Level Settings##
#Defining task priority thresholds
taskPriority_thresholds = {
    "Very High": 14,  # Warn when due date is within 2 weeks
    "High": 7,        # Warn when due date is within 1 week
    "Medium": 3,      # Warn when due date is within 3 days
    "Low": 1         # Warn when due date is within 1 day
}

taskPriority_colors = {
    "Very High": "red",
    "High": "orange",
    "Medium": "blue",
    "Low": "green"
}
taskPriority_options = list(taskPriority_thresholds.keys())

##Dialog for Editing tasks##
@st.dialog("Edit Task")
def edit_task_dialog(task):
    # Pre-fill fields with existing task data
    new_name = st.text_input("Task Name", value=task['name'],help="Edit the name of your task")
    new_desc = st.text_area("Task Description", value=task['description'])
    
    # Handle category slider index finding
    options = ["Personal study", "Exam prep", "Assignment", "Coursework", "Project", "Other"]
    try:
        default_idx = options.index(task['task_category'])
    except ValueError:
        default_idx = 5 # Default to "Other" if mismatch
        
    new_category = st.select_slider("Select Category", options=options, value=options[default_idx])

    ##Priority Selection for task editing##
    current_priority = task.get('task_priority', 'Medium')  # Default to 'Medium' if not found
    try:
        p_idx = taskPriority_options.index(current_priority)
    except ValueError:
        p_idx = 2 # Default to "Medium" if mismatch
    new_priority = st.selectbox("Set Priority Level", options=taskPriority_options, index=p_idx, help="Set the priority level based on the task timeline and importance")
    
    new_due = st.date_input("Due Date", value=task['due_date'])
    
    if st.button("Save Changes", type="primary"):

        ## AI Validation (The Gatekeeper)##
        with st.spinner("Checking task relevance..."):
            is_valid = ai.validate_academic_task(new_name, new_desc, new_category)
        if not is_valid:
            st.error("Hold up! This update doesn't seem academically relevant. Please keep it school-related!")
            time.sleep(4)
            return
        
        db.edit_task(task['id'], new_name, new_category, new_priority, new_due, new_desc) ##This updates the task in the database with new values
        st.toast("✅ Task updated!")
        time.sleep(2)
        st.rerun()

db.init_db() ## Ensure DB is initialized before any operations
##Function for Dashboard page##
def dashboard_page():
    st.title("Dashboard")
    st.caption("Your task overview at a glance. Track your progress and stay organized with Forget Me Not.") 
    st.divider()
    
    tasks_df = db.get_tasks()
    if not tasks_df.empty:
        total_tasks = len(tasks_df)
        completed_tasks = len(tasks_df[tasks_df["status"] == "Completed"])
        pending_tasks = len(tasks_df[tasks_df["status"] == "Pending"])
        overdue_tasks = len(
            tasks_df[
                (tasks_df["due_date"] < datetime.date.today()) &
                (tasks_df["status"] == "Pending")
            ]
        )

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Tasks", total_tasks)
        col2.metric("Completed", completed_tasks)
        col3.metric("Pending", pending_tasks)
        col4.metric("Overdue", overdue_tasks)

        #To show quick notifications in dashboard
        if overdue_tasks > 0:
            # Check if the count is exactly 1 to determine singular or plural
            task_word = "task" if overdue_tasks == 1 else "tasks"
            st.error(f"🚨 You have {overdue_tasks} overdue {task_word}! Please check your notifications.")
        elif pending_tasks > 0:
            # Check if the count is exactly 1 to determine singular or plural
            task_word = "task" if pending_tasks == 1 else "tasks"
            st.warning(f"⚠️ You have {pending_tasks} pending {task_word}. Stay on track!")
        else:
            st.success("Great job! You have no pending tasks.")

    else:
        st.info("No tasks available yet.")
    st.divider()
    
##For Creating New task##
    @st.dialog("Enter Task Details")
    def add_task(details):
        task_name = st.text_input("Task Name", 
        placeholder="e.g., Study for Math Exam", help="Give your task a clear and descriptive name")
        task_desc = st.text_area("Task Description",
        placeholder="e.g., Covers chapters 1 to 5. Focus heavily on binary trees.", help="Provide more details about the task to get abetter AI study plans")

        task_category = st.select_slider(
            "Select relevant task category",
            options=[
                "Personal study",
                "Exam prep",
                "Assignment",
                "Coursework",
                "Project",
                "Other"
            ]
        )
        st.write(f"Selected category: {task_category}") ##shows selected task category
        task_priority = st.selectbox("Set Priority Level", options=taskPriority_options, help="Set the priority level based on the task timeline and importance")

        due_date = st.date_input("Due Date", min_value=datetime.date.today())

        if st.button("Add task", type="primary"):
            if not task_name or not task_desc:
                st.error("Please fill in all the fields.")
                return
            
            ##AI Validation (The Gatekeeper)##
            with st.spinner("Validating task with AI..."):
                is_valid = ai.validate_academic_task(task_name, task_desc, task_category)
            if not is_valid:
                st.error("Hold up! This task doesn't seem like an academic or productivity-related task. Please keep distractions out of your study planner and try again!")
                time.sleep(4)
                return

            db.add_task( ##this saves created task to the database
                name=task_name,
                task_category=task_category,
                task_priority=task_priority,
                due_date=due_date,
                description=task_desc,
                status="Pending"
            )
            st.toast("✅ Task added successfully!")
            time.sleep(2)
            st.rerun()

    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    with col2:
        if st.button("Create new task", type="primary", use_container_width=True):
            add_task(details=True)
    

##Function for All Task Page##
def all_tasks_page():
    st.title("All Tasks")
    st.caption("View and manage all your tasks in one place. Track, edit, or delete tasks as needed.")
    
    # Filter Controls
    filter_status = st.radio("Show:", ["All", "Pending", "Completed"], horizontal=True)

    tasks_df = db.get_tasks()

    if tasks_df.empty:
        st.info("No tasks found.")
        return

    # Apply Filter
    if filter_status == "Pending":
        tasks_df = tasks_df[tasks_df["status"] == "Pending"]
    elif filter_status == "Completed":
        tasks_df = tasks_df[tasks_df["status"] == "Completed"]
 
    # Display Tasks
    for index, task in tasks_df.iterrows():
        # Visual Styling based on status
        border_color = True
        days_left = (task['due_date'] - datetime.date.today()).days  # Always computed
        if task['status'] == 'Completed':
            priority_color = "green"
        else:
            # Using a simple priority color logic
            priority_color = "red" if days_left < 3 else "blue"  ##Red for urgent tasks
 
        with st.container(border=border_color):
            # Columns: Checkbox, Details, Edit, Delete
            c1, c2, c3, c4 = st.columns([0.5, 4, 0.7, 0.7])
            
            with c1:
                # Checkbox for status
                is_completed = task["status"] == "Completed"
                if st.checkbox("Mark as complete", value=is_completed, key=f"check_{task['id']}", label_visibility="collapsed"):
                    if not is_completed:
                        db.update_task_status(task['id'], "Completed")
                        st.balloons() #Celebratory balloons for completing a task
                        st.toast("Task completed successfully!") #To show a popup message
                        time.sleep(1)  # Brief pause to show toast before rerunning
                        st.rerun()
                else:
                    if is_completed:
                        db.update_task_status(task['id'], "Pending")
                        st.rerun()
 
            with c2:
                # Task Details
                st.markdown(f"**:{priority_color}[{task['name']}]**")
                if task['status'] == 'Completed':
                    time_label = "Completed"
                elif days_left < 0:
                    time_label = f"⚠️ {abs(days_left)} {'day' if abs(days_left) == 1 else 'days'} overdue"
                elif days_left == 0:
                    time_label = "⏰ Due today"
                else:
                    time_label = f"⏳ {days_left} {'day' if days_left == 1 else 'days'} left"
                st.caption(f"{task['task_category']} • Due: {task['due_date']} • {time_label}")
                priority = task.get('task_priority', 'Medium')
                st.badge(f"{priority} Priority", color=priority_color)
                if task['description']:
                    with st.expander("Description"):
                        st.write(task['description'])
                
            with c3:
                # Edit Button
                if st.button("✏️ Edit", key=f"edit_{task['id']}", help="Edit Task"):
                    edit_task_dialog(task)
 
            with c4:
                # Delete Button
                if st.button("🗑️ Delete", key=f"del_{task['id']}", help="Delete Task"):
                    db.delete_task(task['id'])
                    st.toast("Task deleted successfully!")
                    st.rerun()
    
##AI Study Plan Generation##
            #st.divider()
        
            ai_status = str(task['ai_response']).strip().lower()
            
            ##Scenario A: AI Plan already exists in the database##
            if ai_status != 'pending' and ai_status != 'nan' and ai_status != 'none':
                with st.expander("View AI Study Plan"):
                    st.markdown(task['ai_response'])
                    
                    # Allow regeneration if task is modified
                    if st.button("Regenerate Plan", key=f"regen_{task['id']}"):
                        with st.spinner("Refining study plan..."):
                            days_left = (task['due_date'] - datetime.date.today()).days
                            new_plan = ai.generate_study_plan(task['name'], task['task_category'], days_left, task['description'])
                            db.save_ai_response(task['id'], new_plan)
                            st.rerun()

            ##Scenario B: No AI Plan yet, show generation button for pending tasks##
            elif task['status'] == "Pending":
                col_left, col_center, col_right = st.columns([1, 1, 1]) #For placing the "Generate AI Plan at the center"
                with col_center:
                    if st.button("✨ Generate AI Study Plan", type='primary' ,key=f"gen_{task['id']}", use_container_width=True):
                        with st.spinner(f"Consulting Gemini AI for {task['name']}..."):
                            days_left = (task['due_date'] - datetime.date.today()).days
                            
                            # Call LangChain
                            plan = ai.generate_study_plan(task['name'], task['task_category'], days_left, task['description'])
                            
                            # Save to database
                            db.save_ai_response(task['id'], plan)
                            st.rerun()

##For Navigation setup##
def notifications_page():
    st.title("Notifications")
    st.caption("Stay on top of your most urgent tasks with Forget Me Not.")
    st.divider()

    task_df = db.get_tasks()
    if task_df.empty:
        st.info("You currently have no tasks. Add some tasks to get notifications about upcoming deadlines and AI study plans.")
        return
    
    #Filter for pending tasks with AI plans
    pending_tasks = task_df[task_df["status"] == "Pending"]

    #If there are no pending tasks
    if pending_tasks.empty:
        st.success("Great job! You have no pending tasks. Keep up the good work!")
        return
    today = datetime.date.today()

    #To categorize tasks based on urgency and priority thresholds
    overdue_tasks = []
    due_today = []
    due_soon = []
    on_track = [] # For tasks that are pending but not yet urgent based on priority thresholds

    for _, task in pending_tasks.iterrows():
        days_left = (task['due_date'] - today).days
        # Fetch the priority using the correct DB column name
        priority = task.get('task_priority', 'Medium') 
    
        # Very High = 14 days, High = 7 days, Medium = 3 days, Low = 1 day
        threshold = taskPriority_thresholds.get(priority, 3) 
        
        if days_left < 0:
            overdue_tasks.append((task, days_left))
        elif days_left == 0:
            due_today.append((task, days_left))
        elif 0 < days_left <= threshold: # Triggers based on priority
            due_soon.append((task, days_left))
        else:
            on_track.append((task, days_left))

    # Sort each group: most urgent first (fewest days left) ## NOT ENITERLY SURE ABOUT THIS PART
    overdue_tasks.sort(key=lambda x: x[1])   # most overdue first (most negative)
    due_soon.sort(key=lambda x: x[1])
    on_track.sort(key=lambda x: x[1])

    ## Notification Display ##
    total_urgent = len(overdue_tasks) + len(due_today) + len(due_soon)
    if total_urgent == 0:
        st.success("✅ You're all caught up! No urgent deadlines approaching.")
    else:
        summary_parts = []
        if overdue_tasks:
            summary_parts.append(f"**{len(overdue_tasks)} overdue task(s)**")
        if due_today:
            summary_parts.append(f"**{len(due_today)} due task(s) today**")
        if due_soon:
            summary_parts.append(f"**{len(due_soon)} approaching task(s)**")
        st.error(f"🚨 You have {' · '.join(summary_parts)} that require your attention. Let's get busy!")

    st.divider()

    # Helper to render a styled task card
    def render_task_card(task, days_left, alert_fn, badge_label, badge_color):
        priority = task.get('task_priority', 'Medium')
        priority_color = taskPriority_colors.get(priority, 'blue')
        with st.container(border=True):
            col_info, col_badges = st.columns([3, 1])
            with col_info:
                st.markdown(f"### {task['name']}")
                st.caption(f"📁 {task['task_category']}  •  📅 Due: **{task['due_date']}**")
                if task.get('description') and str(task['description']).strip():
                    with st.expander("View description"):
                        st.write(task['description'])
            with col_badges:
                st.badge(badge_label, color=badge_color)
                st.badge(f"{priority} Priority", color=priority_color)
        alert_fn(f"**{task['name']}**")  # Accessibility: repeat name in alert for screen readers (hidden visually via caption styling)

    # --- Section: Overdue ---
    if overdue_tasks:
        with st.expander("🚨 Overdue Tasks"):
            #st.subheader("🚨 Overdue Tasks")
            st.caption("These tasks have passed their due date. Address them immediately!")
            for task, days_left in overdue_tasks:
                days_late = abs(days_left)
                day_word = "day" if days_late == 1 else "days"
                priority = task.get('task_priority', 'Medium')
                priority_color = taskPriority_colors.get(priority, 'blue')
                with st.container(border=True):
                    col_info, col_badges = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### {task['name']}")
                        st.caption(f"📁 {task['task_category']}  •  📅 Was due: **{task['due_date']}**")
                        if task.get('description') and str(task['description']).strip():
                            with st.expander("View description"):
                                st.write(task['description'])
                    with col_badges:
                        st.badge(f"{days_late} {day_word} overdue", color="red")
                        st.badge(f"{priority} Priority", color=priority_color)
                st.error(f"⚠️ **{task['name']}** was due {days_late} {day_word} ago — complete or reschedule it now.")
            st.divider()

    # --- Section: Due Today ---
    if due_today:
        with st.expander("⏰ Due Today"):   
            #st.subheader("⏰ Due Today")
            st.caption("These tasks must be completed by end of day!")
            for task, _ in due_today:
                priority = task.get('task_priority', 'Medium')
                priority_color = taskPriority_colors.get(priority, 'blue')
                with st.container(border=True):
                    col_info, col_badges = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### {task['name']}")
                        st.caption(f"📁 {task['task_category']}  •  📅 Due: **Today**")
                        if task.get('description') and str(task['description']).strip():
                            with st.expander("View description"):
                                st.write(task['description'])
                    with col_badges:
                        st.badge("Due Today", color="orange")
                        st.badge(f"{priority} Priority", color=priority_color)
                st.warning(f"🔔 **{task['name']}** is due today — make it your focus!")
            st.divider()

    # --- Section: Approaching Deadlines ---
    if due_soon:
        with st.expander("📌 Approaching Deadlines"):
            #st.subheader("📌 Approaching Deadlines")
            st.caption("These tasks are within their priority alert window. Start planning now.")
            for task, days_left in due_soon:
                priority = task.get('task_priority', 'Medium')
                priority_color = taskPriority_colors.get(priority, 'blue')
                threshold = taskPriority_thresholds.get(priority, 3)
                day_word = "day" if days_left == 1 else "days"
                with st.container(border=True):
                    col_info, col_badges = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### {task['name']}")
                        st.caption(f"📁 {task['task_category']}  •  📅 Due: **{task['due_date']}**  •  ⏳ {days_left} {day_word} left")
                        if task.get('description') and str(task['description']).strip():
                            with st.expander("View description"):
                                st.write(task['description'])
                    with col_badges:
                        st.badge(f"{days_left} {day_word} left", color=priority_color)
                        st.badge(f"{priority} Priority", color=priority_color)

                # Alert style scales with priority
                if priority == "Very High":
                    st.error(f"🔴 **{task['name']}** ({priority} Priority) — only {days_left} {day_word} left!")
                elif priority == "High":
                    st.warning(f"🟠 **{task['name']}** ({priority} Priority) — {days_left} {day_word} remaining.")
                else:
                    st.info(f"🔵 **{task['name']}** ({priority} Priority) — {days_left} {day_word} to go.")

    # --- Section: On Track ---
    if on_track:
        with st.expander(f"All other pending tasks ({len(on_track)} tasks — No immediate alerts!)"):
            #st.subheader(f"All other pending tasks ({len(on_track)} tasks — no immediate alerts)")
            st.caption("These tasks are pending but not yet within their alert window.")
            for task, days_left in on_track:
                priority = task.get('task_priority', 'Medium')
                priority_color = taskPriority_colors.get(priority, 'blue')  
                threshold = taskPriority_thresholds.get(priority, 3)
                day_word = "day" if days_left == 1 else "days"
                with st.container(border=True):
                    col_info, col_badges = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"### {task['name']}")
                        st.caption(f"📁 {task['task_category']}  •  📅 Due: **{task['due_date']}**  •  ⏳ {days_left} {day_word} left")
                        if task.get('description') and str(task['description']).strip():
                            with st.expander("View description"):
                                st.write(task['description'])
                    with col_badges:
                        st.badge(f"{days_left} {day_word} left", color=priority_color)
                        st.badge(f"{priority} Priority", color=priority_color)

                # Alert style scales with priority
                if priority == "Very High":
                    st.error(f"🔴 **{task['name']}** ({priority} Priority) — only {days_left} {day_word} left!")
                elif priority == "High":
                    st.warning(f"🟠 **{task['name']}** ({priority} Priority) — {days_left} {day_word} remaining.")
                else:
                    st.info(f"🔵 **{task['name']}** ({priority} Priority) — {days_left} {day_word} to go.")

## Compute urgent task count for the notification badge ##
_all_tasks = db.get_tasks()
_urgent_count = 0
if not _all_tasks.empty:
    _pending = _all_tasks[_all_tasks["status"] == "Pending"]
    _urgent_count = len(_pending[_pending["task_priority"].isin(["Very High", "High"])])

pages = {
    "Main Menu":[
        st.Page(dashboard_page, title="Dashboard"),
        st.Page(all_tasks_page, title="All Tasks"),
        st.Page(notifications_page, title="Notifications")
    ]
}

selected_page = st.navigation(pages)

##Sidebar with logo and navigation##
with st.sidebar:
    # Notification badge just below the nav link
    if _urgent_count > 0:
        task_word = "task" if _urgent_count == 1 else "tasks"
        st.badge(f"🔴 {_urgent_count} Urgent {task_word}", color="red")
    #NEW addition: NotebookLM Extension#
    st.subheader("Study Extensions")
    st.caption("Upload your textbooks and notes to Google's NotebookLM to generate quizzes, notes, and more.")
    
    # st.link_button automatically opens the URL in a new browser tab
    st.link_button(
        label="✨Open Google NotebookLM✨", 
        url="https://notebooklm.google.com/", 
        type="primary",
        use_container_width=True
    )
    

selected_page.run()  # Call the function for the selected page
    