from fastapi import FastAPI, HTTPException, status, Body, Depends, Query
from fastapi_pagination.links import Page
from fastapi_pagination import add_pagination
from fastapi_pagination.ext.motor import paginate as motor_paginate
from typing import List
from .models.model import User, UpdateUser, Company, UpdateCompany, Token
from .crud.crud_u import add_user, retrieve_user, retrieve_users,update_user, delete_user, user_details, retrieve_user_by_username
from .crud.crud_c import add_company, retrieve_company, retrieve_companies, update_company, delete_company, delete_all_companies
from .auth import  get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from .database import user_collection , company_collection
from bson import ObjectId, errors
from datetime import datetime



app = FastAPI()
add_pagination(app)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await user_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    if "username" not in current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data. 'username' not found."
        )
    
    user = await user_collection.find_one({"email": current_user["username"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )
    

    company_details = None
    if user.get("company_id"):
        try:
            company_id = ObjectId(user["company_id"])
            company = await company_collection.find_one({"_id": company_id})
            print("i am here 00")
            if company:
                company_details = {
                    "id": str(company["_id"]),
                    "company_name": company["company_name"],
                    "location": company["location"],
                    "est_year": company["est_year"]
                }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company ID."
            ) 
    if not user.get("created_at"):
        user["created_at"] = datetime.now()
    if not user.get("updated_at"):
        user["updated_at"] = datetime.now()
            

    user_info = user_details(user)
    user_info.update({
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "company_details": company_details
    })
    return user_info


##---------------------------------------------------------------------------------------

@app.get("/users", status_code=status.HTTP_200_OK, response_model=Page)
async def get_users():
    try:
        paginated_users = await motor_paginate(user_collection)
        for user in paginated_users.items:
            user['id'] = str(user.pop('_id'))
            user.pop('password', None)
        return paginated_users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Page not found"
        )

###--------------------------------------------------------------------------

@app.get("/users/search", status_code=status.HTTP_200_OK,response_model=List[User])
async def search_users_by_designation(search_term: str = Query(..., min_length=1),current_user: dict = Depends(get_current_user)):
    print("I am here 01......")
    users_cursor = user_collection.find({
        "$or": [
            {"username": {"$regex": search_term, "$options": "i"}},
            {"email": {"$regex": search_term, "$options": "i"}},
            {"full_name": {"$regex": search_term, "$options": "i"}},
            {"designation": {"$regex": search_term, "$options": "i"}},
            {"salary": {"$regex": search_term, "$options": "i"}},

        ]
    })
    users = await users_cursor.to_list(length=None)
    
    if not users:
        raise HTTPException(
            status_code=404,
            detail="No users found with the given search field"
        )
  
    user_list = [user_details(user) for user in users]
    return user_list




@app.get("/user/{username}", status_code=status.HTTP_200_OK, response_model=User)
async def get_user_by_username(username: str):
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    user = await retrieve_user_by_username(username)
    print("user : ", user)
    if user:
        return user
    raise HTTPException(status_code=404, detail=f"User with username {username} not found")

@app.get("/users/{id}", status_code=status.HTTP_200_OK,  response_model=User)
async def get_user(id: str):
    print("#######################################", id)
    try:
        object_id = ObjectId(id)
    except errors.InvalidId:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {id}")
    
    user = await retrieve_user(object_id)
    if user:
        return user
    raise HTTPException(status_code=404, detail=f"User {id} not found")




@app.post("/users", status_code=status.HTTP_201_CREATED, response_model=User)
async def create_user(user: User):
    user_data = user.model_dump()
    user_data.pop("id", None)
    new_user = await add_user(user_data)
    if isinstance(new_user, dict) and "message" in new_user:
        raise HTTPException(status_code=400, detail=new_user["message"])
    return new_user




@app.put("users/{id}", status_code=status.HTTP_201_CREATED, response_model=User)
async def update_user_route(id: str, user: UpdateUser = Body(...), current_user: dict = Depends(get_current_user)):
    user_data = user.model_dump(exclude_unset=True)
    updated_user = await update_user(id, user_data)
    if isinstance(updated_user, dict) and "message" in updated_user:
        raise HTTPException(status_code=400, detail=updated_user["message"])
    if updated_user:
        return updated_user
    raise HTTPException(status_code=404, detail=f"User {id} not found")



@app.delete("/users/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def delete_user_route(id: str):
    try:
        user_object_id = ObjectId(id)
        user = await user_collection.find_one({"_id": user_object_id})
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {id} not found")
        

        delete_result = await user_collection.delete_one({"_id": user_object_id})
        if delete_result.deleted_count == 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete user")
        
        
        if "company_id" in user:
            await company_collection.update_one(
                {"_id": ObjectId(user["company_id"])},
                {"$pull": {"user_ids": str(user_object_id)}}
            )

        return {"message": "User deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


###------------------------------------------------------------------------------------------



@app.get("/companies", status_code=status.HTTP_200_OK, response_model=List[Company])
async def get_companies(current_user: dict = Depends(get_current_user)):
    companies = await retrieve_companies()
    print("company :- ", companies)
    return companies



@app.get("/companies/{id}", status_code=status.HTTP_200_OK, response_model=Company)
async def get_company(id: str):
    company = await retrieve_company(id)
    if company:
        return company
    raise HTTPException(status_code=404, detail=f"Company {id} not found")




@app.post("/companies/", status_code=status.HTTP_201_CREATED, response_model=Company)
async def create_company(company: Company, current_user: dict = Depends(get_current_user)):
    company_data = company.model_dump()
    company_data.pop("id", None)
    new_company = await add_company(company_data)
    return new_company



@app.put("/companies/{id}", status_code=status.HTTP_200_OK, response_model=Company)
async def update_company_route(id: str, company: UpdateCompany = Body(...), current_user: dict = Depends(get_current_user)):
    company_data = company.model_dump(exclude_unset=True)
    updated_company = await update_company(id, company_data)
    if updated_company:
        return updated_company
    raise HTTPException(status_code=404, detail=f"Company {id} not found")



@app.delete("/companies/{id}", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def delete_company_route(id: str):
    deleted = await delete_company(id)
    if deleted:
        return {"message": "Company deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Company {id} not found")


#---Aug 08th---

@app.delete("/companies", status_code=status.HTTP_202_ACCEPTED, response_model=dict)
async def delete_all_companies_route(current_user: dict = Depends(get_current_user)):
    print("POOOOOOOOOOOOOOOOOOOOOOOOOOO")
    deleted = await delete_all_companies()
    if deleted:
        return {"message": "All companies deleted successfully"}
    raise HTTPException(status_code=404, detail="No companies found to delete")











