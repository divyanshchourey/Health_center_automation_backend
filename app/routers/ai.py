from fastapi import APIRouter, HTTPException
from groq import Groq
import os
from app.schemas import ChatInput

router = APIRouter(prefix="/ai", tags=["AI Assistant"])
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


chat_histories = {}

@router.post("/analyze")
async def analyze_health_query(data: ChatInput):
    user_id = data.user_id
    

    if user_id not in chat_histories:
        chat_histories[user_id] = []


    messages = [{"role": "system", "content": data.system_prompt}]
    

    messages.extend(chat_histories[user_id][-10:])

    messages.append({"role": "user", "content": data.message})

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5,
        )
        
        ai_reply = completion.choices[0].message.content


        chat_histories[user_id].append({"role": "user", "content": data.message})
        chat_histories[user_id].append({"role": "assistant", "content": ai_reply})
        

        if len(chat_histories[user_id]) > 14:
            chat_histories[user_id] = chat_histories[user_id][-14:]

        return {"reply": ai_reply}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))