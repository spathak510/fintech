import datetime, re


def pan_card_num(ocr_string):
    pan_card_num = ''
    pan_pattern = re.compile(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b')
    pan_match = pan_pattern.search(ocr_string)
    if pan_match:
        pan_card_num = pan_match.group(1)
    
    return pan_card_num




def condidate_name(ocr_string):
    name = ''
    pattern = r'INCOME TAX DEPARTMENT\nसत्यमेव जयते\n(.+)'
    name_match = re.search(pattern, ocr_string)
    if name_match:
        name = name_match.group(1)
    if name == '':        
        pattern = r'INCOME TAX DEPARTMENT\n(.+)'
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

    return father_name



def condidate_dob(ocr_string):
    dob = ''
    dob_regex = '\d{2}/\d{2}/\d{4}'
    dob_match = re.search(dob_regex, ocr_string)
    if dob_match:
        dob = dob_match.group()
    
    return dob




# Main function to make Pan card ocr string into json formate by regex
def get_pan_card_ocr_json_result(ocr_string):
        pancard_list = {}
        pancard_list['pan_card_num'] = ''
        pancard_list['name'] = ''
        pancard_list['dob'] = ''
        pancard_list['father_name'] = ''
        
        
        # remove all extra spece from ocr_string
        ocr_string = re.sub(' +', ' ', ocr_string)
        
        try:
            # Get passport number
            pancard_list['pan_card_num'] = pan_card_num(ocr_string)

            # Get condidate name
            pancard_list['name'] = condidate_name(ocr_string)
            
            # Get condidate father's name
            pancard_list['father_name'] = condidate_father_name(ocr_string)

            # Get condidate date of birth
            pancard_list['dob'] = condidate_dob(ocr_string)  
                  
            return pancard_list
        except Exception as ex:
            print('ex :',ex)
            return False