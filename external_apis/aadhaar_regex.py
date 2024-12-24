import datetime, re


def aadhaar_num(ocr_string):
    aadhaar_num = ''    
    pattern = r'\b(\d{4} \d{4} \d{4})\b'
    match = re.search(pattern, ocr_string)
    if match:
        aadhaar_num = match.group()
    
    return aadhaar_num




def condidate_name(ocr_string):
    name = ''
    pattern = r'\n(\w+\s\w+)\n'
    match = re.search(pattern, ocr_string)
    if match:
        name = match.group(1)
    
    if name == '':    
        pattern = r"Name\n([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            name = name_match.group(1)
    
    if name == '':
        pattern = r"Name\s*([^\n]+)"
        name_match = re.search(pattern, ocr_string)
        if name_match:
            name = name_match.group(1) 
    if name == '':
        name_pattern = r'\n\s*([A-Za-z\s]+)\n'
        name_match = re.search(name_pattern, ocr_string)
        if name_match and name_match.group(1).split('\n')[-1] :
           name = name_match.group(1).split('\n')[-1]   
                                    
    return name


def condidate_gender(ocr_string):
    gender = ''
    pattern = r'(\w+/\s\w+)'
    match = re.search(pattern, ocr_string)
    if match:
        gender = match.group(1)
    
    if gender == '' and (("Male" in ocr_string) or ("MALE" in ocr_string)):
        gender = "Male"
    
    if gender == '' and (("Female" in ocr_string) or ("FEMALE" in ocr_string)):
        gender = "Female"    
                
    return gender



def condidate_dob(ocr_string):
    dob = ''
    dob_regex = r'DOB: (\d{2}/\d{2}/\d{4})'
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



def condidate_adress(ocr_string):
    address = ''
    address_pattern = r'Address:\s*\n(.*?)\n(?=\d{4} \d{4} \d{4}|\Z)'
    match = re.search(address_pattern, ocr_string, re.DOTALL)
    if match:
        address = match.group(1).strip()                       
    
    return address











# Main function to make Voter Id ocr string into json formate by regex
def get_aadhaar_front_json(ocr_string):
        dl_front_list = {}
        dl_front_list['aadhaar_num'] = ''
        dl_front_list['name'] = ''
        dl_front_list['gender'] = ''
        dl_front_list['dob'] = ''
        
        ocr_string = re.sub(r'[^\x00-\x7F]+', ' ', ocr_string)
        
        
        try:
            # Get passport number
            dl_front_list['aadhaar_num'] = aadhaar_num(ocr_string)

            # Get condidate name
            dl_front_list['name'] = condidate_name(ocr_string)
            
            # Get condidate father's name
            dl_front_list['gender'] = condidate_gender(ocr_string)

            # Get condidate date of birth
            dl_front_list['dob'] = condidate_dob(ocr_string)
              
                  
            return dl_front_list
        except Exception as ex:
            print('ex :',ex)
            return dl_front_list
        
        
        
def get_aadhaar_back_json(ocr_string):
        dl_back_list = {}
        dl_back_list['aadhaar_num'] = ''
        dl_back_list['address'] = ''
        
        ocr_string = re.sub(r'[^\x00-\x7F]+', ' ', ocr_string)
        
        try:
            # Get voter id number
            dl_back_list['aadhaar_num'] = aadhaar_num(ocr_string) 
            
            # Get condidate adress
            dl_back_list['address'] = condidate_adress(ocr_string)  
                  
            return dl_back_list
        except Exception as ex:
            print('ex :',ex)
            return dl_back_list        