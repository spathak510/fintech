from datetime import date
import datetime



def calculat_age_band(dob):
    dob = datetime.datetime.strptime(dob, "%Y-%m-%d").date()
    age_band = ''
    age = int((date.today() - dob).days / 365.2425)
    if age <= 10:
        age_band = "1-10"
    elif age>=10 and age<20:
        age_band = "10-20"
    elif age>=20 and age<30:
        age_band = "20-30"  
    elif age>=30 and age<40:
        age_band = "30-40" 
    elif age>=40 and age<50:
        age_band = "40-50"
    elif age>=50 and age<60:
        age_band = "50-60"
    elif age>=60 and age<70:
        age_band = "60-70"
    elif age>=70 and age<80:
        age_band = "70-80"
    elif age>=80 and age<90:
        age_band = "80-90"
    elif age>=90 and age<100:
        age_band = "90-100"
    else:
        return age_band 
    return age_band  


# Masking the numberbers
def number_masking(num):
    num = str(num)
    remainig_num = str(num[-4:])
    strik = len(num)-len(remainig_num)
    masked_num =  '*'*strik+remainig_num
    return  masked_num 

# Make full sentance for gender
def gender_desider(ele):
    gender = ''
    if ele == 'F':
        gender = 'FEMALE'
    elif ele == 'M':
        gender = 'MALE'
    else:
        return gender
    return gender        
     
# Deside color code for aadhaar
def aadhaar_color_code(rule_engine_result):
    rull_engine_val = rule_engine_result.values()
    count = len(rull_engine_val)
    for i in rull_engine_val:
        if i == 'true':
            count = count - 1
    if count < 4 or count == 0:
        count = 1        
        return count
    return count
    
                                                  