import pandas as pd
import numpy as np
import requests
from sklearn.metrics.pairwise import cosine_similarity


def read_dataset():
    df_order_dummy = pd.read_csv('data/df_order_dummy.csv')

    # Change type data user_id to string
    df_order_dummy['user_id'] = df_order_dummy['user_id'].astype(str)

    # Drop mitra_id on df_dummy_order
    df_order_dummy.drop(labels="mitra_id", axis=1, inplace=True)

    # Request All order in API EatAja
    response = requests.get('https://api.eataja.com/api/mitra/get-all-order-for-mitra')

    if response.status_code == 200:
        body = response.json()['data']
    else:
        return df_order_dummy.reset_index()
    
    # Cleaning Data
    deleteMitraId = ['6bd72c87-c1b4-465e-beda-b593a5c871bc', '6732496e-277a-4c86-97fa-6c113b497391', '0d93f781-7f1a-4c42-a056-683fd8866793', 'b8b4935b-b9aa-4d56-ac51-37c43c40ab8e']
    response_menu = requests.get('https://api.eataja.com/api/mitra/all-menu').json()['data']

    list_menu_id = []
    for i in range(len(response_menu)):
        if response_menu[i]['mitra_id'] in deleteMitraId:
            list_menu_id.append(response_menu[i]['id'])
    
    df_order_api = pd.DataFrame(None)
    df_order_api = pd.DataFrame(columns = ['user_id', 'menu_id', 'rating'])

    for order in body:
        for i in range(len(order['menu_order'])):
            if order['menu_order'][i]['menu_id'] in list_menu_id:
                pass
            else:
                if order['rating'] == None:
                    new_row = {'user_id':order['user_id'], 'menu_id':order['menu_order'][i]['menu_id'], 'rating':np.random.randint(3,6)}
                else:
                    new_row = {'user_id':order['user_id'], 'menu_id':order['menu_order'][i]['menu_id'], 'rating':order['rating']}
                df_order_api = df_order_api.append(new_row, ignore_index=True)
    # End cleaning data
    
    # Concat df_order_dummy and df_order_api for general Dataset
    df_order = pd.concat([df_order_dummy, df_order_api], axis=0)

    return df_order.reset_index()
    
        

    # # Get all menu
    # response_menu = requests.get('https://api.eataja.com/api/mitra/all-menu')
    # data_menu = response_menu.json()['data']

    # # Data all menu to catch mitra_id
    # list_mitra_id = []
    # for data in data_menu:
    #     list_mitra_id.append(data['mitra_id'])

    # list_mitra_id = set(list_mitra_id)
    # list_mitra_id = list(list_mitra_id)

    # data_order = []
    # for data in list_mitra_id:
    #     response_order = requests.get("https://api.eataja.com/api/get-order-mitra/" + data)
    #     data_order.append(response_order.json()['data'])

    # df_order_api = pd.DataFrame(columns = ['user_id', 'mitra_id', 'menu_id', 'rating'])
    # for i in range(len(list_mitra_id)):
    #     for data in data_order[i]:
    #         for order in data['menu_order']:
    #             if data['rating'] == None:
    #                 new_row = {'user_id':data['user_id'], 'mitra_id':list_mitra_id[i], 'menu_id':order['menu_id'], 'rating':np.random.randint(3,6)}
    #             else:
    #                 new_row = {'user_id':data['user_id'], 'mitra_id':list_mitra_id[i], 'menu_id':order['menu_id'], 'rating':data['rating']}
    #             df_order_api = df_order_api.append(new_row, ignore_index=True)
    
    # df = pd.concat([df_order_dummy, df_order_api], axis=0)
    # df['user_id'] = df['user_id'].astype(str)
    # return df.reset_index()

def user_item_matrix(df):
    interactions_matrix = df.reset_index().pivot_table(index='user_id', columns='menu_id', values='rating', aggfunc='first')    
    interactions_matrix = interactions_matrix.fillna(0)
    return interactions_matrix

def similar_users(user_id, interactions_matrix):
    # compute similarity of each user to the provided user
    similarity = []
    for user in interactions_matrix.index:
        sim = cosine_similarity([interactions_matrix.loc[user_id]], [interactions_matrix.loc[user]])
        similarity.append((user, sim))
    
    # sort by similarity
    similarity.sort(key=lambda x: x[1], reverse=True)
    
    # create list of just the user ids
    most_similar_users = [tup[0] for tup in similarity]
    
    # create list of similarity score
    similarity_score = [tup[1] for tup in similarity]
    
    # remove the user's own id
    most_similar_users.remove(user_id)
    
    # remove the user's own similarity score
    similarity_score.remove(similarity_score[0])
       
    return most_similar_users, similarity_score

def recommendations(user_id, num_of_menus, user_item_interactions, interactions_matrix):
    # find the most similar users to the user_id for which we want to recommend menus
    most_similar_users = similar_users(user_id, user_item_interactions)[0]
    
    # find out those menus which this user has already interacted with
    menu_ids = set(list(interactions_matrix.columns[np.where(interactions_matrix.loc[user_id] > 0)]))
    
    # create an empty list to store the recommended menus
    recommendations = []
    
    # copy those menus which are already interacted by user_id
    already_interacted = menu_ids.copy()
    
    # loop through each similar user from the list of most_similar_users
    for similar_user in most_similar_users:
        
        # implement the below code till the length of recommended menus does not become equal to num_of_menus
        if len(recommendations) < num_of_menus:
            
            # store all the menus interacted by each similar user to user_id
            similar_user_menu_ids = set(list(interactions_matrix.columns[np.where(interactions_matrix.loc[str(similar_user)] > 0)]))
            
            # add those menus in the recommended list which are present in similar_user_menu_ids but not present in already_interacted
            recommendations.extend(list(similar_user_menu_ids.difference(already_interacted)))
            
            # now add all those menus into already_interacted which we already added in recommendations
            already_interacted = already_interacted.union(similar_user_menu_ids)
            
        else:
            break
    
    return recommendations[:num_of_menus]

def top_five_recommend_menu(df):
    return df['menu_id'].value_counts()[:5]

def get_menu(df, recommendation):
    df_menu = pd.read_csv('data/df_menu.csv')
    
    recommendation_data = []
    for id in recommendation:
        temp = {
            "mitra_id": df_menu[df_menu['menu_id'] == id]['mitra_id'].values[0],
            "id": id,
            "name": df_menu[df_menu['menu_id'] == id]['menu_name'].values[0],
            "description": df_menu[df_menu['menu_id'] == id]['menu_description'].values[0],
            "average_rating": f"{df[df['menu_id'] == id]['rating'].mean():,.2f}",
            "photo": df_menu[df_menu['menu_id'] == id]['photo'].values[0],
        }
        recommendation_data.append(temp)
    return recommendation_data

    
