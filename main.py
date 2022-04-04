import DiagramMaker
import SalesforceObject
import time


start_time = time.perf_counter()
objects = []
objects.append(SalesforceObject.SalesforceObject(name='Link',linked_to=[],id=0))
objects.append(SalesforceObject.SalesforceObject(name='Account',linked_to=['Contact'],id=1))
objects.append(SalesforceObject.SalesforceObject(name='Contact',linked_to=[],id=2))
objects.append(SalesforceObject.SalesforceObject(name='User',linked_to=['Account'],id=3))


diagram = DiagramMaker.DiagramMaker(objects)
# print(diagram.columns)
# print(diagram.rows)

total_time = time.perf_counter()-start_time

print("Total time: "+str(total_time))
print("Done")