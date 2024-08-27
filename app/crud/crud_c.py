from typing import List, Optional
from bson import ObjectId
from ..database import company_collection
from ..models.model import Company
from pymongo import ReturnDocument


def company_helper(company) -> dict:
    return {
        # "id": str(company["_id"]),
        "company_name": company["company_name"],
        "location": company["location"],
        "est_year": company["est_year"],
        "user_ids": [str(user_id) for user_id in company.get("user_ids", [])],
    }



async def retrieve_companies() -> List[Company]:
    companies = []
    async for company in company_collection.find():
        companies.append(company_helper(company))
    return companies



async def add_company(company_data: dict) -> Company:
    company_data.pop('_id', None)  
    company_data['user_ids'] = []
    company = await company_collection.insert_one(company_data)
    new_company = await company_collection.find_one({"_id": company.inserted_id})
    return company_helper(new_company)



async def retrieve_company(id: str) -> Company:
    company = await company_collection.find_one({"_id": ObjectId(id)})
    if company:
        return company_helper(company)
    return None



async def update_company(id: str, data: dict) -> Optional[Company]:
    company = await company_collection.find_one_and_update(
        {"_id": ObjectId(id)},
        {"$set": data},
        return_document=ReturnDocument.AFTER
    )
    if company:
        return company_helper(company)
    



async def delete_company(id: str) -> bool:
    company = await company_collection.delete_one({"_id": ObjectId(id)})
    return bool(company.deleted_count)

async def delete_all_companies() -> bool:
    result = await company_collection.delete_many({})
    return result.deleted_count > 0


# async def update_companies(query: dict, update_data: dict) -> List[Company]:
#     updated_companies = []
#     async for company in company_collection.find(query):
#         updated_company = await company_collection.find_one_and_update(
#             {"_id": company["_id"]},
#             {"$set": update_data},
#             return_document=ReturnDocument.AFTER
#         )
#         if updated_company:
#             updated_companies.append(company_helper(updated_company))
#     return updated_companies

