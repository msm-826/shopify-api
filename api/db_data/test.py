import pandas as pd

df = pd.read_csv('api/db_data/shopify_orders.csv')

# Assuming 'created_at' column is in string format, convert it to datetime
df['created_at'] = pd.to_datetime(df['created_at'])

# Convert 'created_at' to just the date part
df['date_created'] = df['created_at'].dt.date

# Group by customer email and date, then count orders
grouped_orders = df.groupby(['email', 'date_created']).size().reset_index(name='order_count')

# Filter for customers who have placed more than one order on the same day
multiple_orders_same_day = grouped_orders[grouped_orders['order_count'] > 1]

# Display the result
print(multiple_orders_same_day[['email', 'date_created', 'order_count']])
print('-' * 80)