from math import ceil, sqrt

class SalesforceObject:
    def __init__(self, name, linked_to, id):
        self.id = id
        self.name = name
        self.linked_to = linked_to
        self.columns, self.rows = self.determine_dimensions()
        self.size = self.rows*self.columns



    def determine_dimensions(self):
        #Determine preliminary size due to rounding errors it will change.
        if len(self.linked_to) == 0:
            preliminary_size = 1
        else:
            preliminary_size = len(self.linked_to)*2

        #Calculate rows and columns from preliminary size (here rounding error occurs, which is reason why we need preliminary size)
        rows = ceil(sqrt(preliminary_size / 2))
        columns = 2*rows

        return columns, rows