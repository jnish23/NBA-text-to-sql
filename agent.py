import os
import sys
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI

# If running locally, you might need 'from dotenv import load_dotenv; load_dotenv()'
try:
    # 1. Google API Key
    # The library automatically looks for "GOOGLE_API_KEY" in env, 
    # but checking here ensures we fail fast if it's missing.
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

    # 2. Database URI
    # This should be the FULL connection string stored as one secret
    DB_URI = os.environ["DB_URI"]
    
except KeyError as e:
    print(f"❌ CRITICAL ERROR: Missing secret {e}")
    print("   If in Codespaces: Add this to GitHub Repo Settings > Secrets > Codespaces")
    print("   If Local: Create a .env file and ensure load_dotenv() is called.")
    sys.exit(1)


# --- 1. Connect to the "Brain" (LLM) ---
# Gemini 1.5 Flash is fast, cheap (free tier), and good at SQL
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0, # 0 = factual, 1 = creative. We want factual SQL.
)

# --- 2. Connect to the "Memory" (Database) ---
db = SQLDatabase.from_uri(DB_URI)

# --- 3. The "System Prompt" (The Secret Sauce) ---
# This tells the Agent how to behave and explains your specific data quirks.
system_prefix = """
You are an expert NBA Data Science Agent. 
You are designed to answer questions by querying a PostgreSQL database.

Given an input question, create a syntactically correct PostgreSQL query to run, 
then look at the results of the query and return the answer.

Schema definition for `player_game_logs`:
- `player_name` : Player Name
- `team_abbreviation` : Team Abbreviation 
- `matchup` : Format "DEN vs. LAL" (Denver was Home) or "LAL @ Den" (LAL was Away)
- `game_date`` : date
- `pts` : Points
- `fgm` : Field Goals Made
- `fga`: Field Goals Attempted
- `fgm`: Field Goals Made
- `fg_pct`: Field Goal Percentage (0.5 = 50%)
- `min`: Minutes Played 
- `wl`: Win/Loss ("W" or "L")
- `season`: Format "2023-24" or "2024-25"
- `fg3m` : 3 Point Field Goals Made
- `fg3a` : 3 Point Field Goals Attempted
- `fg3_pct` : 3 Point Field Goal Percentage
- `ftm` : Free Throws Made
- `fta` : Free Throws Attempted
- `ft_pct` : Free Throw Percentage
- `oreb` : Offensive Rebounds
- `dreb` : Defensive Rebounds
- `reb` : Total Rebounds
- `ast` : Assists
- `stl` : Steals
- `blk` : Blocks 
- `tov` : Turnovers
- `pf` : Personal Foulds
-  `plus_minus` :Plus Minus

There is one row per player per team per game that was played, assuming the player played 

CRITICAL RULES:
1. **Never** query for all columns (`SELECT *`). Only select the columns needed to answer the question.
2. If asked about "efficiency" or "shooting", usually check `fg_pct` and `fga`.
3. `min` is a string! To sort by minutes, you might need to cast it, but usually just filtering by games > 20 mins is enough.
4. Do NOT use `LIMIT` unless the user specifically asks for a "Top N" list.
"""

# --- 4. Build the Agent ---
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools", # Gemini supports this tool-calling standard
    prefix=system_prefix,
    verbose=True # This lets you see the "Thinking" process in the console
)

# --- 5. Run It (The Interface) ---
if __name__ == "__main__":
    print("🏀 NBA Agent Ready! Type 'exit' to quit.")
    
    while True:
        user_q = input("\nAsk a question: ")
        if user_q.lower() == "exit":
            break
            
        try:
            # invoke() sends the text to the agent
            response = agent_executor.invoke({"input": user_q})
            print(f"\n🤖 Answer: {response['output']}")
        except Exception as e:
            print(f"❌ Error: {e}")