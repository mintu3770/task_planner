# 🎯 Smart Task Planner

A Python-based application that uses a Large Language Model (LLM) to break down high-level user goals into actionable, dependent tasks with estimated timelines. The frontend is built with Streamlit.

## ✨ Features

-   **AI-Powered Reasoning:** Leverages Google's Gemini Pro model to understand goals and generate logical task breakdowns.
-   **Task Dependencies:** Automatically identifies which tasks must be completed before others can begin.
-   **Timeline Estimation:** Provides an estimated duration in days for each task.
-   **Interactive Frontend:** A clean and simple user interface built with Streamlit to input goals and view the generated plan.
-   **Structured Output:** The LLM is prompted to return a clean JSON object, ensuring reliable parsing and display.

## 🛠️ Tech Stack

-   **Backend Logic:** Python
-   **AI Model:** Google Gemini Pro
-   **Frontend:** Streamlit
-   **API Interaction:** `google-generativeai` library
-   **Environment Management:** `python-dotenv`

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Prerequisites

-   Python 3.8+
-   A Google API Key. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/smart-task-planner.git
    cd smart-task-planner
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Key:**
    -   Create a new file named `.env` in the root of the project directory.
    -   Add your Google API key to this file:
        ```
        GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
        ```

### Running the Application

Once the setup is complete, run the Streamlit app with the following command:

```bash
streamlit run app.py
