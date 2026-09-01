# Agent evaluation

Model: `gemini-3.1-flash-lite` · weather source: `real` · 8 test cases

| Metric | Result |
| --- | --- |
| Tool-selection accuracy | **100%** |
| Answer quality (LLM-as-judge, 1-5) | **4.6** |
| Average latency | 8.1s |
| Tokens (in / out) | 33,320 / 1,841 |
| Cost per 1,000 questions | **$1.39** |

| Question | Expected tools | Tools actually called | Pass | Score |
| --- | --- | --- | :-: | :-: |
| Tell me about surfing in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What can I do in St Ives? | search_travel_info | search_travel_info | yes | 4/5 |
| Suggest three towns with a nice beach in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What is the weather in Falmouth, Cornwall right now? | weather_forecast | weather_forecast | yes | 5/5 |
| Compare the weather in Newquay and Penzance | weather_forecast | weather_forecast, weather_forecast | yes | 5/5 |
| Suggest two Cornwall beach towns with nice weather | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast | yes | 5/5 |
| I want a surfing town in Cornwall where it is not raining today | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast, weather_forecast, weather_forecast | yes | 5/5 |
| Which Cornwall coastal town should I visit today based on the weather? | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast, weather_forecast, weather_forecast | yes | 5/5 |
