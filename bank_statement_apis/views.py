from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from . import processors as PROCESSORS
from . import serializers as Serializer

class BankStatementViews(ModelViewSet):

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def generate_link(self, request):
        result = {
            "success": False,
            "link_url": ""
        }
        try:
            data = request.data
            txn_id = data['TxnId']
            callback_url = data['callback_url']
            return_url = data['return_url']
            result["TxnId"] = txn_id
            response = {
                "txn_id": txn_id
            }
            res = PROCESSORS.get_results_perfios(txn_id=txn_id, callback_url=callback_url, return_url=return_url)
            result["exception"] = res["exception"]
            result["perfios_txn_id"] = res["perfios_txn_id"]
            result["link_url"] = res["link_url"]
            result["link_expire_at"] = res["link_expire_at"]
            response["response_json"] = res["perfios_response"]
            response["status_code"] = res["success_code"]
            response["exception"] = res["exception"]
            response["perfios_txn_id"] = res["perfios_txn_id"]
            response["link_expire_at"] = res["link_expire_at"]
            response["generated_link"] = res["link_url"]
            response["link_type"] = "netbanking"
            serializer = Serializer.LinkGenerateSerializer(data=response)
            if serializer.is_valid():
                serializer.save()
                if res["success_code"] == 200:
                    result["msg"] = "link generated successfully!"
                    result["success"] = True
                    return Response(result, status=status.HTTP_200_OK)
                elif res["success_code"] == 500:
                    result["msg"] = "issue in Perfios portal, please try again after some time!"
                    return Response(result, status=status.HTTP_404_NOT_FOUND)
                else:
                    result["msg"] = "Something went wrong!"
                    return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            result["exception"] = str(e)
            result["msg"] = ""
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def generate_link_upload(self, request):
        result = {
            "success": False,
            "link_url": ""
        }
        try:
            data = request.data
            txn_id = data['TxnId']
            callback_url = data['callback_url']
            trans_from = data['trans_from']
            trans_to = data['trans_to']
            return_url = data['return_url']
            result["TxnId"] = txn_id
            result["trans_from"] = trans_from
            result["trans_to"] = trans_to
            response = {
                "txn_id": txn_id
            }
            res = PROCESSORS.get_results_perfios_statement(
                txn_id=txn_id,
                callback_url=callback_url,
                trans_from=trans_from,
                trans_to=trans_to,
                return_url=return_url
            )
            result["exception"] = res["exception"]
            result["perfios_txn_id"] = res["perfios_txn_id"]
            result["link_url"] = res["link_url"]
            result["link_expire_at"] = res["link_expire_at"]
            response["response_json"] = res["perfios_response"]
            response["status_code"] = res["success_code"]
            response["exception"] = res["exception"]
            response["perfios_txn_id"] = res["perfios_txn_id"]
            response["link_expire_at"] = res["link_expire_at"]
            response["generated_link"] = res["link_url"]
            response["link_type"] = "statement"
            serializer = Serializer.LinkGenerateSerializer(data=response)
            if serializer.is_valid():
                serializer.save()
                if res["success_code"] == 200:
                    result["msg"] = "link generated successfully!"
                    result["success"] = True
                    return Response(result, status=status.HTTP_200_OK)
                elif res["success_code"] == 500:
                    result["msg"] = "issue in Perfios portal, please try again after some time!"
                    return Response(result, status=status.HTTP_404_NOT_FOUND)
                else:
                    result["msg"] = "Something went wrong!"
                    return Response(result, status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            result["exception"] = str(e)
            result["msg"] = ""
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def retrieve_reports(self, request):
        try:
            data = request.data
            perfios_txn_id = data['perfios_txn_id']
            res = PROCESSORS.retrieve_report(perfios_txn_id=perfios_txn_id)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(False, status=status.HTTP_500_INTERNAL_SERVER_ERROR)