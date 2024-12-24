import requests
import hashlib
from binascii import hexlify
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
import xml.etree.ElementTree as ET
import sys, os
from hv_whatsapp.settings import PerfiosCreds
from bs4 import BeautifulSoup

payload = {
        "processingType": "NETBANKING_FETCH",
        "transactionCompleteCallbackUrl": "https://example.com",
        "txnId": "test1234567890",
        "employmentType": "Salaried",
        "facility": "None",
        "sourceSystem": "tablet",
        "productType": "Loan",
}

###########################################################################
payload_netbanking = """
        <payload>
            <txnId>{TxnId}</txnId>
            <processingType>NETBANKING_FETCH</processingType>
            <transactionCompleteCallbackUrl>{TransactionCompleteCallBackUrl}</transactionCompleteCallbackUrl>
            <productType>Loan</productType>
            <employmentType>Salaried</employmentType>
            <sourceSystem>tablet</sourceSystem>
            <facility>NONE</facility>
            <returnUrl>{return_url}</returnUrl>
            <loanDuration>1</loanDuration>
            <loanAmount>1</loanAmount>
            <loanType>Home</loanType>
        </payload>
        """

payload_statement_upload = """
        <payload>
            <txnId>{TxnId}</txnId>
            <processingType>STATEMENT</processingType>
            <transactionCompleteCallbackUrl>{TransactionCompleteCallBackUrl}</transactionCompleteCallbackUrl>
            <productType>Loan</productType>
            <employmentType>Salaried</employmentType>
            <sourceSystem>tablet</sourceSystem>
            <facility>NONE</facility>
            <yearMonthFrom>{TransactionFrom}</yearMonthFrom>
            <yearMonthTo>{TransactionTo}</yearMonthTo>
            <returnUrl>{return_url}</returnUrl>
        </payload>
        """


def encode_url(string):
  result = ""
  for ch in string:
        if ('A' <= ch <= 'Z') or ('a' <= ch <= 'z') or ('0' <= ch <= '9') or ch == '_' or ch == '-' or ch == '~' or ch == '.' or ch == '/':
            result += ch
        else:
            result += hexlify(ch)
  return result

def get_results_perfios(txn_id, callback_url, return_url):
    result = {
        "link_url": "",
        "exception": "",
        "success": True
    }
    try:
        payload = payload_netbanking.format(
            TxnId=txn_id, 
            TransactionCompleteCallBackUrl=callback_url,
            return_url=return_url
        )
        vendor_id = PerfiosCreds.VendorID
        perfios_specific_date = PerfiosCreds.XPerfiosDate
        private_key_path = PerfiosCreds.PrivateKeyPath
        host = PerfiosCreds.Host
        Method = "POST"
        uriEncodedQuery = ""
        url = PerfiosCreds.URL.format(vendor_id)
        Netbankingdigest = hashlib.sha256(payload.encode()).hexdigest()
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(b'mypassword'))
        returnString = encode_url(url)
        CanonicalRequest = Method + "\n" + returnString + "\n" + uriEncodedQuery + "\n" + "host:" + host + "\n" + "x-perfios-content-sha256:" + Netbankingdigest + "\n" + "x-perfios-date:" + perfios_specific_date + "\n" + "host;x-perfios-content-sha256;x-perfios-date" + "\n" + Netbankingdigest
        sha256CanonicalRequest = hashlib.sha256(CanonicalRequest.encode()).hexdigest()
        StringToSign = "PERFIOS-RSA-SHA256" + "\n" + perfios_specific_date + "\n" + sha256CanonicalRequest
        checksum = hashlib.sha256(StringToSign.encode()).hexdigest()
        signature = hexlify(private_key.sign(
            bytes(checksum, 'utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        )
        headers = {
            'content-type': 'application/xml',
            'host': host,
            'x-Perfios-Algorithm': 'PERFIOS-RSA-SHA256',
            'X-Perfios-Signed-Headers': 'host;x-perfios-content-sha256;x-perfios-date',
            'x-perfios-content-sha256': Netbankingdigest,
            'x-perfios-date': perfios_specific_date,
            'x-Perfios-Signature': signature
        }
        r = requests.post('https://daa2.perfios.com' + url, data=payload, headers=headers)
        root = ET.fromstring(r.text)
        if r.status_code == 200:
            link_url = root.find('url').text
            perfios_txn_id = root.find('perfiosTransactionId').text
            link_expire_at = root.find('expires').text
            result['link_url'] = link_url
            result['perfios_txn_id'] = perfios_txn_id
            result['success_code'] = r.status_code
            result['perfios_response'] = r.text
            result['link_expire_at'] = link_expire_at
        else:
            exceptions = root.find('message').text
            result['link_url'] = ""
            result['perfios_txn_id'] = ""
            result['success_code'] = r.status_code
            result['perfios_response'] = r.text
            result['link_expire_at'] = ""
            result['exception'] = exceptions
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        result['exception'] = f"{exc_type.__name__}:{e.args[0]} in file: {fname} at line number: {exc_tb.tb_lineno}"
        result['success'] = False
        result['success_code'] = 424
        result['perfios_response'] = ""
        result['perfios_txn_id'] = ""
        result['link_expire_at'] = ""
    finally:
        return result


def get_results_perfios_statement(txn_id, callback_url, trans_from, trans_to, return_url):
    result = {
        "link_url": "",
        "exception": "",
        "success": True
    }
    try:
        payload = payload_statement_upload.format(
            TxnId=txn_id,
            TransactionCompleteCallBackUrl=callback_url,
            TransactionFrom=trans_from,
            TransactionTo=trans_to,
            return_url=return_url
        )
        vendor_id = PerfiosCreds.VendorID
        perfios_specific_date = PerfiosCreds.XPerfiosDate
        private_key_path = PerfiosCreds.PrivateKeyPath
        host = PerfiosCreds.Host
        Method = "POST"
        uriEncodedQuery = ""
        url = PerfiosCreds.URL.format(vendor_id)
        Netbankingdigest = hashlib.sha256(payload.encode()).hexdigest()
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        returnString = encode_url(url)
        CanonicalRequest = Method + "\n" + returnString + "\n" + uriEncodedQuery + "\n" + "host:" + host + "\n" + "x-perfios-content-sha256:" + Netbankingdigest + "\n" + "x-perfios-date:" + perfios_specific_date + "\n" + "host;x-perfios-content-sha256;x-perfios-date" + "\n" + Netbankingdigest
        sha256CanonicalRequest = hashlib.sha256(CanonicalRequest.encode()).hexdigest()
        StringToSign = "PERFIOS-RSA-SHA256" + "\n" + perfios_specific_date + "\n" + sha256CanonicalRequest
        checksum = hashlib.sha256(StringToSign.encode()).hexdigest()
        signature = hexlify(private_key.sign(
            bytes(checksum, 'utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        )
        headers = {
            'content-type': 'application/xml',
            'host': host,
            'x-Perfios-Algorithm': 'PERFIOS-RSA-SHA256',
            'X-Perfios-Signed-Headers': 'host;x-perfios-content-sha256;x-perfios-date',
            'x-perfios-content-sha256': Netbankingdigest,
            'x-perfios-date': perfios_specific_date,
            'x-Perfios-Signature': signature
        }
        r = requests.post('https://daa2.perfios.com' + url, data=payload, headers=headers)
        root = ET.fromstring(r.text)
        if r.status_code == 200:
            link_url = root.find('url').text
            perfios_txn_id = root.find('perfiosTransactionId').text
            link_expire_at = root.find('expires').text
            result['link_url'] = link_url
            result['perfios_txn_id'] = perfios_txn_id
            result['success_code'] = r.status_code
            result['perfios_response'] = r.text
            result['link_expire_at'] = link_expire_at
        else:
            exceptions = root.find('message').text
            result['link_url'] = ""
            result['perfios_txn_id'] = ""
            result['success_code'] = r.status_code
            result['perfios_response'] = r.text
            result['link_expire_at'] = ""
            result['exception'] = exceptions
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        result['exception'] = f"{exc_type.__name__}:{e.args[0]} in file: {fname} at line number: {exc_tb.tb_lineno}"
        result['success'] = False
        result['success_code'] = 424
        result['perfios_response'] = ""
        result['perfios_txn_id'] = ""
        result['link_expire_at'] = ""
    finally:
        return result

def retrieve_report(perfios_txn_id):
    """
    report_type values: currently we are using json
    xml: to retrieve XML report
    xml,pdf: to retrieve XML, and PDF reports (as a zip file)
    xls,json: to retrieve XLS, and JSON reports (as a zip file)
    xlsx: to retrieve XLSX report
    statements: to retrieve original statements
    incomeTaxDocuments: to retrieve income tax Documents
    transactions: to retrieve Amount balance mismatch details
    """
    result = dict()
    try:
        payload = ""
        perfios_specific_date = PerfiosCreds.XPerfiosDate
        private_key_path = PerfiosCreds.PrivateKeyPath
        host = PerfiosCreds.Host
        Method = "GET"
        uriEncodedQuery = "types=json"
        url = PerfiosCreds.RetrieveURL.format(perfios_txn_id, 'json')
        _url = url.split('?')[0]
        Netbankingdigest = hashlib.sha256(payload.encode()).hexdigest()
        with open(private_key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        returnString = encode_url(_url)
        CanonicalRequest = Method + "\n" + returnString + "\n" + uriEncodedQuery + "\n" + "host:" + host + "\n" + "x-perfios-content-sha256:" + Netbankingdigest + "\n" + "x-perfios-date:" + perfios_specific_date + "\n" + "host;x-perfios-content-sha256;x-perfios-date" + "\n" + Netbankingdigest
        sha256CanonicalRequest = hashlib.sha256(CanonicalRequest.encode()).hexdigest()
        StringToSign = "PERFIOS-RSA-SHA256" + "\n" + perfios_specific_date + "\n" + sha256CanonicalRequest
        checksum = hashlib.sha256(StringToSign.encode()).hexdigest()
        signature = hexlify(private_key.sign(
            bytes(checksum, 'utf-8'),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        )
        headers = {
            "Content-Type": "application/json",
            "host": host,
            "x-Perfios-Algorithm": "PERFIOS-RSA-SHA256",
            "X-Perfios-Signed-Headers": "host;x-perfios-content-sha256;x-perfios-date",
            "x-perfios-content-sha256": Netbankingdigest,
            "x-perfios-date": perfios_specific_date,
            "x-Perfios-Signature": signature
        }
        r = requests.get(PerfiosCreds.BaseURL + url, headers=headers)
        result['success_code'] = r.status_code
        result['perfios_txn_id'] = perfios_txn_id
        if r.status_code == 200:
            result['perfios_response'] = r.json()
            result['exception'] = ""
        else:
            soup = BeautifulSoup(r.text, 'html.parser')
            error = soup.find('div', id='errorbox').text.replace('\n', '')
            result['perfios_response'] = ""
            result['exception'] = error
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        e = f"{exc_type.__name__}:{e.args[0]} in file: {fname} at line number: {exc_tb.tb_lineno}"
        result['success_code'] = 500
        result['perfios_txn_id'] = perfios_txn_id
        result['perfios_response'] = ""
        result['exception'] = e
    finally:
        return result
