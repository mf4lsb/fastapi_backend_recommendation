from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import collaborative_filtering_algorithm as cf

app = FastAPI()

@app.get('/api/v1/menu/{token}/{id}/recommendation')
# async def get_recommendation(token: str, id: Optional[str] = None):
async def get_recommendation_w_token(token: str, id: str):
    df = cf.read_dataset()
    interactions_matrix = cf.user_item_matrix(df)

    response = requests.get('https://api.eataja.com/api/user/get-order-by-user-id', headers={
        'Authorization': "Bearer " + token
    })

    result = []
    print(response.status_code)

    if len(response.json()['data']) == 0:
        order_status = 0
        for i in range(len(cf.top_five_recommend_menu(df))):
            result.append(cf.top_five_recommend_menu(df).index[i])
    else:
        order_status = len(response.json()['data'])
        result = cf.recommendations(id, 5, interactions_matrix, interactions_matrix)

    return {"id": id, "order_status": order_status, "recommendation": result}


@app.get('/api/v1/menu/{id}/recommendation')
async def get_recommendation(id: str):
    df = cf.read_dataset()
    interactions_matrix = cf.user_item_matrix(df)

    recommendation = []
    recommendation = cf.recommendations(id, 5, interactions_matrix, interactions_matrix)

    recommendation_data = cf.get_menu(df, recommendation)

    return {"id": id, "recommendation": recommendation_data}

@app.get('/api/v1/menu/top-five')
async def top_five():
    df = cf.read_dataset()

    recommendation = list(cf.top_five_recommend_menu(df).index)

    recommendation_data = cf.get_menu(df, recommendation)

    return {"recommendation": recommendation_data}


# MAIN
df = cf.read_dataset()
interactions_matrix = cf.user_item_matrix(df)

result = []

result = cf.recommendations("12703b56-b204-4d37-b517-a68c01290306", 5, interactions_matrix, interactions_matrix)
data = cf.get_menu(df, result)
print(data)