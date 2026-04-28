import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import pandas as pd
from datetime import datetime

# ── Environment setup ──────────────────────────────────────────────────────────

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
MODEL = 'gpt-4o-mini'

# ── Mock Database ──────────────────────────────────────────────────────────────
# In a production app, these would be SQL tables or a cloud database

slots_db = {
    "Morning": ["06:00", "07:00", "08:00", "09:00"],
    "Evening": ["17:00", "18:00", "19:00", "20:00", "21:00"]
}

leads_db = []

faq_knowledge_base = {
    "parking": "Yes, we have free parking available for all members and trial visitors.",
    "cancel": "Memberships are non-refundable but can be transferred to another person for a small admin fee.",
    "freeze": "You can freeze your annual membership for up to 30 days for medical reasons with documentation.",
    "trainers": "All our trainers are internationally certified with a minimum of 3 years of experience.",
    "ladies": "We have dedicated ladies-only training sessions available in the morning and afternoon.",
    "trial": "We offer a free one-day trial so you can experience the gym before committing."
}

# ── Tool Functions ─────────────────────────────────────────────────────────────

def check_availability(time_of_day: str) -> str:
    """Returns available trial slots for Morning or Evening."""
    slots = slots_db.get(time_of_day, [])
    if not slots:
        return json.dumps({"error": "No slots available for that time."})
    return json.dumps({"available_slots": slots})


def book_trial(name: str, phone: str, time: str, goal: str = "General") -> str:
    """Books a free trial and saves lead to the database."""
    status = "Hot Lead" if goal and goal.lower() != "general" else "Warm Lead"
    lead_entry = {
        "Name": name,
        "Phone": phone,
        "Time": time,
        "Goal": goal,
        "Status": status,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    leads_db.append(lead_entry)
    return f"Success! {name} is booked for a free trial at {time}. We look forward to seeing you!"


def generate_mini_plan(goal: str, current_weight: float) -> str:
    """Generates a quick personalized diet and workout summary."""
    goal_lower = goal.lower()
    if "loss" in goal_lower:
        return (
            f"For your goal of weight loss at {current_weight}kg: "
            f"Aim for a 300kcal daily deficit. "
            f"Target 1.5g of protein per kg of bodyweight. "
            f"Recommended training: 3 days strength + 2 days cardio per week."
        )
    elif "muscle" in goal_lower or "gain" in goal_lower:
        return (
            f"For your goal of muscle gain at {current_weight}kg: "
            f"Aim for a 200kcal daily surplus. "
            f"Focus on hypertrophy training (8-12 reps). "
            f"Consider creatine supplementation for performance support."
        )
    else:
        return (
            "For body recomposition: Stay at maintenance calories with high protein intake. "
            "Follow a progressive overload strength program."
        )


def get_policy_answer(topic: str) -> str:
    """Returns gym policy answers for common FAQs."""
    topic_lower = topic.lower()
    for key, value in faq_knowledge_base.items():
        if key in topic_lower:
            return value
    return "That's a great question — let me connect you with our team for the most accurate answer."


# ── Tool Definitions for OpenAI ────────────────────────────────────────────────

tools = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check available gym trial slots. Input must be 'Morning' or 'Evening'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "time_of_day": {"type": "string", "enum": ["Morning", "Evening"]}
                },
                "required": ["time_of_day"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_trial",
            "description": "Book a free trial session. Always collect Name, Phone, and Goal before booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the prospect"},
                    "phone": {"type": "string", "description": "Phone number of the prospect"},
                    "time": {"type": "string", "description": "Selected trial time slot"},
                    "goal": {"type": "string", "description": "Fitness goal e.g. weight loss, muscle gain"}
                },
                "required": ["name", "phone", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_mini_plan",
            "description": "Generate a quick personalized diet and workout plan to add value for the prospect.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "Fitness goal e.g. weight loss, muscle gain"},
                    "current_weight": {"type": "number", "description": "Current weight in kg"}
                },
                "required": ["goal", "current_weight"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_policy_answer",
            "description": "Get official gym policy answers for FAQs about parking, cancellation, freezing, trainers, or ladies batches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "The topic or keyword to look up"}
                },
                "required": ["topic"]
            }
        }
    }
]

# ── System Prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are 'Coach Max', the AI Sales Assistant at PeakForm Gym.
Your goal is to help prospects find the right membership by being genuinely helpful — not pushy.

SALES STRATEGY:
1. Discovery first — always ask about their fitness goal before discussing pricing.
2. Add value — if they share their weight and goal, offer a free Mini Plan using the tool.
3. Handle objections — use get_policy_answer for questions about parking, cancellation, etc.
4. Close gently — when they seem interested, invite them to book a FREE trial session.

MEMBERSHIP PRICING (only share if asked):
- Basic: $49/month — Gym floor access only
- Pro: $79/month — Gym + Group classes + Sauna
- Elite: $120/month — Full access + 5 Personal Training sessions

RULES:
- Never reveal pricing unprompted — lead with value first.
- Always collect Name, Phone, and Goal before booking a trial.
- Keep responses concise and friendly.
- If unsure about a policy, use get_policy_answer before guessing.
"""

# ── Chat Logic ─────────────────────────────────────────────────────────────────

TOOL_ROUTER = {
    "check_availability": lambda args: check_availability(args["time_of_day"]),
    "book_trial": lambda args: book_trial(args["name"], args["phone"], args["time"], args.get("goal", "General")),
    "generate_mini_plan": lambda args: generate_mini_plan(args["goal"], args["current_weight"]),
    "get_policy_answer": lambda args: get_policy_answer(args["topic"]),
}


def chat_logic(message: str, history: list) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for h in history:
        if isinstance(h, dict) and "role" in h and "content" in h:
            messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for tool_call in msg.tool_calls:
                fname = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                handler = TOOL_ROUTER.get(fname)
                result = handler(args) if handler else f"Unknown tool: {fname}"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": fname,
                    "content": str(result)
                })

            final = client.chat.completions.create(model=MODEL, messages=messages)
            return final.choices[0].message.content

        return msg.content

    except Exception as e:
        return f"Something went wrong: {e}"


# ── Admin Helper ───────────────────────────────────────────────────────────────

def get_leads_dataframe():
    if not leads_db:
        return pd.DataFrame(columns=["Name", "Phone", "Time", "Goal", "Status", "Timestamp"])
    return pd.DataFrame(leads_db)


# ── Gradio UI ──────────────────────────────────────────────────────────────────

with gr.Blocks(theme=gr.themes.Soft(), title="PeakForm Gym - AI Sales Agent") as app:
    gr.Markdown("# PeakForm Gym — AI Sales Assistant")
    gr.Markdown("Chat with Coach Max to learn about memberships, book a free trial, or get a personalized fitness plan.")

    with gr.Row():
        with gr.Column(scale=2):
            gr.ChatInterface(
                fn=chat_logic,
                type="messages",
                examples=[
                    "What memberships do you offer?",
                    "I want to lose weight, I am 85kg.",
                    "Do you have parking?",
                    "Can I book a free trial?"
                ]
            )

        with gr.Column(scale=1):
            gr.Markdown("### Membership Pricing")
            gr.DataFrame(
                headers=["Tier", "Price", "Features"],
                value=[
                    ["Basic", "$49/mo", "Gym Floor Only"],
                    ["Pro", "$79/mo", "Gym + Classes + Sauna"],
                    ["Elite", "$120/mo", "Full Access + 5 PT Sessions"]
                ]
            )

            gr.Markdown("---")
            gr.Markdown("### Admin — Captured Leads")
            gr.Markdown("*Note: Leads reset on app restart. Connect a database for persistence.*")
            refresh_btn = gr.Button("Refresh Leads")
            leads_table = gr.DataFrame(value=get_leads_dataframe())
            refresh_btn.click(fn=get_leads_dataframe, outputs=leads_table)

app.launch(inbrowser=True)