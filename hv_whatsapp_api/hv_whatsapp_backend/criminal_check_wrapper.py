import datetime, json
import hashlib

def transform_json(valuePitch_result):

    final_json = []
    if valuePitch_result['status_code'] == 200:
        for json_a in json.loads(valuePitch_result['text']):
            # Initialize petitioner and respondent lists
            petitioner = []
            respondent = []

            # Handle petitioner and respondent details based on type
            if json_a["type"] == 0:  # Petitioner
                petitioner.append({
                    "pincode": "",
                    "localityname": "",
                    "address": json_a.get("matched_address", ""),
                    "subdistname": json_a.get("dist_name", ""),
                    "statename": json_a.get("state_name", ""),
                    "lastname": "",
                    "districtname": json_a.get("dist_name", ""),
                    "name": f"1. {json_a.get('name', '')}",
                    "id": 1,
                    "age": ""
                })
            elif json_a["type"] == 1:  # Respondent
                respondent.append({
                    "pincode": "",
                    "localityname": "",
                    "address": json_a.get("matched_address", ""),
                    "subdistname": json_a.get("dist_name", ""),
                    "statename": json_a.get("state_name", ""),
                    "lastname": "",
                    "districtname": json_a.get("dist_name", ""),
                    "name": f"1. {json_a.get('oparty', '')}",
                    "id": 1,
                    "age": ""
                })

            # Extract court number from court_no_and_judge
            court_no_and_judge = json_a.get("court_no_and_judge", "")
            court_number = court_no_and_judge.split('-')[0].strip() if '-' in court_no_and_judge else ""

            # Assign addresses based on type
            petitioner_address = json_a.get("matched_address", "") if json_a["type"] == 0 else ""
            respondent_address = json_a.get("matched_address", "") if json_a["type"] == 1 else json_a.get("oparty", "")

            # Create a unique ID using a hash function
            unique_id = hashlib.sha256(json_a.get("uniq_case_id", "").encode()).hexdigest() if json_a.get("uniq_case_id") else ""

            # Construct JSON B
            json_obj = {
                "year": json_a.get("case_year", ""),
                "bench": "",
                "crawledDate": datetime.datetime.now().isoformat(),
                "judgementDate": json_a.get("decision_date", ""),
                "judgementDescription": "",
                "caseFlow": [],
                "orderFlow": "",
                "petitioner": json_a.get("name", "") if json_a["type"] == 0 else "",
                "stateCode": str(json_a.get("state_code", "")),
                "distCode": str(json_a.get("dist_code", "")),
                "courtNumber": court_number,
                "regNumber": "",
                "filingNumber": "",
                "filingDate": "",
                "hearingDate": json_a.get("first_hearing_date", ""),
                "courtNumberAndJudge": court_no_and_judge,
                "score": json_a.get("score", 0),
                "id": json_a.get("id", ""),
                "respondent": json_a.get("oparty", "") if json_a["type"] == 1 else json_a.get("oparty", ""),
                "caseName": "",
                "caseTypeName": json_a.get("case_type", ""),
                "courtName": json_a.get("court_name", ""),
                "caseStatus": json_a.get("case_status", ""),
                "caseNo": json_a.get("case_code", ""),
                "firnumber": json_a.get("fir_no", ""),
                "firlink": "",
                "dist": json_a.get("dist_name", ""),
                "policestation": "",
                "circle": "",
                "state": json_a.get("state_name", ""),
                "courtType": json_a.get("jurisdiction_type", ""),
                "district": json_a.get("dist_name", ""),
                "caseLink": json_a.get("link", ""),
                "suitfiledamount": "",
                "gfc_updated_at": "",
                "created_at": "",
                "cinNumber": "",
                "caseRegDate": "",
                "petitionerAddress": petitioner_address,
                "respondentAddress": respondent_address,
                "underAct": json_a.get("under_acts", ""),
                "underSection": json_a.get("under_sections", ""),
                "natureOfDisposal": json_a.get("nature_of_disposal", ""),
                "gfc_respondents": [],
                "gfc_petitioners": [],
                "gfc_fir_respondents": [],
                "gfc_fir_petitioners": [],
                "gfc_uniqueid": unique_id,
                "elasticId": json_a.get("id", ""),
                "caseDetailsLink": json_a.get("link", ""),
                "gfc_fir_number_court": "",
                "gfc_fir_year_court": "",
                "gfc_fir_policestation_court": "",
                "gfc_orders_data": {
                    "petitioners": petitioner,
                    "respondents": respondent
                },
                "caseType": json_a.get("case_category", ""),
                "judgementLink": json_a.get("link", ""),
                "position": 1
            }
            final_json.append(json_obj)
        valuePitch_result['text'] = final_json
    return valuePitch_result
