
import zerorpc
import time

client1 = zerorpc.Client()
client1.connect("tcp://127.0.0.1:4242")
print client1._rpc_list()
print client1._rpc_inspect()
print client1._rpc_name()
print client1._rpc_ping()
print client1._rpc_args('hello')
print client1._rpc_args('sub')
print client1._rpc_args('add')
print client1._rpc_help('hello')

res = client1.hello("parameter 1")
print "Result is " + str(res)

res = client1.sub(100, 30)
print "Result is " + str(res)

for item in client1.progress(100, 200, 30):
    print item

try:
    res = client1.exception_test()
except Exception as e:
    print e

client2 = zerorpc.Client()
client2.connect("tcp://127.0.0.1:4243")
res = client2.hello("parameter 2")
print "Result is " + str(res)
res = client2.div(100, 30)
print "Result is " + str(res)

res = client1.add(20, 30)
print "Result is " + str(res)

#res = client1.block_test()
#print "Result is " + str(res)

while True:
    time.sleep(1)