import datetime, re






# Regex to get condidate passport number from OCR string
def passport_num(ocr_string):
    pno = ''
    pno_reg = r'[A-Z][0-9][0-9]{6}'
    pno_match = re.search(pno_reg, ocr_string)
    if pno_match:
        pno = pno_match.group()
        
    if pno == '':    
        pno_reg = r'(\d{8})\n- / Passport No'
        pno_match = re.search(pno_reg, ocr_string)
        if pno_match:
            pno = pno_match.group(1).replace('\n', '')

    if pno == '':
        pno_reg = r'^\d{0,10}<'
        pno_match = re.findall(pno_reg, ocr_string)
        if len(pno_match) >= 1:
            pno = pno_match[0].replace('<', '')

    if pno == '':
        pno_reg = r'[A-Z][A-Z]\d{6}'
        pno_match = re.search(pno_reg, ocr_string)
        if pno_match:
            pno = pno_match.group()

    if pno == '':
        pno_reg = r'PASSPORT NO\.\n(.+?)\n'
        pno_match = re.search(pno_reg, ocr_string)
        if pno_match:
            pno = pno_match.group(1)             
            
    return pno



# Regex to get condidate name from OCR string
def condidate_name(ocr_string):
    name = ''
    input_str = ocr_string.lower()
    name_reg = r'k?ind<?<?[a-z]+<<?[a-z]+<?[a-z]*<'
    name_match = re.search(name_reg, input_str)
    
    if name_match:
        name = name_match.group() 
        name = name.split('<<')
        surname = name[0].replace('kind','').replace('ind','')
        firstname = name[1].replace('<<', '').replace('<', ' ').strip()
        name = firstname + ' ' + surname
    
    if name == '':
        name_reg = r'P?ind<?<?[a-z]+<<?[a-z]+<?[a-z]*<'
        name_match = re.search(name_reg, input_str)
        if name_match:
            name = name_match.group() 
            name = name.split('<<')
            surname = name[0].replace('kind','').replace('ind','')
            firstname = name[1].replace('<<', '').replace('<', ' ').strip()
            name = firstname + ' ' + surname    
    
    if name == '':
        name_pattern = r'P\s+([A-Z\s]+)\s+\/\s+Given Names\s+([A-Z\s]+)\s+\/\s+Surname'
        name_match = re.search(name_pattern, ocr_string)
        if name_match:
            first_name = name_match.group(1).strip()
            last_name = name_match.group(2).strip()
            name = first_name+" "+last_name
    
    if name == '':
        # ocr_string = ocr_string.replace('\n','')
        name_pattern = r'\nP.*<<<+'
        name_match = re.findall(name_pattern, ocr_string)
        if len(name_match)>=1:
            name = ((name_match[0]).replace('P<NPL','').replace('<',' ')).strip()
    
    return name            
    
    
    
# Regex to get Date of Birth from OCR string  

def condidate_dob(ocr_string):
    dob = ''
    input_str = ocr_string.lower()
    SearchDate=r'([ ]{0,1}[0-3]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[0,1]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})[-,\,/]{1}([ ]{0,1}[1-2]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1}[0-9]{1}[ ]{0,1})'
    fout1=str(input_str).replace('\n', ' ')
    datemin=datetime.datetime(2300, 5, 17)
    dateNew = re.compile(SearchDate)
    matches_list=dateNew.findall(str(fout1))
    if matches_list:
        for d in matches_list:
            date = datetime.datetime(int(d[2].replace(' ', '')), int(d[1].replace(' ', '')), int(d[0].replace(' ', '')))
            if date< datemin:
                datemin=date
        dob = datemin.strftime("%d-%m-%Y")
    
    if dob == '':
        dob_pattern = r'DATE OF BIRTH\n(.+?)\n'
        dob_match = re.search(dob_pattern, ocr_string)
        if dob_match:
            dob = dob_match.group(1)
    
    if dob == '':
        dob_pattern = r'\d{1,2}\s(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s\d{4}'        
        dob_match = re.findall(dob_pattern, ocr_string)
        if dob_match:
            date_objects = [datetime.strptime(date, '%d %b %Y') for date in dob_match]
            smallest_date = min(date_objects)
            dob = smallest_date.strftime('%d %b %Y')
    
    return dob



# Regex to get Date of Issue from OCR string
def date_of_issue(ocr_string):
    date_of_issue = ''
    pattern = r'\d{1,2}\s(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s\d{4}'        
    doi_match = re.findall(pattern, ocr_string)
    if doi_match:
        date_objects = [datetime.strptime(date, '%d %b %Y') for date in doi_match]
        sorted_dates = sorted(date_objects)
        second_smallest_date = sorted_dates[1]
        date_of_issue = second_smallest_date.strftime('%d %b %Y')
    
    if date_of_issue == '':
        issue_date_pattern = r'Date of Issue\n(\d{2}/\d{2}/\d{4})'
        issue_date = re.search(issue_date_pattern, ocr_string)
        date_of_issue = issue_date.group(1) if issue_date else None    
        
    return date_of_issue




# Regex to get Date of Expiry from OCR string
def date_of_expiry(ocr_string):
    date_of_expiry = ''
    pattern = r'\d{1,2}\s(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s\d{4}'        
    doe_match = re.findall(pattern, ocr_string)
    if doe_match:
        date_objects = [datetime.strptime(date, '%d %b %Y') for date in doe_match]
        largest_date = max(date_objects)
        date_of_expiry = largest_date.strftime('%d %b %Y')
    
    if date_of_expiry == '':
        expiry_date_pattern = r'Date of Expiry\n(\d{2}/\d{2}/\d{4})'
        expiry_date = re.search(expiry_date_pattern, ocr_string)
        date_of_expiry = expiry_date.group(1) if expiry_date else None    
    
    return date_of_expiry





# Regex to get File number from OCR string
def passport_file_num(ocr_string):
    file_num = ''
    
    input_str = ocr_string.replace('\r','')
    file_reg = r'(\n[A-Z0-9]{7}[0-9]{8}\n)|(\n[A-Z0-9]{5}[0-9]{7}\n)'
    file_match = re.search(file_reg, input_str)
    if file_match:
        file_num = (file_match.group()).replace('\n','')
    
    if file_num == '':
        ref_reg = r'Ref\. No\.\n(.+?)\n'
        ref_match = re.search(ref_reg, ocr_string)
        if ref_match:
            file_num = ref_match.group(1)
    
    return file_num




# Regex to get Father name from OCR string
def condidate_father_name(ocr_string):
    father_name = ''
    if father_name == '':
        name_reg =  r'NAME\n([^\n]+)'
        name_match = re.search(name_reg, ocr_string)
        if name_match:
            father_name = name_match.group(1)
            
    if father_name == '':
        name_reg = r'\n[A-Z ]+\n'
        name_match = re.search(name_reg, ocr_string)
        if name_match:
            father_name = (name_match.group()).replace('\n','')
    
    return father_name




# Regex to get Address from OCR string
def condidate_address(ocr_string):
    address = ''
    
    address_reg1 = r'Address\n([\s\S]*?)(?=\n\||$)'
    address_1 = re.search(address_reg1, ocr_string)
    address_part1 = address_1.group(1).replace('\n',' ')
    address_reg2 = r'\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n[ A-Z0-9:.!@#$%^&*();<>?\",_/\-]+\n'
    address_part2 = re.search(address_reg2, ocr_string)
    if address_part2:
        input_str = ocr_string.replace('\r','')
        file_reg = r'(\n[A-Z0-9]{7}[0-9]{8}\n)|(\n[A-Z0-9]{5}[0-9]{7}\n)'
        file_match = re.search(file_reg, input_str)
        file_no = ''
        if file_match:
            file_no = (file_match.group()).replace('\n','')
        address = address_part1 +", "+(address_part2.group()).replace('\n','')
        if file_no in address:
            address = address.replace(file_no,'')
    
    if address == '':
        address_reg = r'ADDRESS\n([^\n]+)'
        address_match = re.search(address_reg, ocr_string)
        if address_match:
            address = address_match.group(1)
        
    if address == '':
        address_reg = r'/ Address\n(.+?)\n'
        address_match = re.search(address_reg, ocr_string)
        if address_match:
            address = address_match.group(1)
            
    if address == '':
        address_pattern = r'Place of Birth\n(.+)'
        address_match = re.search(address_pattern, ocr_string)
        address = address_match.group(1) if address else None
        
    return address



# Get MRZ code 
def get_mrz_code(ocr_string):
    mrz_code = ''
    mrz_pattern = r'([A-Z0-9<]{44})'
    mrz_matches = re.findall(mrz_pattern, ocr_string)
    if mrz_matches:
        mrz_code = ''.join(mrz_matches)
     
    if mrz_code == '':
        ocr_s = ocr_string.replace('\n', '')
        mrz_pattern = r'([A-Z0-9<]{38})'
        mrz_matches = re.findall(mrz_pattern, ocr_s)
        if mrz_matches:
            mrz_code = ''.join(mrz_matches)        
            
    return mrz_code


# Main function to make Passport Front string into json formate by regex
def get_indian_passport_front_result(ocr_string):
        passport_list = {}
        passport_list['passport_num'] = ''
        passport_list['name'] = ''
        passport_list['dob'] = ''
        passport_list['date_of_issue'] = ''
        passport_list['date_of_expiry'] = ''
        passport_list['mrz'] = ''
        
        # Remove all hindi content fron ocr_sting
        ocr_string = re.sub(r'[^\x00-\x7F]+', '', ocr_string)
        # remove all extra spece from ocr_string
        ocr_string = re.sub(' +', ' ', ocr_string)
        
        try:
            # Get passport number
            passport_list['passport_num'] = passport_num(ocr_string)

            # Get condidate name
            passport_list['name'] = condidate_name(ocr_string)

            # Get condidate date of birth
            passport_list['dob'] = condidate_dob(ocr_string)
                
            # Get passport Issueing date
            passport_list['date_of_issue'] =  date_of_issue(ocr_string)
            
            # Get passport Expiry date 
            passport_list['date_of_expiry'] =  date_of_expiry(ocr_string)
            
            # Get MRZ code
            passport_list['mrz'] = get_mrz_code(ocr_string)  
                  
            return passport_list
        except Exception as ex:
            print('ex :',ex)
            return False
        
        
        
# Main function to make Passport Back string into json formate by regex
def get_indian_passport_back_result(ocr_string):
    passport_list = {}
    passport_list['fileNo'] = ''
    passport_list['address'] = ''
    passport_list['father_name'] = ''
    
    try:
        # Get file Number from passport
        input_str = ocr_string.replace('\r','')
        passport_list['fileNo'] = passport_file_num(input_str)

        # Get Address from passport
        passport_list['address'] = condidate_address(input_str)

        # Get Father name from passport
        passport_list['father_name'] = condidate_father_name(input_str)
        
        return passport_list
    except Exception as ex:
        print('ex :',ex)
        return False