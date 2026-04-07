from __future__ import annotations

import json
import random
from pathlib import Path


OUTPUT_PATH = Path("data/realistic_triage_records.jsonl")


CASE_LIBRARY = [
    {
        "severity": "low",
        "subtype": "general_distress",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: general_distress; repeated_emergencies: 0; last_session_days_ago: 21",
        "openers": [
            "Work was exhausting and I still can't switch my brain off.",
            "I've been feeling stretched thin and I barely slept this week.",
            "Nothing dramatic happened, I'm just tired and on edge lately.",
            "Today was fine on paper but I still feel weirdly tense.",
        ],
        "assistant_prompts": [
            "What felt most draining about today?",
            "When did that stress start building up?",
            "What has your body been doing when you try to rest?",
            "What part of the day keeps replaying in your head?",
        ],
        "followups": [
            "Mostly I keep replaying meetings and worrying I forgot something.",
            "I get tense at night and then I feel silly for overreacting.",
            "It feels like my brain won't slow down even when I'm home.",
            "I don't feel in danger, just constantly wound up.",
        ],
    },
    {
        "severity": "low",
        "subtype": "general_distress",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: general_distress; repeated_emergencies: 0; last_session_days_ago: 14",
        "openers": [
            "I've been crying easily and I don't really know why.",
            "I feel kind of fragile and small over little things today.",
            "I feel off today and a little more emotional than usual.",
            "I keep telling myself I'm okay, but I don't really feel okay.",
        ],
        "assistant_prompts": [
            "Did something specific happen or is it more of a build-up?",
            "What has felt hardest to carry today?",
            "How long have you been feeling this way?",
            "What changed in your week, even if it seemed small?",
        ],
        "followups": [
            "It is more like everything piled up and now normal stuff feels harder.",
            "I keep thinking I should be handling this better than I am.",
            "Nothing huge happened, which almost makes me feel worse for struggling.",
            "I think I've been pushing through for too long without stopping.",
        ],
    },
    {
        "severity": "medium",
        "subtype": "panic_anxiety",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: panic_anxiety; repeated_emergencies: 0; last_session_days_ago: 6",
        "openers": [
            "My chest has been tight all day and I feel like something bad is coming.",
            "I can't calm down and my heart keeps racing for no reason.",
            "I am trying to act normal but inside I feel like I'm spiraling.",
            "I keep checking my breathing because it feels wrong.",
        ],
        "assistant_prompts": [
            "What happens in your body when that wave hits?",
            "Did something trigger the panic today?",
            "Are you able to slow your breathing at all right now?",
            "Does it feel more like fear, dread, or total overwhelm?",
        ],
        "followups": [
            "My hands shake and I keep checking if I'm about to pass out.",
            "It started after a text from my boss and then it kept growing.",
            "I know it might be anxiety but it feels physically overwhelming.",
            "I get scared that something is medically wrong even when tests were normal.",
        ],
    },
    {
        "severity": "medium",
        "subtype": "depression_hopelessness",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: depression_hopelessness; repeated_emergencies: 0; last_session_days_ago: 9",
        "openers": [
            "Everything feels flat and pointless lately even when I try to keep going.",
            "I got through the day, but honestly I don't feel much of anything anymore.",
            "I have this heavy feeling that nothing is really going to get better.",
            "People think I'm functioning, but inside everything feels gray.",
        ],
        "assistant_prompts": [
            "When did that hopeless feeling start getting stronger?",
            "Have you been able to enjoy anything lately?",
            "What has changed in the past few weeks?",
            "What feels most empty right now?",
        ],
        "followups": [
            "I am doing the motions, but I feel disconnected from my own life.",
            "People keep telling me to rest, but I wake up feeling the same emptiness.",
            "It feels like I am slowly disappearing inside while everything looks normal outside.",
            "I don't want to scare anyone, but I really don't feel like myself anymore.",
        ],
    },
    {
        "severity": "medium",
        "subtype": "depression_hopelessness",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: depression_hopelessness; repeated_emergencies: 0; last_session_days_ago: 16",
        "openers": [
            "Everyone keeps saying I'm handling things, but honestly I feel like I'm fading out.",
            "I laugh when people expect me to, but inside I feel disconnected from everything.",
            "Nothing looks wrong from the outside, but I feel emotionally absent most of the time.",
            "I keep showing up for life, but I don't really feel present in it.",
        ],
        "assistant_prompts": [
            "When did that disconnected feeling start becoming noticeable?",
            "What feels hardest to connect with right now?",
            "Have there been moments lately when you felt more like yourself?",
            "What do you notice in yourself when that numbness gets heavier?",
        ],
        "followups": [
            "It feels like I'm behind glass watching my own life happen.",
            "The scary part is how normal I probably look to everyone else.",
            "I keep waiting to snap out of it, but I don't.",
            "It isn't dramatic, it just feels like my emotions went quiet in a bad way.",
        ],
    },
    {
        "severity": "medium",
        "subtype": "general_distress",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: general_distress; repeated_emergencies: 0; last_session_days_ago: 12",
        "openers": [
            "I feel like I'm falling apart but I can't point to one single reason.",
            "I'm overwhelmed by really basic things and that scares me.",
            "Even small tasks make me want to shut down today.",
            "I keep pushing people away because everything feels too much.",
        ],
        "assistant_prompts": [
            "What feels most unmanageable right now?",
            "Did this build slowly or all at once?",
            "What happened just before things started to feel unbearable today?",
            "When you say falling apart, what does that look like for you?",
        ],
        "followups": [
            "I just feel like my coping is thinner than usual.",
            "It feels like one more thing could push me over the edge emotionally.",
            "I'm not in danger, I just don't feel steady at all.",
            "I want support but I don't even know what words to use.",
        ],
    },
    {
        "severity": "low",
        "subtype": "general_distress",
        "emergency": False,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: general_distress; repeated_emergencies: 0; last_session_days_ago: 18",
        "openers": [
            "I've been pretending I'm fine because I don't want every conversation to turn heavy.",
            "I keep saying I'm just tired, but something feels off in a way I can't explain.",
            "My day looked normal, but I still came home feeling emotionally wrung out.",
            "I don't think I'm in danger, I just feel more fragile than people realize.",
        ],
        "assistant_prompts": [
            "What part of that has felt hardest to say out loud?",
            "When did you first notice that 'off' feeling?",
            "What happens when you stop trying to look okay for everyone else?",
            "Does the fragility feel more emotional, physical, or both?",
        ],
        "followups": [
            "I think hiding it all day is making me feel even more alone.",
            "It's like I spend so much energy seeming okay that I crash afterward.",
            "The feeling is subtle, but it keeps sticking around.",
            "I want support before it gets worse, not after.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "suicidal_ideation",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: suicidal_ideation; repeated_emergencies: 1; last_session_days_ago: 2",
        "openers": [
            "I don't want to do this anymore and I keep thinking everyone would be better without me.",
            "I'm tired in a way that makes me wonder if it would be easier to just stop being here.",
            "I have been trying to hide it, but I keep thinking about ending everything tonight.",
            "I feel like I am running out of reasons to stay.",
        ],
        "assistant_prompts": [
            "Are you having thoughts of hurting yourself right now?",
            "Have those thoughts become more specific today?",
            "Are you alone at the moment?",
            "Have you thought about how you might act on those thoughts?",
        ],
        "followups": [
            "I haven't told anyone, but the thoughts are louder tonight.",
            "I keep looking at the pills in my room and that scares me.",
            "I don't trust myself to just sleep this off.",
            "I wasn't planning to say it, but yes, this feels dangerous tonight.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "suicidal_ideation",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: depression_hopelessness,suicidal_ideation; repeated_emergencies: 1; last_session_days_ago: 3",
        "openers": [
            "I keep thinking everyone would be better off without me and that thought is getting louder.",
            "Part of me wishes I could just disappear and not wake up tomorrow.",
            "I haven't told anyone, but I'm running out of reasons to stay here.",
            "I don't know how to say it directly, but I'm scared of my thoughts tonight.",
        ],
        "assistant_prompts": [
            "When you say those thoughts are getting louder, do they feel dangerous right now?",
            "Are you alone with those thoughts at the moment?",
            "Have you found yourself thinking about a specific way to act on them?",
            "Do you feel able to keep yourself safe tonight?",
        ],
        "followups": [
            "I haven't acted on them, but I don't feel steady with myself.",
            "I keep imagining not being here and it doesn't feel abstract anymore.",
            "It scares me how calm those thoughts can sound in my head.",
            "I think I need someone with me because I don't trust where my mind is going.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "self_harm",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: self_harm; repeated_emergencies: 1; last_session_days_ago: 4",
        "openers": [
            "I keep thinking about cutting again because I need everything in my head to stop.",
            "I don't want to explain it, I just really want to hurt myself right now.",
            "I found myself looking for something sharp and that scared me.",
            "I feel like I might do something to myself if tonight keeps getting worse.",
        ],
        "assistant_prompts": [
            "Have you already hurt yourself tonight?",
            "Is there anything sharp or dangerous near you right now?",
            "Are you alone while this urge is happening?",
            "Can you put some distance between yourself and the object you were thinking about using?",
        ],
        "followups": [
            "I haven't yet but the urge feels strong.",
            "I moved one thing away but I'm still not feeling safe with myself.",
            "I don't trust my own thoughts right now.",
            "Part of me wants help and part of me wants to disappear.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "substance_overdose",
        "emergency": True,
        "prior_summary": "previous_high_crisis: no; prior_subtypes: none; repeated_emergencies: 0; last_session_days_ago: unknown",
        "openers": [
            "I messed up and took way too many pills because I wanted everything to stop for a while.",
            "My friend is barely responding and I think they overdosed.",
            "I drank and took a bunch of tablets and now I feel really wrong.",
            "I thought I could sleep it off, but now I'm dizzy and scared.",
        ],
        "assistant_prompts": [
            "Did someone call emergency services yet?",
            "How long ago did that happen?",
            "Is the person awake and breathing?",
            "Can you tell me if help is already on the way?",
        ],
        "followups": [
            "It was not that long ago and I feel dizzy and scared.",
            "They are breathing but barely and I don't know what to do.",
            "I was hoping I would just sleep, but now I think this is serious.",
            "I think I need urgent help and I waited too long to say that.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "abuse_violence",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: abuse_violence; repeated_emergencies: 1; last_session_days_ago: 5",
        "openers": [
            "My partner shoved me again tonight and I don't know where to go.",
            "Someone in my house is breaking things and threatening me right now.",
            "I think I am in danger but I feel frozen and embarrassed even saying that.",
            "I'm trying to be quiet because the person who hurt me is still nearby.",
        ],
        "assistant_prompts": [
            "Are you physically safe right now?",
            "Can you move to another room or leave the house?",
            "Is the person still near you?",
            "Can you get to someone you trust tonight?",
        ],
        "followups": [
            "I locked myself in the bathroom but I can still hear them outside.",
            "I could maybe go to my car, but I am shaking.",
            "I don't want to make it worse, but I don't feel safe staying here.",
            "I know I should leave but I'm scared of what happens when I move.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "abuse_violence",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: abuse_violence; repeated_emergencies: 1; last_session_days_ago: 3",
        "openers": [
            "I keep thinking I might hurt someone if I lose control tonight.",
            "I'm so angry I keep picturing myself killing him and I know that's not okay.",
            "I said I wanted to kidnap someone just to scare them, and now I'm worried about myself.",
            "I feel out of control and I'm having violent thoughts toward someone close to me.",
        ],
        "assistant_prompts": [
            "Are you with that person right now?",
            "Do you have access to anything you could use to hurt them?",
            "Can you move away from them or leave the situation immediately?",
            "Is there someone who can stay with you or help separate you right now?",
        ],
        "followups": [
            "I'm still close enough that I don't trust myself.",
            "I haven't done anything but I know these thoughts are dangerous.",
            "I need distance because I feel like I could snap.",
            "I don't want to act on it, but the images in my head are getting stronger.",
        ],
    },
    {
        "severity": "high_crisis",
        "subtype": "abuse_violence",
        "emergency": True,
        "prior_summary": "previous_high_crisis: yes; prior_subtypes: abuse_violence; repeated_emergencies: 1; last_session_days_ago: 1",
        "openers": [
            "If I see him tonight I'm scared I might snap and do something awful.",
            "I keep picturing myself making him disappear and I know that's dangerous.",
            "I don't want to hurt anyone, but I can't trust myself around them right now.",
            "My anger feels so out of control that I think someone could get hurt if I stay here.",
        ],
        "assistant_prompts": [
            "Can you get physical distance from that person right now?",
            "Do you have access to anything you could use to hurt them?",
            "Is there someone who can help separate you from this situation immediately?",
            "Are you with the person you're worried about hurting right now?",
        ],
        "followups": [
            "I'm trying to leave because staying close feels dangerous.",
            "I haven't done anything, but I know I need distance right now.",
            "The thoughts feel more intense than I want to admit.",
            "I need help cooling this down before I lose control.",
        ],
    },
]


def build_records(seed: int = 7, repeats_per_case: int = 150) -> list[dict]:
    rng = random.Random(seed)
    records: list[dict] = []

    for case in CASE_LIBRARY:
        for _ in range(repeats_per_case):
            opener = rng.choice(case["openers"])
            prompt = rng.choice(case["assistant_prompts"])
            followup = rng.choice(case["followups"])
            records.append(
                {
                    "conversation_turns": [
                        {"role": "user", "content": opener},
                        {"role": "assistant", "content": prompt},
                        {"role": "user", "content": followup},
                    ],
                    "prior_summary": case["prior_summary"],
                    "severity_label": case["severity"],
                    "subtype_label": case["subtype"],
                    "emergency_flag": case["emergency"],
                }
            )

    rng.shuffle(records)
    return records


def main() -> None:
    records = build_records()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")
    print(f"wrote {len(records)} records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
