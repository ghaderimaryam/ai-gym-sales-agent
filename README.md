# PeakForm Gym — AI Sales Assistant

An AI-powered gym sales agent with tool calling, lead capture, and an admin dashboard. 
Chat with Coach Max to explore memberships, book a free trial, or get a personalized fitness plan.

## Demo

![Demo](assets/demo.gif)

## Features

- Conversational AI sales agent with a discovery-first strategy
- OpenAI function calling — checks availability, books trials, generates fitness plans
- Live lead capture with admin dashboard
- Personalized mini fitness plans based on user goals and weight
- FAQ handler for gym policies

## Tech Stack

- Python
- OpenAI API (function calling / tool use)
- Gradio
- Pandas

## Getting Started

### 1. Clone the repo
git clone https://github.com/ghaderimaryam/ai-gym-sales-agent.git
cd ai-gym-sales-agent

### 2. Install dependencies
pip install -r requirements.txt

### 3. Set up environment variables
cp .env.example .env
# Add your OpenAI API key to .env

### 4. Run the app
python3 app.py

## How It Works

The agent follows a 3-step sales strategy:
1. Discovery — asks about fitness goals before discussing price
2. Value — generates a free personalized mini plan to build trust
3. Close — invites the prospect to book a free trial session

Tool calling enables the agent to check real availability, book trials, and answer FAQs dynamically.