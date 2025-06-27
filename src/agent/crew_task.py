from playwright.sync_api import sync_playwright
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from crewai import Agent,Crew,Task
from crewai.tools import BaseTool
# from crewai.tools import tool
# from langchain.tools import tool
from crewai import LLM

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model=genai.GenerativeModel("gemini-2.0-flash")


print("-----------------------------------------")
class LoginTool(BaseTool):
     name: str="login_tool"
     description:str="A tool that logs into Notion using Playwright and returns the resulting message from the Google sign-in page."
     
     def _run(self) -> str:
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=False,slow_mo=2000)
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
                # output=google_page.locator("div.dMNVAe")
                # output1=output.all_inner_texts()
                
                # result="".join(output1)
                # print(result)
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
            return "Error while login"
    
    
login_tool=LoginTool()

# login_tool=Tool.from_function(
#      name="Notion_Logger",
#      func=login_notion,
#      description="You will be instructed to login in to notion website and you should return text which you get from there"
# )

try:
    # Use CrewAI's native LLM class instead of LangChain
    llm = LLM(
        model="gemini/gemini-1.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7
    )
    print("CrewAI LLM initialized successfully")
except Exception as e:
    print(f"LLM initialization failed: {e}")
    raise


main_agent=Agent(
    name="Main",
    role="Conversational assitant",
    goal="You need to answer the basic questions of user and depending on what user asks delegate task to appropriate agent",
    backstory="You are expert in normal conversation and in delegating task to other agents. You have access to agent that can login in into notion website which has all required details to finish login",
    llm=llm,
    verbose=True
)

login_agent=Agent(
     name="NotionWebsiteLogger",
     role="Automates Notion login",
     goal="You should log in into notion webiste and respond correctly in a stuctured way as per text received as a result",
     backstory="You are an expert in login into a website",
    tools=[login_tool],
    llm=llm,
    verbose=True
)




task2=Task(
     description="Go and login for me in notion website",
     expected_output="A message that gives idea about the completion of event in a structured manner.Output should be a object with status, message and details about login task in differnt lines",
     agent=login_agent
)

task1=Task(
    description="Hello.How are you?Can you help me to login into notion website",
    expected_output="Give output as its a normal conversation",
    agent=main_agent
)


crew=Crew(
     agents=[main_agent,login_agent],
     tasks=[task1,task2],
     verbose=True

)

print("Attempting to log in to Notion...")
final_result = crew.kickoff()
print("\n--- Login Automation Result ---")
# print(result)

results = {}
for task in crew.tasks:
    results[task.agent.role] = task.output

# You can now print, return, or send this `results` to the frontend
print("Outputs of each agent:")
for role, output in results.items():
    print(f"{role} → {output}")