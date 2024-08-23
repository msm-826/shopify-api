import pandas as pd
from pymongo import MongoClient

connection_string = "mongodb+srv://db_user_read:LdmrVA5EDEv4z3Wr@cluster0.n10ox.mongodb.net/RQ_Analytics?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(connection_string)

db = client.RQ_Analytics

def get_data_as_df(collection_name):
    collection = db[collection_name]
    data = list(collection.find())
    df = pd.DataFrame(data)
    return df

df_customers = get_data_as_df('shopifyCustomers')
df_products = get_data_as_df('shopifyProducts')
df_orders = get_data_as_df('shopifyOrders')

df_customers.to_csv('api/db_data/shopify_customers.csv', index=False)
df_products.to_csv('api/db_data/shopify_products.csv', index=False)
df_orders.to_csv('api/db_data/shopify_orders.csv', index=False)
