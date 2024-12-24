class name_genrator:
    
    def __init__(self, name, father_name):
        self.name = name.lower().replace("  "," ")
        self.father_name = father_name.lower().replace("  "," ")
        self.extra_words = ["sh.","sh","shri","md.","md","mohmad","mohammad"]
        self.remove_extra_words()
        self.all_name = []
        self.surname = ""
        self.first_name = ""
        self.find_first_name()
        self.get_surname()
        self.all_addable_father_name=[]
        self.arrange_all_permutations()
    
    def remove_extra_words(self):
        for word in self.extra_words:
            if word in self.name.split(' '):
                self.name=self.name.replace(word,"")
            if word in self.father_name.split(' '):
                self.father_name=self.father_name.replace(word,"")


    def get_all_name_permutations(self):
        return list(set(self.all_name))

    def find_first_name(self):
        self.first_name = self.name.split(' ')[0].strip()

    def arrange_all_permutations(self):
        self.all_name.append(self.name.strip())
        if self.not_is_surname_there():
            self.all_name.append((self.name+' '+self.surname).strip())
        if self.not_is_father_name_there():
            self.add_all_permutations_father_name()



    def not_is_surname_there(self):
        if self.surname in self.name.split(' '):
            return False
        else:
            return True

    def not_is_father_name_there(self):
        if len(list((set(self.name.split(' ')) & set(self.father_name.split(' '))) & set([self.surname])))==0:
            return len(list(set(self.name.split(' ')) & set(self.father_name.split(' '))))==0
        else:
            return True


    def get_surname(self):
        if (set(self.name.split(' ')) & set(self.father_name.split(' '))):
            self.surname = list(set(self.name.split(' ')) & set(self.father_name.split(' ')))[0].strip()
        else:
            self.surname = self.name.split(' ')[len(self.name.split(' '))-1].strip()
            
        

    def add_all_permutations_father_name(self):
        self.get_all_addable_father_name()
        self.all_name.append((self.first_name+' '+self.surname).strip())
        for addable_father_name in self.all_addable_father_name:
            self.all_name.append((self.first_name+' '+addable_father_name).strip())
            if addable_father_name != self.surname:
                self.all_name.append((self.first_name+' '+addable_father_name+' '+self.surname).strip())
                self.all_name.append((addable_father_name+' '+self.first_name+' '+self.surname).strip())
                self.all_name.append((self.first_name+' '+self.surname+' '+addable_father_name).strip())
            
        

    def get_all_addable_father_name(self):
        for subname in self.father_name.split(' '):
            if subname != self.surname or subname!=" " or subname!="":
                self.all_addable_father_name.append(subname.strip())


# obj = name_genrator("Parvinder Singh Bhullar","sh. Darshan singh yadav")
# print(obj.get_all_name_permutations())
