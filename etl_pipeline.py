import pandas as pd
import numpy as np
import time
from nba_api.stats.endpoints import leaguegamelog
from datetime import datetime, timedelta
from supabase import create_client, Client
import os


SUPABASE_URL = os.getenv('SUPABASE_URL')  
SUPABASE_KEY = os.getenv('SUPABASE_KEY')  
# Define Seasons to Fetch
SEASON_YEARS = [str(s) + '-' + str(s+1)[-2:] for s in range(2023, 2026)] 

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_nba_data(seasons):
    """
    Fetches game logs for all players for the specified seasons.
    Uses the 'LeagueGameLog' endpoint which is generally stable.
    """
    all_logs = []
    
    print("🏀 Starting Data Ingestion...")
    
    for season in seasons:
        print(f"   Fetching {season}...")
        try:
            # 'P' = Player logs (not Team), season_type_all_star='Regular Season'
            log = leaguegamelog.LeagueGameLog(
                season=season, 
                player_or_team_abbreviation='P', 
                season_type_all_star='Regular Season'
            )
            df = log.get_data_frames()[0]
            
            # Add a clear 'season' column for filtering later
            df['season'] = season
            all_logs.append(df)
            
            # Respect rate limits (NBA API is sensitive)
            time.sleep(1) 
            
        except Exception as e:
            print(f"   ❌ Error fetching {season}: {e}")

    if not all_logs:
        return pd.DataFrame()

    # Combine all seasons
    final_df = pd.concat(all_logs, ignore_index=True)
    return final_df

def clean_data_for_llm(df):
    """
    Simplifies column names and formats data for the LLM.
    """
    print("🧹 Cleaning Data...")
    
    # 1. Standardize Columns (Mapping NBA API codes to readable names)
    df.columns = df.columns.str.lower()
    
    # 2. drop player_id and team_ids to save token space for the LLM later
    cols_to_keep = [
        'player_name', 'team_abbreviation', 'matchup', 'game_date', 
        'wl', 'min', 'pts', 'fgm', 'fga', 'fg_pct', 
        'fg3m', 'fg3a', 'fg3_pct', 'ftm', 'fta', 'ft_pct', 
        'oreb', 'dreb', 'reb', 'ast', 'stl', 'blk', 'tov', 'pf', 'plus_minus',
        'season'
    ]
    
    df_clean = df[cols_to_keep].copy()
    
    # 3. Convert Types
    # Ensure percentages are floats and numeric cols are ints
    df_clean['game_date'] = pd.to_datetime(df_clean['game_date']).dt.strftime('%Y-%m-%d')
    df_clean['pts'] = df_clean['pts'].astype(int)

    df_clean['fg_pct'] = df_clean['fg_pct'].replace(np.nan, None)
    df_clean['fg3_pct'] = df_clean['fg3_pct'].replace(np.nan, None)
    df_clean['ft_pct'] = df_clean['ft_pct'].replace(np.nan, None)
                                                    
    return df_clean

def upload_to_supabase(df, table_name="player_game_logs"):
    """
    Uploads the dataframe to Supabase in chunks.
    """
    print(f"Uploading {len(df)} rows to Supabase table '{table_name}'...")
    
    # Convert DataFrame to list of dicts (JSON)
    records = df.to_dict(orient='records')
    
    # Supabase (and most APIs) prefer chunked uploads
    chunk_size = 1000
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            response = supabase.table(table_name).upsert(chunk).execute()
            print(f"   ✅ Batch {i // chunk_size + 1} uploaded.")
        except Exception as e:
            print(f"   ❌ Error uploading batch: {e}")


def get_yesterday_date():
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%m/%d/%Y') # Format required by some endpoints



if __name__ == "__main__":
    # Check if we are running in "Daily Update" mode or "Historical Backfill" mode
    # For simplicity, let's assume we just want to fetch the current season every time
    # (The API is fast enough to just re-fetch the current active season daily)
    
    current_season = ['2025-26'] 
    
    # 1. Fetch ONLY current season (replace with SEASON_YEARS for full backfill)
    raw_df = fetch_nba_data(current_season)
    
    if not raw_df.empty:
        clean_df = clean_data_for_llm(raw_df)
        
        # 2. Upsert (Update/Insert)
        # Supabase 'upsert' prevents duplicates if the 'id' or primary key matches.
        
        # Option B (Easiest Reliability): Delete current season data, then re-upload.
        print("Emptying current season data to prevent duplicates...")
        supabase.table("player_game_logs").delete().eq("season", current_season[0]).execute()
        
        upload_to_supabase(clean_df)