from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from src.database.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
from src.models.user_model import User
from src.controllers import auth
from sqlalchemy import or_
from src.schema import schema
from typing import List
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login") # tokenurl is token kis jagah se aa raha hai kuch bhi likh do chal jayenga par empty nahi hona chiaye
#ye automactically authetication header me se bearer token me se token nikal ke deta hai
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

userRouter=APIRouter()

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    print("Validating Token")
    payload=auth.validate_token(token)
    # object with field payload.username payload.userid
    print("Validating_Token: Payload : ",payload)
    print(payload.get("username"))
    if not payload.get("username") and not payload.get("userid"):
        raise HTTPException(status_code=401,detail="Invalid Token.Login Again")
    
    user=db.query(User).filter(or_(
        User.username==payload.get("username"),
        User.id==payload.get("userid")
    )).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not Found!")
    
    return user

    


@userRouter.get("/getCurrentUser",response_model=schema.UserOutput)
def getCurrentUser(current_user:User=Depends(get_current_user)):
    return current_user

#current_user jaruri hai to check logged in user hi hai 
@userRouter.get("/getAllUser",response_model=List[schema.UserOutput])
def get_all_user(current_user:User=Depends(get_current_user),db:Session=Depends(get_db)):
    print("Fetching All Users...")
    users=db.query(User).all()
    return users




