import redis

r = redis.StrictRedis(host='localhost', port=6379)

exchange_code = 123456788 
value = {
    'num': 100,  # how many people can exchange
    'ctype': 0, # car type, 0->carpool, 1->specail car
    'note': 'wuyunong-1hao', # decription
    'deadline': '2015-05-02', 
    'within': 20, # total price must higher than this
    'price': 60  # coupon price
    }

rkey = 'c_' + str(exchange_code)
print rkey
r.delete(rkey)
r.hmset(rkey, value)
