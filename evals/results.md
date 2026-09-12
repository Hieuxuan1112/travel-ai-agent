# Agent evaluation

Model: `gemini-3.1-flash-lite` · weather source: `real` · 9 test cases

| Metric | Result |
| --- | --- |
| Tool-selection accuracy | **100%** |
| Answer quality (LLM-as-judge, 1-5) | **4.7** |
| Average latency | 14.2s |
| Tokens (in / out) | 29,272 / 1,910 |
| Cost per 1,000 questions | **$1.13** |

| Question | Expected tools | Tools actually called | Pass | Score |
| --- | --- | --- | :-: | :-: |
| Tell me about surfing in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What can I do in St Ives? | search_travel_info | search_travel_info | yes | 4/5 |
| Suggest three towns with a nice beach in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What is the weather in Falmouth, Cornwall right now? | weather_forecast | weather_forecast | yes | 5/5 |
| Compare the weather in Newquay and Penzance | rank_town_candidates | rank_town_candidates | yes | 5/5 |
| Suggest two Cornwall beach towns with nice weather | rank_town_candidates, search_travel_info | search_travel_info, rank_town_candidates | yes | 5/5 |
| I want a surfing town in Cornwall where it is not raining today | rank_town_candidates, search_travel_info | search_travel_info, rank_town_candidates | yes | 5/5 |
| Which Cornwall coastal town should I visit today based on the weather? | rank_town_candidates, search_travel_info | search_travel_info, rank_town_candidates | yes | 5/5 |
| Suggest two Cornwall beach towns colder than 0 degrees Celsius right now | rank_town_candidates, search_travel_info | search_travel_info, rank_town_candidates | yes | 5/5 |
