import boto3, json
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from django.conf import settings
import cryptocode
load_dotenv()

def get_secret(secret_name):
    region_name = os.getenv("AWS_REGION_NAME")
    STORAGE_K = os.getenv("STORAGE_K")
    STORAGE_SK = os.getenv("STORAGE_SK")
    STORAGE_K = cryptocode.decrypt(STORAGE_K,settings.SECRET_KEY) 
    STORAGE_SK = cryptocode.decrypt(STORAGE_SK,settings.SECRET_KEY) 
    session = boto3.session.Session(aws_access_key_id=STORAGE_K, aws_secret_access_key=STORAGE_SK)
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)




def download_file_from_s3(object_key, local_file_path):
    s3 = boto3.client('s3',aws_access_key_id=settings.AWS_ACCESS_KEY_ID,aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    try:
        s3.download_file(bucket_name, object_key, local_file_path)
        return True
    except Exception as ex:
        return False

from PIL import Image

def resize_image(object_key, output_image_path, size):
    try:
        download_file_from_s3(object_key, output_image_path)
        # output_image_path = 'media2/'+object_key
        input_image = Image.open(output_image_path)
        input_image = input_image.convert('RGB')
        resized_image = input_image.resize(size)
        resized_image.save(output_image_path)
        return output_image_path.split('/')[-1]
    except Exception as ex:
        return str(ex)
    