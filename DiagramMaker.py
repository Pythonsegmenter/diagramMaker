from ortools.sat.python import cp_model
from math import sqrt, ceil
import numpy as np
import basic_constants as bc

class DiagramMaker:
    def __init__(self, objects):
        # Initialisation
        self.objects = objects
        self.columns, self.rows = self.determine_size()

        # Store model
        self.model = cp_model.CpModel()
        self.pos = self.set_up_model()
        self.obj_bool_vars = []  # Keeps track of the cost of if certain evaluations result in true (boolean costs)
        self.obj_bool_coeffs = []

        self.obj_int_vars_exponential = []
        self.obj_int_coeffs_exponential = []

        # Evaluate rules
        self.evaluate_all_rules()

        # Solve the model
        self.planning = self.solve() #The planning as a list with one sublist per week. In every sublist there are 7 names.

    def determine_size(self):
        amount_of_positions = 0
        for obj in self.objects:
            amount_of_positions+=obj.size*2 #Make the field double the object sizes
        # amount_of_positions = (len(self.objects)-1)*3 #-1 because link is also considered an "object" #TODO 12 should be used
        columns = ceil(sqrt(amount_of_positions/2))
        rows = 2*columns
        return columns, rows


    def set_up_model(self):
        pos = {}
        for row in range(self.rows):
            for col in range(self.columns):
                for obj in self.objects: #+1 as links also need identification
                    pos[row, col, obj.id] = self.model.NewBoolVar('pos_%i_%i_%i' % (row, col, obj.id))
        return pos

    def evaluate_all_rules(self):

        ### RULE 0 ###
        # Every must have maximum one obj
        self.enforce_max_one_obj_per_pos()

        ### RULE 1 ###
        # Objects must have a certain size
        self.enforce_obj_size()

        ### RULE 2 ###
        # Objects must not be fragmented but one whole
        self.enforce_obj_coherence()

        ### RULE 3 ###
        # Objects must be linked
        self.enforce_obj_links()

    def enforce_obj_coherence(self):
        """Ensures that objects are one whole and not split over the matrix"""
        for obj in self.objects:
            if obj.id==0: #This is the link object. It should not be "coherent"
                continue
            pattern = np.full((obj.rows, obj.columns), obj.id, dtype=int)
            self.pattern_checker(pattern) #Enforce this pattern somewhere

    def enforce_max_one_obj_per_pos(self):
        """Exactly one object per position."""
        for row in range(self.rows):
            for col in range(self.columns):
                options = [self.pos[row, col, obj.id] for obj in self.objects]
                self.model.Add(sum(options) <= 1)  # max one obj per pos

    def enforce_obj_size(self):
        """Objects must have a certain size"""
        for obj in self.objects[1:]:
            options = []
            for row in range(self.rows):
                for col in range(self.columns):
                    options.append(self.pos[row, col, obj.id])
            self.model.Add(sum(options) == obj.size)

    def enforce_obj_links(self): #We're going to enforce a link with just one vertical space in between
        for obj in self.objects:
            for linked_obj_name in obj.linked_to:
                linked_obj = self.get_linked_obj(linked_obj_name)
                pattern = np.array([[obj.id],[0],[0],[linked_obj.id]])
                self.pattern_checker(pattern)


    def pattern_checker(self,pattern):
        """Expects a numpy array"""
        #Get pattern rows & columns
        pattern_rows = pattern.shape[0]
        pattern_columns = pattern.shape[1]

        #Get all options
        options_evaluations = [] #all options for the pattern to be positioned are stored in this one.
        for row in range(self.rows-pattern_rows+1):
            for col in range(self.columns-pattern_columns+1):
                #Create a bool that evaluates for every position if the pattern is here
                options = []
                for pattern_row in range(pattern_rows):
                    for pattern_col in range(pattern_columns):
                        options.append(self.pos[row+pattern_row, col+pattern_col, pattern[pattern_row][pattern_col]])
                options_evaluation = self.model.NewBoolVar("")
                self.evaluate_and(options,options_evaluation)
                options_evaluations.append(options_evaluation)
        self.model.Add(sum(options_evaluations)==1) #Exactly once the pattern should be present

    def get_linked_obj(self, linked_obj):
        for obj in self.objects:
            if obj.name == linked_obj:
                return obj
        else:
            raise KeyError("Obj "+linked_obj+" not found.")

    def evaluate_or(self, or_list, resulting_bool_var):
        # Either a or b or both must be 1 if c is 1.
        self.model.AddBoolOr(or_list).OnlyEnforceIf(resulting_bool_var)

        # The above line is not sufficient, as no constraints are defined if c==0 (see reference documentation of
        # "OnlyEnforceIf". We therefore add another line to cover the case when c==0:

        # a and b must both be 0 if c is 0
        or_not_list = [i.Not() for i in or_list]
        self.model.AddBoolAnd(or_not_list).OnlyEnforceIf([resulting_bool_var.Not()])

        return resulting_bool_var

    def evaluate_and(self, and_list, resulting_bool_var):
        # Both a and b must be 1 if c is 1
        self.model.AddBoolAnd(and_list).OnlyEnforceIf(resulting_bool_var)

        # What happens if c is 0? This is still undefined thus let us add another line:

        # Either a or b or both must be 0 if c is 0.
        and_not_list = [i.Not() for i in and_list]
        self.model.AddBoolOr(and_not_list).OnlyEnforceIf(resulting_bool_var.Not())

        return resulting_bool_var

    def solve(self):
        # # Objective
        # self.model.Minimize(
        #     sum(self.obj_bool_vars[i] * self.obj_bool_coeffs[i] for i in range(len(self.obj_bool_vars))) +
        #     sum(self.obj_int_vars_exponential[i] * self.obj_int_coeffs_exponential[i] for i in
        #         range(len(self.obj_int_vars_exponential))))

        # Solve the model.
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solution_printer = cp_model.ObjectiveSolutionPrinter()
        status = solver.Solve(self.model, solution_printer)

        # Output solution
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("Solution found")

            solution_array = np.empty([self.rows,self.columns])
            solution_array[:] = np.nan
            for row in range(self.rows):
                for col in range(self.columns):
                    for obj in self.objects:
                        if solver.BooleanValue(self.pos[row,col,obj.id]):
                            solution_array[row,col]=obj.id
            print("Done")

