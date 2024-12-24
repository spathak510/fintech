import datetime, re


def voter_id_num(ocr_string):
    voter_num = ''
    pattern = r"Sid\n\s*([^\n]+)"
    voter_match = re.search(pattern, ocr_string)
    if voter_match:
        voter_num = voter_match.group(1)
        
    if voter_num == '':
        pattern = r'CARD\n([A-Z\d]+)'
        match = re.search(pattern, ocr_string)
        if match:
            voter_num = match.group(1)
            
    if voter_num == '':    
        pattern = r'.*?\w(\d+).*?'
        voter_match = re.search(pattern, ocr_string)
        if voter_match:
            voter_num = voter_match.group()
    
    
    return voter_num




def condidate_name(ocr_string):
    name = ''
    name_pattern = re.compile(r"Elector's Name\n(.+)")
    name_matches = re.search(name_pattern, ocr_string)
    if name_matches:
        name = name_matches.group(1).strip()
    
    if name == '':
        pattern = r"Elector's Name\n \nFather's Name\n\s+([^\n]+)"
        name_matches = re.search(pattern, ocr_string)
        if name_matches:
            name = name_matches.group(1).strip()
    
    if name == '':
        pattern = r"ELECTOR'S NAME:\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            name = name_match.group(1)
            
    if name == '':
        pattern = r"NAME:\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            name = name_match.group(1)
    
    if name == '':
        pattern = r"Elector's Name : (.+?)\n"
        match = re.search(pattern, ocr_string)
        if match:
            name = match.group(1)                             
    return name


def condidate_father_name(ocr_string):
    father_name = ''
    
    pattern = r"FATHER'S NAME\n\s*([^\n]+)"
    name_match = re.search(pattern, ocr_string)
    if name_match:
        father_name = name_match.group(1)
    
    if father_name == '':
        pattern = r"FATHER'S NAME:\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            father_name = name_match.group(1)        
            
    return father_name



def condidate_dob(ocr_string):
    dob = ''
    dob_regex = '\d{2}/\d{2}/\d{4}'
    dob_match = re.search(dob_regex, ocr_string)
    if dob_match:
        dob = dob_match.group()
    
    return dob



def condidate_gender(ocr_string):
    gender = ''
    
    if 'Female' in ocr_string or 'female' in ocr_string or 'FEMALE' in ocr_string:
        gender = 'FEMALE'
        
    elif 'Male' in ocr_string or 'MALE' in ocr_string or 'male' in ocr_string:
        gender = 'MALE'    
         
    
    return gender




def condidate_adress(ocr_string):
    address = ''
    pattern = r'Address:\n(.*?)(?=\nDate)'
    match = re.search(pattern, ocr_string, re.DOTALL)
    if match:
        address = match.group(1).replace('\n','')
    
    if address == '':
        pattern = r'Address:\s*([^\n]+)'
        match = re.search(pattern, ocr_string, re.DOTALL)
        if match:
            address = match.group(1).replace('\n','')                
    
    return address



def voter_id_issue_date(ocr_string):
    issue_date = ''
    date_pattern = r'Date: (\d{2}/\d{2}/\d{4})'
    date_match = re.search(date_pattern, ocr_string)
    if date_match:
        issue_date = date_match.group(1)
    
    return issue_date






# Main function to make Voter Id ocr string into json formate by regex
def get_voter_id_front_json(ocr_string):
        voter_id_front_list = {}
        voter_id_front_list['voter_id_num'] = ''
        voter_id_front_list['name'] = ''
        voter_id_front_list['father_name'] = ''
        voter_id_front_list['dob'] = ''
        voter_id_front_list['Gender'] = ''
        
        
        
        # remove all extra spece from ocr_string
        pattern = re.compile(r'[^\x00-\x7F]+', flags=re.UNICODE)
        ocr_string = pattern.sub('', ocr_string)
        ocr_string = re.sub(' +', ' ', ocr_string)
        
        try:
            # Get passport number
            voter_id_front_list['voter_id_num'] = voter_id_num(ocr_string)

            # Get condidate name
            voter_id_front_list['name'] = condidate_name(ocr_string)
            
            # Get condidate father's name
            voter_id_front_list['father_name'] = condidate_father_name(ocr_string)

            # Get condidate date of birth
            voter_id_front_list['dob'] = condidate_dob(ocr_string)
            
            # Get condidate date of birth
            voter_id_front_list['Gender'] = condidate_gender(ocr_string)  
                 
            return voter_id_front_list
        except Exception as ex:
            print('ex :',ex)
            return voter_id_front_list
        
        
        
def get_voter_id_back_json(ocr_string):
        voter_id_back_list = {}
        voter_id_back_list['voter_id_num'] = ''
        voter_id_back_list['dob'] = ''
        voter_id_back_list['Gender'] = ''
        voter_id_back_list['address'] = ''
        voter_id_back_list['issue_date'] = ''
        
        
        # remove all extra spece from ocr_string
        pattern = re.compile(r'[^\x00-\x7F]+', flags=re.UNICODE)
        ocr_string = pattern.sub('', ocr_string)
        ocr_string = re.sub(' +', ' ', ocr_string)
        
        try:
            # Get voter id number
            voter_id_back_list['voter_id_num'] = voter_id_num(ocr_string)
            
            # Get condidate date of birth
            voter_id_back_list['dob'] = condidate_dob(ocr_string)
            
            # Get condidate date of birth
            voter_id_back_list['Gender'] = condidate_gender(ocr_string) 
            
            # Get condidate adress
            voter_id_back_list['address'] = condidate_adress(ocr_string)

            # Get condidate voter id issue date 
            voter_id_back_list['issue_date'] = voter_id_issue_date(ocr_string)  
                  
            return voter_id_back_list
        except Exception as ex:
            print('ex :',ex)
            return voter_id_back_list        