# Agent evaluation

Model: `gemini-3.1-flash-lite` · weather source: `real` · 31 test cases

| Metric | Result |
| --- | --- |
| Tool-selection accuracy | **100%** |
| Answer quality (LLM-as-judge, 1-5) | **4.6** |
| Average latency | 5.2s |
| Tokens (in / out) | 76,895 / 6,480 |
| Cost per 1,000 questions | **$0.93** |

| Question | Expected tools | Tools actually called | Pass | Score |
| --- | --- | --- | :-: | :-: |
| Tell me about surfing in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What can I do in St Ives? | search_travel_info | search_travel_info | yes | 4/5 |
| Suggest three towns with a nice beach in Cornwall | search_travel_info | search_travel_info | yes | 4/5 |
| What are the best surf spots in Newquay? | search_travel_info | search_travel_info, search_travel_info | yes | 4/5 |
| Tell me about the history of Tintagel | search_travel_info | search_travel_info | yes | 4/5 |
| What is there to do at the Eden Project? | search_travel_info | search_travel_info | yes | 3/5 |
| Is St Michael's Mount worth visiting? | search_travel_info | search_travel_info | yes | 4/5 |
| What food is Cornwall famous for? | search_travel_info | search_travel_info | yes | 5/5 |
| How do I get around Cornwall without a car? | search_travel_info | search_travel_info | yes | 4/5 |
| What are some quiet fishing villages in Cornwall? | search_travel_info | search_travel_info | yes | 4/5 |
| Tell me about Land's End | search_travel_info | search_travel_info | yes | 5/5 |
| Tell me literally anything interesting about Cornwall | search_travel_info | search_travel_info | yes | 3/5 |
| What is the weather in Falmouth, Cornwall right now? | weather_forecast | weather_forecast | yes | 5/5 |
| Compare the weather in Newquay and Penzance | weather_forecast | weather_forecast, weather_forecast | yes | 5/5 |
| What's the weather like in Padstow today? | weather_forecast | weather_forecast | yes | 5/5 |
| Current temperature in Truro? | weather_forecast | weather_forecast | yes | 5/5 |
| Is it raining in Bude right now? | weather_forecast | weather_forecast | yes | 5/5 |
| What's the wind speed in Fowey? | weather_forecast | weather_forecast | yes | 5/5 |
| Weather forecast for Looe | weather_forecast | weather_forecast | yes | 5/5 |
| How warm is Mousehole today? | weather_forecast | weather_forecast | yes | 5/5 |
| Compare the weather in St Mawes and Port Isaac | weather_forecast | weather_forecast, weather_forecast, search_travel_info, weather_forecast | yes | 5/5 |
| Compare weather between Truro and Bodmin | weather_forecast | weather_forecast, weather_forecast | yes | 5/5 |
| What is the weather in a town that does not exist, Xyzzyville? | weather_forecast | weather_forecast | yes | 5/5 |
| Suggest two Cornwall beach towns with nice weather | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast | yes | 5/5 |
| I want a surfing town in Cornwall where it is not raining today | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast, weather_forecast, weather_forecast | yes | 5/5 |
| Which Cornwall coastal town should I visit today based on the weather? | search_travel_info, weather_forecast | search_travel_info, weather_forecast, weather_forecast, weather_forecast, weather_forecast | yes | 5/5 |
| Suggest a fishing village in Cornwall and tell me its current weather | search_travel_info, weather_forecast | search_travel_info, weather_forecast | yes | 5/5 |
| I want to visit a historic Cornwall town - suggest one and check if it is sunny there today | search_travel_info, weather_forecast | search_travel_info, weather_forecast | yes | 5/5 |
| Recommend a town near the Eden Project and give me its current forecast | search_travel_info, weather_forecast | search_travel_info, weather_forecast | yes | 5/5 |
| Is Mevagissey a good place for seafood, and how is the weather there now? | search_travel_info, weather_forecast | search_travel_info, weather_forecast | yes | 5/5 |
| What outdoor activities can I do in Perranporth today given the weather? | search_travel_info, weather_forecast | weather_forecast, search_travel_info | yes | 5/5 |
