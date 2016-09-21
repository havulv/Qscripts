#!/usr/bin/python3

'''
    A function class to simplify adding documentation to files

'''

import re

PARAMS = re.compile("\((.*?)\)")

class Func(object):

    def __init__(self, declaration, retstat=(None,None)):
        self.name = self._get_name(declaration[1])
        self.params = self._get_params(declaration[1])
        self.retvals = self._get_return(retstat[1])
        self.location = (declaration[0], retstat[0]) #end=None implies void
        self.doc = None
        self.docstring = ""

    def __repr__(self):
        return self.name

    def doc_check(self, contents):
        if "'''" in contents[self.location[0]+1][1]:
            return True
        else:
            return False

    def _get_params(self, declaration):
        params = PARAMS.search(declaration).group(1).split(',')
        return params if params != [''] else [None]

    def _get_return(self, rts):
        return [rts[rts.find("return ")+7:rts.find("\n")]]\
                                            if rts != None else [None]

    def _get_name(self, decl):
        return decl[decl.find("def ")+4:decl.find("(")]

    def mk_doc(self):
        skip = input("Do you want to skip adding documentation to "
                    "this function, {0}? (Y/N)\n".format(self.name))
        if skip.upper() == "Y":
            self.doc = True

        if not self.doc:
            self.docstring += " "*4+"'''\n"
            print("Function: {0}  Parameters: {1} Returns:"
                    " {2}".format(self.name, ','.join(self.params),
                                                    *self.retvals))
            for j in [  ("Summary", [False]),
                        ("Parameters", self.params),
                        ("Return Values", self.retvals)]:
                self.docstring += " "*8+j[0]+":\n"
                for i in j[1]:
                    if not i and i != None:
                        try:
                            self._doc_input(False)
                        except KeyboardInterrupt:
                            print("\n")
                            continue
                    elif i:
                        try:
                            self._doc_input(i)
                        except KeyboardInterrupt:
                            print("\n")
                            continue
                    elif i == None:
                        self.docstring += " "*12+"VOID\n"

                if j[0] != "Return Values":
                    self.docstring += " "*8+ "-"*64+"\n"
                elif j[0] == "Return Values":
                    print("\n")

            self.docstring += " "*4+"'''\n"

        elif skip.upper() == "Y" and self.doc == True:
            return
        else:
            raise ValueError("This function is already documented")

    def _doc_input(self, arg):
        doc = ''

        if not arg:
            user_in = input("\tSUMMARY :: ")
            user_in = user_in.split('\\n')
            for line in range(len(user_in)):
                if user_in[line] != '' and line == 0:
                    doc += " "*12 + user_in[line]+"\n"
                elif user_in[line] != '':
                    doc += " "*16 + user_in[line]+"\n"
        else:
            user_in = input("\t{0} :: ".format(arg))
            user_in = user_in.split('\\n')
            for line in range(len(user_in)):
                if user_in[line] != '' and line == 0:
                    doc += " "*12 +"{0} :: ".format(arg)+ \
                                                    user_in[line]+"\n"
                elif user_in[line] != '':
                    doc += " "*16 + user_in[line]+"\n"
        if "'''" in doc:
            raise Exception("DON'T FUCK AROUND IN THE DOCS")
        else:
            self.docstring += doc + "\n"
