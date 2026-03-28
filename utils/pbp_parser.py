"""
Play-by-play assist → shot type parsing logic.
Uses nba_api PlayByPlayV3 (the current working endpoint).
Used exclusively by data_pull.py (not imported by the Streamlit app).
"""

from __future__ import annotations
import logging
import re
import time
import unicodedata

logger = logging.getLogger(__name__)

# Regex to parse assist from description: "(LastName N AST)" or "(Full Name N AST)"
# Unicode flag handles diacritics like Jokić, Dončić, Šarić, etc.
_ASSIST_RE = re.compile(r'\(([\w .\'-]+?)\s+\d+\s+AST\)', re.IGNORECASE | re.UNICODE)
# Clock format: "PT09M26.00S" → "9:26"
_CLOCK_RE = re.compile(r'PT(\d+)M([\d.]+)S')


def _parse_clock(clock_str: str) -> str:
    """Convert 'PT09M26.00S' → '9:26'."""
    m = _CLOCK_RE.match(str(clock_str))
    if m:
        mins = int(m.group(1))
        secs = int(float(m.group(2)))
        return f"{mins}:{secs:02d}"
    return str(clock_str)


def _assister_name_from_desc(description: str) -> str | None:
    """Extract assister last name / partial name from play description."""
    m = _ASSIST_RE.search(description)
    if m:
        return m.group(1).strip()
    return None


def _fold_name(s: str) -> str:
    """
    Normalize for comparison: strip combining marks so e.g. Jokić (game log)
    matches Jokic (ASCII in play-by-play text).
    """
    s = unicodedata.normalize("NFKD", s.strip())
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def _name_matches(player_name: str, desc_name: str) -> bool:
    """
    Fuzzy match: check if desc_name (partial/last name from description)
    matches player_name (full name from game log).
    """
    if not desc_name or not str(desc_name).strip():
        return False

    fp = _fold_name(player_name)
    fd = _fold_name(desc_name)

    # Direct contains (on folded strings)
    if fd in fp or fp in fd:
        return True

    # Last name match
    player_last = fp.split()[-1]
    desc_last = fd.split()[-1]
    if player_last == desc_last:
        return True

    # Special: "Jr." suffix removal
    player_last_clean = re.sub(r'\s*(jr\.?|sr\.?|iii?|iv)$', '', player_last).strip()
    desc_last_clean = re.sub(r'\s*(jr\.?|sr\.?|iii?|iv)$', '', desc_last).strip()
    if player_last_clean and player_last_clean == desc_last_clean:
        return True

    return False


def parse_assist_sequences_v3(df_pbp, player_name: str) -> list[dict]:
    """
    Given a PlayByPlayV3 DataFrame and the focal player's full name,
    return a list of assist-sequence dicts ready for assist_sequences.csv.

    Each dict has:
      period, time_remaining, assisted_player, shot_type, shot_value,
      points_scored, is_and1, free_throw_points
    """
    sequences: list[dict] = []

    # Work through made field goals with assist info in description
    fg_made = df_pbp[
        (df_pbp['isFieldGoal'] == 1) &
        (df_pbp['shotResult'] == 'Made')
    ].copy()

    fg_made = fg_made.reset_index(drop=True)

    for idx, row in fg_made.iterrows():
        desc = str(row.get('description', ''))
        assister_in_desc = _assister_name_from_desc(desc)

        if assister_in_desc is None:
            continue  # unassisted

        if not _name_matches(player_name, assister_in_desc):
            continue  # assisted by someone else

        shot_value = int(row.get('shotValue', 2))
        shot_type = "3-pointer" if shot_value == 3 else "2-pointer"
        period = int(row.get('period', 0))
        clock = _parse_clock(row.get('clock', ''))
        shooter_name = str(row.get('playerName', 'Teammate'))

        # Look ahead in the full df_pbp for and-1 free throws
        # Find the original row index in df_pbp
        is_and1 = False
        ft_pts = 0

        # Get the action number of this event to scan forward
        action_num = row.get('actionNumber', None)
        if action_num is not None:
            upcoming = df_pbp[
                (df_pbp['actionNumber'] > action_num) &
                (df_pbp['period'] == period)
            ].head(8)

            for _, next_row in upcoming.iterrows():
                next_action = str(next_row.get('actionType', '')).lower()
                next_desc = str(next_row.get('description', '')).lower()

                if next_row.get('isFieldGoal', 0) == 1:
                    break  # next field goal — new possession

                if 'free throw' in next_action:
                    if 'technical' in next_desc:
                        continue
                    next_shooter = str(next_row.get('playerName', ''))
                    if _fold_name(next_shooter) == _fold_name(shooter_name) or (
                        next_shooter and shooter_name and
                        _fold_name(next_shooter.split()[-1]) == _fold_name(shooter_name.split()[-1])
                    ):
                        is_and1 = True
                        if next_row.get('shotResult', '') == 'Made':
                            ft_pts += 1

        sequences.append({
            'period': period,
            'time_remaining': clock,
            'assisted_player': shooter_name,
            'shot_type': shot_type,
            'shot_value': shot_value,
            'points_scored': shot_value,
            'is_and1': is_and1,
            'free_throw_points': ft_pts,
        })

    return sequences


def fetch_pbp_events_v3(game_id: str) -> object:
    """
    Pull play-by-play from nba_api PlayByPlayV3.
    Returns a DataFrame.
    Raises on failure.
    """
    from nba_api.stats.endpoints import PlayByPlayV3

    for attempt in range(3):
        try:
            time.sleep(0.8)
            pbp = PlayByPlayV3(game_id=game_id, timeout=30)
            df = pbp.get_data_frames()[0]
            return df
        except Exception as e:
            wait = 1.5 ** attempt
            logger.warning(f"PlayByPlayV3 attempt {attempt+1} failed for {game_id}: {e}. Waiting {wait:.1f}s")
            if attempt == 2:
                raise
            time.sleep(wait)


# ── Public interface (called by data_pull.py) ─────────────────────────────────

def fetch_pbpstats_events(game_id: str) -> object:
    """
    Compatibility shim. Returns a DataFrame from PlayByPlayV3.
    data_pull.py calls this then passes the result to parse_assist_sequences().
    """
    return fetch_pbp_events_v3(game_id)


def parse_assist_sequences(df_pbp, player_name: str) -> list[dict]:
    """
    Public interface called by data_pull.py.
    Accepts a PlayByPlayV3 DataFrame and focal player's full name.
    Returns list of assist sequence dicts.
    """
    if df_pbp is None or (hasattr(df_pbp, 'empty') and df_pbp.empty):
        return []
    return parse_assist_sequences_v3(df_pbp, player_name)
