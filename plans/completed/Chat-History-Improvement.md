For implementation after Chat-History Improvement.md

We should look to make sure we are receiving proper ollama responses that are displayed within oru chat history

You can utilize playwright tooling to go into this and be certain that this is happening.

For example, a lot of these chats have a single input by a user and do not have a single response being shown in the UI. However, 
I don't think this is an ollama issue but an issue within our app thast should be resolved.