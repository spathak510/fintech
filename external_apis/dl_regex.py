import datetime, re


def dl_num(ocr_string):
    dl_num = ''    
    pattern = r'[A-Z]+\d+\s*\d+'
    match = re.search(pattern, ocr_string)
    if match:
        dl_num = match.group()
    
    if dl_num == '':
        pattern = r'([A-Z]+\d+\s*\d+)'
        match = re.search(pattern, ocr_string)
        if match:
            dl_num = match.group(1)
    
    if dl_num == '':
        pattern = r'Number\s*:(\S+)'
        match = re.search(pattern, ocr_string)
        if match:
            dl_num = match.group(1)

    if dl_num == '':
        pattern = r'\n([A-Z]+-\d+)'
        match = re.search(pattern, ocr_string) 
        if match:
            dl_num = match.group(1)
    return dl_num




def condidate_name(ocr_string):
    name = ''
    pattern = r"Name\n([^\n]+)"
    name_match = re.search(pattern, ocr_string)
    if name_match:
        name = name_match.group(1)
    
    if name == '':
        pattern = r"Name\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            name = name_match.group(1)                         
    return name


def condidate_father_name(ocr_string):
    father_name = ''
    pattern = re.compile(r'(?i)\n([A-Z\s]+)\n\d{2}/\d{2}/\d{4}\nPermanent Account Number', re.MULTILINE)
    name_match = pattern.search(ocr_string)
    if name_match:
        original_string = ((name_match.group(1)).replace('INCOME TAX DEPARTMENT','')).replace('\n','')
        substring = condidate_name(ocr_string)
        father_name = original_string.replace(substring, "")

    if father_name == '':
        pattern = r"FATHER'S NAME\n\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            father_name = name_match.group(1)
    
    if father_name == '':
        pattern = r"FATHER'S NAME:\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            father_name = name_match.group(1)
    
    if father_name == '':
        pattern = r"Father\n\s*([^\n]+)"
        match = re.search(pattern, ocr_string)                
        if match:
            father_name = match.group(1)
            
    return father_name



def condidate_dob(ocr_string):
    dob = ''
    dob_regex = r'Date of Birth\n(\d{2}/\d{2}/\d{4})'
    dob_match = re.search(dob_regex, ocr_string)
    if dob_match:
        dob = dob_match.group(1)
    
    if dob == '':
        dob_regex = r'DOB:\s*(\d{2}-\d{2}-\d{4})'
        dob_match = re.search(dob_regex, ocr_string)
        if dob_match:
            dob = dob_match.group(1) 
               
    if dob == '':
        dob_regex = r'Date of Birth\n(\d{2}-\d{2}-\d{4})'
        match = re.search(dob_regex, ocr_string)
        if match:
            dob = match.group(1)
    return dob


def dl_issue_date(ocr_string):
    issue_date = ''
    date_pattern = r'Date of Issue\n(\d{2}/\d{2}/\d{4})'
    date_match = re.search(date_pattern, ocr_string)
    if date_match:
        issue_date = date_match.group(1)
    
    if issue_date == '':
        pattern = r'Date of issue\n(\d{2}-\d{2}-\d{4})'
        match = re.search(pattern, ocr_string)
        if match:
           issue_date = match.group(1)     
    if issue_date == '':
        date_pattern = r'Date of Issue\n(\d{2}-\d{2}-\d{4})'
        date_match = re.search(date_pattern, ocr_string)
        if date_match:
            issue_date = date_match.group(1)
    return issue_date


def dl_validity_for_non_transport_date(ocr_string):
    valid_date = ''
    date_pattern = r'NT\s*(\d{2}/\d{2}/\d{4})'
    date_match = re.search(date_pattern, ocr_string)
    if date_match:
        valid_date = date_match.group(1)    
         
    
    return valid_date

def dl_validity_for_transport_date(ocr_string):
    valid_date = ''
    date_pattern = r'Validity\n(\d{2}/\d{2}/\d{4})'
    date_match = re.search(date_pattern, ocr_string)
    if date_match:
        valid_date = date_match.group(1)    
         
    
    return valid_date




def condidate_adress(ocr_string):
    address = ''
    pattern = r'Address:\n(.*?)(?=\nDate)'
    match = re.search(pattern, ocr_string, re.DOTALL)
    if match:
        address = match.group(1).replace('\n','')
    
    if address == '':
        pattern = r'Permanent Address\n([^\n]+)'
        match = re.search(pattern, ocr_string, re.DOTALL)
        if match:
            address = match.group(1).replace('\n','')
            
    if address == '':
        pattern = r'Present Address\n([^\n]+)'
        match = re.search(pattern, ocr_string, re.DOTALL)
        if match:
            address = match.group(1).replace('\n','')                        
    
    return address











# Main function to make Voter Id ocr string into json formate by regex
def get_dl_front_json(ocr_string):
        dl_front_list = {}
        dl_front_list['dl_num'] = ''
        dl_front_list['name'] = ''
        dl_front_list['father_name'] = ''
        dl_front_list['dob'] = ''
        dl_front_list['issue_date'] = ''
        dl_front_list['non_transport_valid_date'] = ''
        dl_front_list['transport_valid_date'] = ''
        dl_front_list['address'] = ''
        
        
        
        
        try:
            # Get passport number
            dl_front_list['dl_num'] = dl_num(ocr_string)

            # Get condidate name
            dl_front_list['name'] = condidate_name(ocr_string)
            
            # Get condidate father's name
            dl_front_list['father_name'] = condidate_father_name(ocr_string)

            # Get condidate date of birth
            dl_front_list['dob'] = condidate_dob(ocr_string)
            
            # Get condidate dl issue date
            dl_front_list['issue_date'] = dl_issue_date(ocr_string) 
            
            # Get condidate dl non transport valid date
            dl_front_list['non_transport_valid_date'] = dl_validity_for_non_transport_date(ocr_string)
            
            # Get condidate dl transport valid date
            dl_front_list['transport_valid_date'] = dl_validity_for_transport_date(ocr_string)
            
            # Get condidate DL address
            dl_front_list['address'] = condidate_adress(ocr_string)  
                  
            return dl_front_list
        except Exception as ex:
            print('ex :',ex)
            return dl_front_list
        
        
        
def get_dl_back_json(ocr_string):
        dl_back_list = {}
        dl_back_list['dl_num'] = ''
        dl_back_list['address'] = ''
        
        
        try:
            # Get voter id number
            dl_back_list['dl_num'] = dl_num(ocr_string) 
            
            # Get condidate adress
            dl_back_list['address'] = condidate_adress(ocr_string)  
                  
            return dl_back_list
        except Exception as ex:
            print('ex :',ex)
            return dl_back_list        