from typing import List, Optional, Union
from bson.objectid import ObjectId
from ..database import user_collection, company_collection
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
from ..models.model import User
from ..hash import hash_password 

def user_details(user) -> dict:
    return {
        "username": user["username"],
        "email": user["email"],
        "full_name": user.get("full_name"),
        "hashed_password": user["hashed_password"],
        "company_id": user.get("company_id"),
        "designation":user["designation"],
        "salary":user["salary"],
    }

async def retrieve_users() -> List[User]:
    users = []
    async for user in user_collection.find():
        users.append(user_details(user))
    return users


async def add_user(user_data: dict) -> Union[User, dict]:
    try:
        user_data.pop('_id', None)
        user_data['hashed_password'] = hash_password(user_data['hashed_password'])
        user = await user_collection.insert_one(user_data)
        new_user = await user_collection.find_one({"_id": user.inserted_id})
        if user_data.get('company_id'):
            await company_collection.update_one(
                {"_id": ObjectId(user_data['company_id'])},
                {"$addToSet": {"user_ids": str(user.inserted_id)}}
            )
        return user_details(new_user)
    except DuplicateKeyError as e:
        return {"message": f"{e.details['keyValue']} already exists"}


async def retrieve_user(id: str) -> User:
    user = await user_collection.find_one({"_id": ObjectId(id)})
    if user:
        return user_details(user)
    return None


async def retrieve_user_by_username(username: str) -> Optional[User]:
    user = await user_collection.find_one({"username": username})
    if user:
        return user_details(user)  
    return None

     

async def update_user(id: str, data: dict) -> Optional[Union[dict, str]]:
    object_id = ObjectId(id)
    
    if 'email' in data:
        existing_user = await user_collection.find_one({"email": data['email']})
        if existing_user and str(existing_user["_id"]) != id:
            return {"message": "Email already exists"}
    
    if 'hashed_password' in data:
        data['hashed_password'] = hash_password(data['hashed_password'])
    
    current_user = await user_collection.find_one({"_id": object_id})
    if current_user and data.get('company_id') and current_user.get('company_id') != data['company_id']:
        await company_collection.update_one(
            {"_id": ObjectId(current_user['company_id'])},
            {"$pull": {"user_ids": id}}
        )
        await company_collection.update_one(
            {"_id": ObjectId(data['company_id'])},
            {"$addToSet": {"user_ids": id}}
        )
    
    update_user = await user_collection.find_one_and_update(
        {"_id": object_id},
        {"$set": data},
        return_document=ReturnDocument.AFTER
    )
    if update_user:
        return user_details(update_user)
    
    return {"message": "Data is updated successfully"}



async def delete_user(id: str) -> Optional[bool]:
    object_id = ObjectId(id)
    user = await user_collection.find_one({"_id": object_id})
    print("4444444444444444444444444444444444444444444444444444444444")
    if user and user.get('company_id'):
        await company_collection.update_one(
            {"_id": ObjectId(user['company_id'])},
            {"$pull": {"user_ids": id}}
        )
    delete_result = await user_collection.delete_one({"_id": object_id})
    if delete_result.deleted_count == 1:
        return True
    return False


