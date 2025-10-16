import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv

import google.generativeai as genai
from supabase import create_client, Client

# -------------------------
# Configuration and Setup
# -------------------------
load_dotenv()
st.set_page_config(page_title="Smart Task Planner", page_icon="🎯", layout="wide")

# --- API Key Configuration ---
try:
    API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("🚨 Missing Google API key. Please add it to your environment variables.")
    st.stop()
except Exception as e:
    st.error(f"🚨 An error occurred during API configuration: {e}")
    st.stop()

# --- Supabase Configuration ---
try:
    SUPABASE_URL = os.environ["SUPABASE_URL"]
    SUPABASE_KEY = os.environ["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except KeyError as e:
    st.error(f"🚨 Missing Supabase credentials: {e}. Please add SUPABASE_URL and SUPABASE_KEY to your environment.")
    st.stop()
except Exception as e:
    st.error(f"🚨 An error occurred during Supabase configuration: {e}")
    st.stop()


# -------------------------
# Available Models
# -------------------------
AVAILABLE_MODELS = {
    "Gemini 2.0 Flash (Experimental) - Fastest": "models/gemini-2.0-flash-exp",
    "Gemini 2.5 Flash - Recommended": "models/gemini-2.5-flash",
    "Gemini 2.5 Pro - Most Capable": "models/gemini-2.5-pro",
    "Gemini 2.0 Flash - Stable": "models/gemini-2.0-flash",
}

# -------------------------
# Database Functions
# -------------------------
def save_plan_to_db(goal: str, model_name: str, plan_json: dict):
    """Saves a generated plan to Supabase."""
    try:
        data = {
            "goal": goal,
            "model_used": model_name,
            "plan_json": plan_json
        }
        result = supabase.table("task_plans").insert(data).execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_recent_plans(limit: int = 10):
    """Retrieves recent plans from the database."""
    try:
        result = supabase.table("task_plans")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def search_plans_by_goal(search_term: str):
    """Searches plans by goal text."""
    try:
        result = supabase.table("task_plans")\
            .select("*")\
            .ilike("goal", f"%{search_term}%")\
            .order("created_at", desc=True)\
            .execute()
        return {"success": True, "data": result.data}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_plan(plan_id: str):
    """Deletes a plan from the database."""
    try:
        result = supabase.table("task_plans")\
            .delete()\
            .eq("id", plan_id)\
            .execute()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------
# Core Function
# -------------------------
def generate_plan(goal: str, model_name: str):
    """Generates a structured project plan from a user's goal using the Gemini API."""
    if not goal:
        return {"error": "Goal cannot be empty."}

    prompt = f"""
You are an expert project manager AI. Your task is to break down the user's goal into a structured action plan.
Goal: "{goal}"

Return ONLY a valid JSON object with this exact structure:
{{
  "plan": [
    {{
      "task_id": 1,
      "task_name": "Task name here",
      "description": "Detailed description here",
      "dependencies": [],
      "duration_days": 5
    }}
  ]
}}

Rules:
- task_id: integer starting from 1
- task_name: concise string
- description: detailed string
- dependencies: array of task_id integers (empty array if none)
- duration_days: integer

Provide a complete, logical breakdown of the goal into sequential tasks.
Return ONLY the JSON, no other text or markdown formatting.
"""
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        response = model.generate_content(
            contents=prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                top_p=0.95,
                top_k=40,
                max_output_tokens=8192,
            )
        )

        # Parse the response
        response_text = response.text.strip()
        
        # Try to extract JSON if it's wrapped in markdown code blocks
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines).strip()
        
        try:
            plan_json = json.loads(response_text)
            # Basic validation to ensure the structure is correct
            if "plan" in plan_json and isinstance(plan_json["plan"], list):
                return plan_json
            else:
                 return {"error": "AI returned JSON in an unexpected format.", "raw": response_text}
        except json.JSONDecodeError as je:
            return {"error": f"AI failed to return valid JSON: {je}", "raw": response_text}

    except Exception as e:
        # Catch potential API errors
        return {"error": f"An error occurred while calling the AI model: {e}"}


def display_plan(tasks: list):
    """Displays a plan in an organized format."""
    if not tasks:
        st.warning("The plan is empty.")
        return
    
    # Sort tasks by ID for a logical display order
    sorted_tasks = sorted(tasks, key=lambda x: x.get("task_id", 0))
    
    for task in sorted_tasks:
        task_id = task.get('task_id', '?')
        task_name = task.get('task_name', 'Unnamed Task')
        duration = task.get('duration_days', '?')
        dependencies = task.get("dependencies", [])
        deps_str = ", ".join(map(str, dependencies)) if dependencies else "None"

        with st.expander(f"**Task {task_id}: {task_name}** ({duration} days)"):
            st.markdown(f"**Description:** {task.get('description', 'No description provided.')}")
            st.markdown(f"**Dependencies:** Task(s) {deps_str}")


# -------------------------
# Streamlit UI
# -------------------------

# Create tabs for different sections
tab1, tab2 = st.tabs(["📝 Generate Plan", "📚 View History"])

# TAB 1: Generate Plan
with tab1:
    st.title("🎯 Smart Task Planner")
    st.write(
        "Describe your high-level goal, and the AI will break it down into a "
        "detailed, structured action plan for you."
    )

    # Model selection
    col1, col2 = st.columns([3, 1])

    with col1:
        # Initialize session state for the input field
        if "goal_input" not in st.session_state:
            st.session_state.goal_input = "Launch a minimal e-commerce web app in 4 weeks."

        goal_input = st.text_input(
            "Enter your goal:",
            key="goal_input"
        )

    with col2:
        selected_model_display = st.selectbox(
            "Select Model:",
            options=list(AVAILABLE_MODELS.keys()),
            index=0  # Default to Gemini 2.0 Flash Experimental
        )
        selected_model = AVAILABLE_MODELS[selected_model_display]

    if st.button("Generate Plan", type="primary", use_container_width=True):
        if goal_input:
            with st.spinner("🧠 AI is thinking... Please wait."):
                result = generate_plan(goal_input, selected_model)

            if "error" in result:
                st.error(f'**Error:** {result["error"]}')
                if "raw" in result and result["raw"]:
                    with st.expander("📟 View Raw AI Output"):
                        st.code(result["raw"], language="text")
            elif "plan" in result:
                tasks = result.get("plan", [])
                
                if not tasks:
                    st.warning("The AI generated an empty plan. Try a more specific goal.")
                else:
                    st.success("✅ Here is your AI-generated action plan:")
                    display_plan(tasks)
                    
                    # Save to database
                    with st.spinner("💾 Saving to database..."):
                        save_result = save_plan_to_db(goal_input, selected_model, result)
                        
                        if save_result["success"]:
                            st.success("✅ Plan saved to database!")
                        else:
                            st.warning(f"⚠️ Plan generated but failed to save: {save_result.get('error', 'Unknown error')}")
            else:
                st.warning("The AI did not return a valid plan. Please try rephrasing your goal.")
        else:
            st.warning("Please enter a goal first.")

    # Footer
    st.markdown("---")
    st.caption(f"Using model: `{selected_model}`")

# TAB 2: View History
with tab2:
    st.title("📚 Plan History")
    st.write("Browse and search your previously generated plans.")
    
    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search plans by goal:", key="search_query")
    with col2:
        st.write("")
        st.write("")
        if st.button("Search", use_container_width=True):
            st.session_state.search_triggered = True
    
    # Fetch and display plans
    if search_query and st.session_state.get("search_triggered", False):
        with st.spinner("Searching..."):
            plans_result = search_plans_by_goal(search_query)
            st.session_state.search_triggered = False
    else:
        with st.spinner("Loading recent plans..."):
            plans_result = get_recent_plans(20)
    
    if plans_result["success"]:
        plans = plans_result["data"]
        
        if not plans:
            st.info("No plans found. Generate your first plan in the 'Generate Plan' tab!")
        else:
            st.success(f"Found {len(plans)} plan(s)")
            
            for plan in plans:
                plan_id = plan["id"]
                goal = plan["goal"]
                model_used = plan["model_used"]
                created_at = datetime.fromisoformat(plan["created_at"].replace("Z", "+00:00"))
                plan_json = plan["plan_json"]
                
                with st.expander(f"🎯 {goal[:100]}{'...' if len(goal) > 100 else ''}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Goal:** {goal}")
                        st.caption(f"Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')} | Model: {model_used}")
                    
                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{plan_id}"):
                            delete_result = delete_plan(plan_id)
                            if delete_result["success"]:
                                st.success("Deleted!")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {delete_result.get('error')}")
                    
                    st.markdown("---")
                    if "plan" in plan_json:
                        display_plan(plan_json["plan"])
                    else:
                        st.json(plan_json)
    else:
        st.error(f"Failed to load plans: {plans_result.get('error', 'Unknown error')}")
