import redis

r = redis.StrictRedis(host='localhost', port=6379)

exchange_code = 123456789 
value = {
    'num': 2,  # how many people can exchange
    'ctype': 0, # car type, 0->carpool, 1->specail car
    'note': 'hello', # decription
    'deadline': '2015-05-02', 
    'within': 200, # total price must higher than this
    'price': 1  # coupon price
    }

rkey = 'c_' + str(exchange_code)
r.delete(rkey)
r.hmset(rkey, value)
