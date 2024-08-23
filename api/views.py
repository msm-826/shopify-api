from rest_framework.views import APIView
from rest_framework.response import Response
from .mongodb_client import get_collection

def get_date_format(interval):
    formats = {
        'daily': '%Y-%m-%d',
        'monthly': '%Y-%m',
        'yearly': '%Y',
        'quarterly': None
    }
    return formats.get(interval, '%Y-%m-%d')

class TotalSalesOverTime(APIView):
    def get(self, request):
        interval = request.GET.get('interval', 'daily')
        date_format = get_date_format(interval)
        
        pipeline = [
            {
                "$addFields": {
                    "date_field": {"$toDate": "$created_at"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$cond": {
                            "if": { "$eq": [interval, 'quarterly'] },
                            "then": {
                                "$concat": [
                                    {"$toString": {"$year": {"$toDate": "$created_at"}}},
                                    "-Q",
                                    {"$toString": {"$add": [
                                        {"$floor": {"$divide": [{"$subtract": [{"$month": {"$toDate": "$created_at"}}, 1]}, 3]}},
                                        1
                                    ]}}
                                ]
                            },
                            "else": {
                                "$dateToString": {
                                    "format": date_format,
                                    "date": "$date_field"
                                }
                            }
                        }
                    },
                    "total_sales": {"$sum": {"$toDouble": "$total_price_set.shop_money.amount"}}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        orders = get_collection('shopifyOrders')
        sales_data = list(orders.aggregate(pipeline))

        return Response(sales_data)
    
class NewCustomersOverTime(APIView):
    def get(self, request):
        interval = request.GET.get('interval', 'daily')
        date_format = get_date_format(interval)

        pipeline = [
            {
                "$addFields": {
                    "date_field": {
                        "$toDate": "$created_at"
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$cond": {
                            "if": { "$eq": [interval, 'quarterly'] },
                            "then": {
                                "$concat": [
                                    {"$toString": {"$year": {"$toDate": "$created_at"}}},
                                    "-Q",
                                    {"$toString": {"$add": [
                                        {"$floor": {"$divide": [{"$subtract": [{"$month": {"$toDate": "$created_at"}}, 1]}, 3]}},
                                        1
                                    ]}}
                                ]
                            },
                            "else": {
                                "$dateToString": {
                                    "format": date_format,
                                    "date": "$date_field"
                                }
                            }
                        }
                    },
                    "new_customers": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        customers = get_collection('shopifyCustomers')
        customers_data = list(customers.aggregate(pipeline))
        
        return Response(customers_data)
    
class RepeatCustomers(APIView):
    def get(self, request):
        interval = request.GET.get('interval', 'daily')
        
        date_format = {
            'daily': '%Y-%m-%d',
            'monthly': '%Y-%m',
            'quarterly': '%Y-Q%q',
            'yearly': '%Y'
        }.get(interval, '%Y-%m-%d')

        pipeline = [
            {
                "$addFields": {
                    "date_field": {"$toDate": "$created_at"}
                }
            },
            {
                "$group": {
                    "_id": {
                        "customer": "$customer.id",
                        "date": {
                            "$dateToString": {
                                "format": date_format,
                                "date": "$date_field"
                            }
                        }
                    },
                    "order_count": {"$sum": 1},
                    "customer_info": {
                        "$addToSet": {
                            "id": "$customer.id",
                            "name": "$customer.first_name",
                            "email": "$customer.email"
                        }
                    }
                }
            },
            {
                "$match": {
                    "order_count": {"$gt": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "repeat_customers": {"$sum": 1},
                    "customer_orders": {"$push": {
                        "details": {
                            "id": {"$first": "$customer_info.id"},
                            "name": {"$first": "$customer_info.name"},
                            "email": {"$first": "$customer_info.email"},
                            "order_count": "$order_count"
                        }
                    }}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        if interval == 'quarterly':
            pipeline[1]["$group"]["_id"]["date"] = {
                "$concat": [
                    {"$toString": {"$year": "$date_field"}},
                    "-Q",
                    {"$toString": {"$ceil": {"$divide": [{"$month": "$date_field"}, 3]}}}
                ]
            }

        orders = get_collection('shopifyOrders')
        repeat_customers_data = list(orders.aggregate(pipeline))
        
        return Response(repeat_customers_data)
        
class GeographicalDistribution(APIView):
    def get(self, request):
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "city": "$default_address.city",
                        "province": "$default_address.province"
                    },
                    "customer_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "city": "$_id.city",
                    "province": "$_id.province",
                    "customer_count": 1
                }
            },
            {"$sort": {"customer_count": -1}}
        ]
        
        customers = get_collection('shopifyCustomers')
        geo_data = list(customers.aggregate(pipeline))
        
        return Response(geo_data)

class CustomerLifetimeValue(APIView):
    def get(self, request):
        orders = get_collection('shopifyOrders')

        first_purchase_pipeline = [
            {
                "$addFields": {
                    "order_date": {"$toDate": "$created_at"}
                }
            },
            {
                "$group": {
                    "_id": "$customer.id",
                    "first_purchase": {"$min": "$order_date"}
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "first_purchase_month": {
                        "$concat": [
                            {"$toString": {"$year": "$first_purchase"}},
                            "-",
                            {"$cond": [
                                {"$lt": [{"$month": "$first_purchase"}, 10]},
                                {"$concat": ["0", {"$toString": {"$month": "$first_purchase"}}]},
                                {"$toString": {"$month": "$first_purchase"}}
                            ]}
                        ]
                    }
                }
            }
        ]
        
        customer_first_purchases = list(orders.aggregate(first_purchase_pipeline))
        
        customer_cohorts = {str(cust["_id"]): cust["first_purchase_month"] for cust in customer_first_purchases}
        
        clv_pipeline = [
            {
                "$addFields": {
                    "order_value": {"$toDouble": "$total_price_set.shop_money.amount"}
                }
            },
            {
                "$group": {
                    "_id": "$customer.id",
                    "total_value": {"$sum": "$order_value"},
                    "order_count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "customer_id": "$_id",
                    "total_value": 1,
                    "order_count": 1
                }
            }
        ]
        
        clv_data = list(orders.aggregate(clv_pipeline))
        
        cohort_clv = {}
        for customer in clv_data:
            cohort = customer_cohorts.get(str(customer['customer_id']), 'unknown')
            if cohort not in cohort_clv:
                cohort_clv[cohort] = {'total_value': 0, 'customer_count': 0}
            cohort_clv[cohort]['total_value'] += customer['total_value']
            cohort_clv[cohort]['customer_count'] += 1

        result = [
            {
                'cohort': cohort,
                'customer_count': data['customer_count'],
                'total_value': data['total_value'],
                'clv': data['total_value'] / data['customer_count'] if data['customer_count'] > 0 else 0
            }
            for cohort, data in cohort_clv.items()
        ]
        
        result.sort(key=lambda x: x['cohort'])
        
        return Response(result)