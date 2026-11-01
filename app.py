import random
import pandas as pd
import streamlit as st
import re
st.set_page_config(
    page_title="Shout It Out",
    layout="wide"
)
st.markdown("""
<style>
div.stButton > button {
    height: 100px;
    width: 100%;
    font-size: 28px;
    font-weight: 700;
    border-radius: 15px;
}
</style>
""", unsafe_allow_html=True)

st.subheader("Additional Prompts, for this game only")
extra_prompts = st.text_area(
    "One prompt per line", 
    height=150)
prompts_df=pd.read_excel("prompts.xlsx", sheet_name="Prompts")
choices_df=pd.read_excel("prompts.xlsx", sheet_name="Choices")
LIMITED_PLACEHOLDERS=["{letters}","{colour}"]
def draw_prompt():
    active = prompts_df[
        prompts_df["active"].astype(str).str.upper().isin(["TRUE", "YES", "1"])
    ]
    letter_rows=active.copy()
    active=active[active["template"].apply(lambda x: (not any (ph in x for ph in LIMITED_PLACEHOLDERS)or st.session_state.prompt_usage.get(x,0)<3))]
    if st.session_state.get("custom_prompts"):
        custom_df = pd.DataFrame(st.session_state.custom_prompts)
        active=pd.concat([active, custom_df], ignore_index=True)
    remaining = active[~active["id"].isin(st.session_state.used_prompt_ids)]
    if remaining.empty:
        st.session_state.finished=True
        return {
        "text": "All prompts have been used",
        "template": ""
        }
    row = remaining.sample(1).iloc[0]
    template=row["template"]
    if any (ph in template for ph in LIMITED_PLACEHOLDERS):
        st.session_state.prompt_usage[template]=(
            st.session_state.prompt_usage.get(template,0)+1
        )
    st.session_state.used_prompt_ids.append(row["id"])

    text = row["template"]
    placeholders=re.findall(r"\{(.*?)\}", text)
    for placeholder in placeholders:
        values=(choices_df[choices_df["choice_group"] == placeholder]["value"].dropna().tolist())
        if values:
            text=text.replace(f"{{{placeholder}}}", random.choice(values))
    return {
        "text": text,
        "template":row["template"]
        }

if "scores" not in st.session_state:
    st.session_state.scores={}
if "current_prompt" not in st.session_state:
    st.session_state.current_prompt=None
if "history" not in st.session_state:
    st.session_state.history=[]
if "finished" not in st.session_state:
    st.session_state.finished=False
if "teams" not in st.session_state:
    st.session_state.teams=[]
if "used_prompt_ids" not in st.session_state:
    st.session_state.used_prompt_ids=[]
if "prompt_usage" not in st.session_state:
    st.session_state.prompt_usage={}
team_count = st.number_input("Number of teams", min_value=2, max_value=10, value=2, step=1)

with st.form("team_setup"):
    team_names=[
        st.text_input(f"Name for Team {i + 1}", value=f"Team {i + 1}")
        for i in range(team_count)]
    submitted=st.form_submit_button("Set up Teams")

if submitted:
    st.session_state.custom_prompts = []

    if extra_prompts:

        for i, prompt in enumerate(
            extra_prompts.splitlines()
        ):

            prompt = prompt.strip()

            if prompt:

                st.session_state.custom_prompts.append(
                    {
                        "id": f"CUSTOM_{i}",
                        "active": "TRUE",
                        "template": prompt
                    }
                )
    teams = [
        name.strip() or f"Team {i + 1}"
        for i, name in enumerate(team_names)
    ]

    st.session_state.teams = teams
    st.session_state.scores = {team: 0 for team in teams}
    st.success(f"Team setup complete ({len(teams)} teams)")
    for team in teams:
        st.write(f"• {team}")
    st.session_state.current_prompt = None
    st.session_state.history = []
    st.session_state.finished = False
    st.session_state.prompt_usage={}

draw_disabled=st.session_state.current_prompt is not None
if st.button("Draw prompt", disabled=draw_disabled) and not st.session_state.finished:
    if not st.session_state.get("teams"):
        st.warning("Set up Team Names first.")
    else:
        st.session_state.current_prompt=draw_prompt()
if st.session_state.current_prompt:
    st.subheader(st.session_state.current_prompt["text"])
    template=st.session_state.current_prompt["template"]
    if "{letters}" in template:
        if st.button("New Letter"):
            text=template
            placeholders=re.findall(r"\{(.*?)\}", text)
            for placeholder in placeholders:
                values=(choices_df[choices_df["choice_group"]==placeholder]["value"].dropna().tolist())
                if values:
                    text=text.replace(
                        f"{{{placeholder}}}", random.choice(values)
                    )
            st.session_state.current_prompt["text"]=text
            st.rerun()
    st.write("Who got the correct answer first")
    button_cols=st.columns([1]*(len(st.session_state.teams)+1), gap="large")
    with button_cols[0]:
        if st.button("Draw", key="next_prompt",use_container_width=True):
            st.session_state.history.append({
                "prompt": st.session_state.current_prompt,
                "winner":"No Winner"
            })
            st.session_state.current_prompt = draw_prompt()
            st.rerun()
    for i, team in enumerate(st.session_state.teams):
        with button_cols[i+1]:
            if st.button(team, key=f"score_{team}", use_container_width=True):
                st.session_state.scores[team]+=1
                st.session_state.history.append({
                    "prompt": st.session_state.current_prompt, 
                    "winner":team})
                st.session_state.current_prompt=draw_prompt()
                st.rerun()
            


st.divider()

st.subheader("🏆 Scoreboard")

score_df = (
    pd.DataFrame(
        st.session_state.scores.items(),
        columns=["Team", "Score"]
    )
    .sort_values("Score", ascending=False)
)

st.dataframe(
    score_df,
    hide_index=True,
    use_container_width=True
)