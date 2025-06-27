from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from crewai import Crew
from src.database.database import SessionLocal
from pydantic import BaseModel
from playwright.sync_api import sync_playwright
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from crewai import Agent,Crew,Task
from crewai.tools import BaseTool
from crewai import LLM
from fastapi.concurrency    import run_in_threadpool
import asyncio  
import traceback
load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model=genai.GenerativeModel("gemini-2.0-flash")

class LoginTool(BaseTool):
     name: str="Login_tool"
     description:str="A tool that automates logging into Notion website using Playwright and returns the resulting message from the Google sign-in page."
     
     def _run(self) -> str:
        print("🔧 LoginTool _run triggered")
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=True,slow_mo=2000)
                context=browser.new_context()
                page=context.new_page()
                page.goto("https://www.notion.com/")
                login=page.get_by_role("link", name="Log in", exact=False)

                print(login)
                login.click()
                continuwithgoogle=page.locator("div.tx-uiregular-14-med",has_text="Continue with Google")
                print(continuwithgoogle)
                continuwithgoogle.highlight()

                with context.expect_page() as new_page_info:    
                    continuwithgoogle.click()
                google_page=new_page_info.value
                # print(google_page)
                input_box = google_page.locator("input[type='email']")
                if input_box.count() == 0:
                    print("❌ Input box not found")
                else:
                    print("✅ Input box found")
                input_box.fill("aryanj260506@gmail.com")

                Next=google_page.get_by_text("Next")
                Next.click()
                time.sleep(5)
                google_page.screenshot(path="output.png")
                with open("output.png","rb") as f:
                    image_bytes=f.read()

                response=model.generate_content([
                    {
                        "mime_type":"image/png",
                        "data":image_bytes
                    },
                    "Try to extract text from image and interpret whether the login was sucessful or not and clearly state if successful or unsuccessful and also what went wrong."
                ])

                result=response.text
                print("result of tool : " ,result)
                return result
                
                
        
        except Exception as e:
   
            traceback.print_exc()
            return f"Error while login: {e}"


login_tool=LoginTool()

try:
    # Use CrewAI's native LLM class instead of LangChain
    llm = LLM(
        model="gemini/gemini-2.0-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7
    )
    print("CrewAI LLM initialized successfully")
except Exception as e:
    print(f"LLM initialization failed: {e}")



#Make agents

main_agent = Agent(
    role="Conversational AI Assistant",
    goal="Respond helpfully and naturally to the user. If the user mentions 'login' or 'Notion', inform them that a secure agent exists to handle it. Only proceed if the user explicitly agrees.",
    backstory="You are the primary assistant. You specialize in general conversation, not direct logins. There is a secure login agent available to log into Notion when the user agrees.",
    verbose=True,
    tools=[login_tool],
    llm=llm
)

login_agent=Agent(
    role="Automate Notion Login",
    goal="You should log in into notion webiste and respond correctly in a stuctured way as per text received as a result",
    backstory="You are an expert in your job",
    tools=[login_tool],
    llm=llm,
    verbose=True
)
#  Yes, wherever you want to send dynamic input to the agent, you should use kickoff(inputs={"your_key": your_value}).
# 🧠 Then use that key (like {user_input}) in your Task description to drive logic.

chat_task = Task(
    agent=main_agent,
    description="""
            You are a helpful assistant. Respond appropriately to the following user message:

            "{user_input}"

            If it's a normal conversation (greeting, question, etc.), reply accordingly.

            If the user mentions Notion or asks to log in, tell them:
            - You are not the one who logs in, but there's a secure login agent who can.
            - Ask for consent to proceed.
            - Say: 'Would you like me to ask the login agent to do that for you? Reply with Y to proceed.'

            Only mention the login agent if Notion/login is brought up by the user.
            If "{user_input}" is Y/y/yes/Yes then only delegate task to login_agent for doing the login.

            Otherwise, continue the conversation as a helpful AI assistant.
            """,
    expected_output="Your natural or intent-aware response as a string",
    output_key="main_response"
)

login_task = Task(
    agent=login_agent,
    description="Login to Notion using playwright via login_tool",
    expected_output="A message that gives idea about the completion of event in a structured manner.Output should have  status, message and details about login task in differnt lines in a paragraph",
)

main_crew=Crew(
    agents=[main_agent,login_agent],
    tasks=[chat_task],
    verbose=True
)

login_crew=Crew(
            agents=[login_agent],
            tasks=[login_task],
            verbose=True
        )

class User_Input(BaseModel):
    usermsg:str

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

chatRouter=APIRouter()


# usermsg:str direct aise loge to error dega kyuki input me frontedn se {usermsg:"Hello"} aisa aayega


async def chatResponse(input: User_Input, db: Session = Depends(get_db)):
    print(input.usermsg)
    usermsg = input.usermsg.strip().lower()

    if usermsg in ["y", "yes"]:
        response = await run_in_threadpool(login_crew.kickoff)
        print("Login Crew Response:", response)
        return response
    else:
        response = await run_in_threadpool(main_crew.kickoff, inputs={"user_input": input.usermsg})
        print("Main Crew Response:", response)
        return response



@chatRouter.post("/")
async def test(input:dict):
    print(input["usermsg"])
    usermsg1=input["usermsg"]
    input_data = User_Input(usermsg=usermsg1)
    response=await chatResponse(input_data)
    return response



    

# asyncio.run(test({"usermsg":"Y"}))
    


# No need for checking logged in hai ki yahi frontend pe hi check kar liye using useEffect
